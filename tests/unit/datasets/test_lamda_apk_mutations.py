from __future__ import annotations

import io
import subprocess
import zipfile
from pathlib import Path
from typing import Any

import pytest

from fedact.data.lamda_apk_mutations import (
    UNREFERENCED_RESOURCE_ENTRY_NAME,
    ApkMutationError,
    ApkSigningError,
    ApkSigningIdentity,
    apply_apk_operator_family,
    generate_deterministic_debug_keystore,
    java_subprocess_environment,
    permission_neutral_resource_injection,
    sign_and_align_apk,
    unreachable_benign_gadget_injection,
)
from fedact.domain.types import (
    ApkFileBytes,
    ApkOperatorFamilyName,
    ApkSigningKeyAlias,
    ApkSigningPassword,
    NormalizedParameterString,
    PayloadBytes,
)

KEY_ALIAS = ApkSigningKeyAlias("fedact-operator")
STORE_PASSWORD = ApkSigningPassword("changeit")
PAYLOAD_SIZE = PayloadBytes(256)
UNSIGNED_APK = ApkFileBytes(b"unsigned-apk-body")
REBUILT_APK = b"rebuilt-apk-body"


def _apk_zip_bytes(entries: dict[str, bytes]) -> ApkFileBytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in entries.items():
            archive.writestr(name, content)
    return ApkFileBytes(buffer.getvalue())


def _signing_identity(working_directory: Path) -> ApkSigningIdentity:
    return ApkSigningIdentity(
        keystore_path=working_directory / "debug-keystore.jks",
        key_alias=KEY_ALIAS,
        store_password=STORE_PASSWORD,
    )


def _entry_names(apk_bytes: ApkFileBytes) -> set[str]:
    with zipfile.ZipFile(io.BytesIO(bytes(apk_bytes))) as archive:
        return set(archive.namelist())


class _Toolchain:
    def __init__(self, rebuilt_bytes: bytes = REBUILT_APK) -> None:
        self.calls: list[list[str]] = []
        self._rebuilt_bytes = rebuilt_bytes
        self.fail_on: str | None = None

    def __call__(self, args: list[str], **_kwargs: Any) -> Any:
        call = [str(item) for item in args]
        self.calls.append(call)
        tool = call[0].rsplit("/", 1)[-1]
        if self.fail_on is not None and tool == self.fail_on:
            raise subprocess.CalledProcessError(returncode=1, cmd=call, stderr=b"tool failed")
        if tool == "apktool" and "d" in call:
            Path(call[call.index("-o") + 1]).mkdir(parents=True, exist_ok=True)
        elif tool == "apktool" and "b" in call:
            Path(call[call.index("-o") + 1]).write_bytes(self._rebuilt_bytes)
        elif tool == "zipalign":
            Path(call[-1]).write_bytes(self._rebuilt_bytes)
        return subprocess.CompletedProcess(args=call, returncode=0, stdout=b"", stderr=b"")


def test_java_subprocess_environment_preserves_existing_java_options(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("_JAVA_OPTIONS", "-Xmx2g")
    environment = java_subprocess_environment()
    assert "-Xmx2g" in environment["_JAVA_OPTIONS"]
    assert "urandom" in environment["_JAVA_OPTIONS"]


def test_java_subprocess_environment_adds_the_entropy_option_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("_JAVA_OPTIONS", raising=False)
    first = java_subprocess_environment()
    monkeypatch.setenv("_JAVA_OPTIONS", first["_JAVA_OPTIONS"])
    second = java_subprocess_environment()
    assert second["_JAVA_OPTIONS"] == first["_JAVA_OPTIONS"]


def test_resource_injection_drops_signature_entries_and_adds_the_payload() -> None:
    source = _apk_zip_bytes(
        {
            "classes.dex": b"dex",
            "META-INF/MANIFEST.MF": b"manifest",
            "META-INF/CERT.RSA": b"signature",
            "META-INF/CERT.SF": b"signature-file",
            "resources.arsc": b"resources",
        }
    )
    mutated = permission_neutral_resource_injection(source, PAYLOAD_SIZE)
    names = _entry_names(mutated)
    assert {"classes.dex", "resources.arsc", UNREFERENCED_RESOURCE_ENTRY_NAME} == names
    assert not any(name.upper().startswith("META-INF/") for name in names)


def test_resource_injection_refuses_to_collide_with_an_existing_payload() -> None:
    source = _apk_zip_bytes({"classes.dex": b"dex", UNREFERENCED_RESOURCE_ENTRY_NAME: b"present"})
    with pytest.raises(ApkMutationError, match="already present"):
        permission_neutral_resource_injection(source, PAYLOAD_SIZE)


def test_resource_injection_writes_the_requested_payload_length() -> None:
    source = _apk_zip_bytes({"classes.dex": b"dex"})
    mutated = permission_neutral_resource_injection(source, PAYLOAD_SIZE)
    with zipfile.ZipFile(io.BytesIO(bytes(mutated))) as archive:
        assert len(archive.read(UNREFERENCED_RESOURCE_ENTRY_NAME)) == PAYLOAD_SIZE


def test_keystore_generation_is_skipped_when_the_keystore_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    identity = _signing_identity(tmp_path)
    identity.keystore_path.write_bytes(b"existing-keystore")
    toolchain = _Toolchain()
    monkeypatch.setattr("fedact.data.lamda_apk_mutations.subprocess.run", toolchain)
    generate_deterministic_debug_keystore(identity)
    assert toolchain.calls == []


def test_keystore_generation_invokes_keytool_with_the_signing_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    identity = _signing_identity(tmp_path)
    toolchain = _Toolchain()
    monkeypatch.setattr("fedact.data.lamda_apk_mutations.subprocess.run", toolchain)
    generate_deterministic_debug_keystore(identity)
    call = toolchain.calls[0]
    assert call[0] == "keytool"
    assert str(identity.keystore_path) in call
    assert KEY_ALIAS in call
    assert identity.keystore_path.parent.is_dir()


def test_signing_aligns_then_signs_and_returns_the_aligned_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    toolchain = _Toolchain()
    monkeypatch.setattr("fedact.data.lamda_apk_mutations.subprocess.run", toolchain)
    signed = sign_and_align_apk(UNSIGNED_APK, _signing_identity(tmp_path), tmp_path / "signing")
    assert bytes(signed) == REBUILT_APK
    tools = [call[0] for call in toolchain.calls]
    assert tools == ["zipalign", "apksigner"]
    assert "--ks-key-alias" in toolchain.calls[1]
    assert f"pass:{STORE_PASSWORD}" in toolchain.calls[1]


def test_signing_failure_is_reported_as_a_signing_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    toolchain = _Toolchain()
    toolchain.fail_on = "apksigner"
    monkeypatch.setattr("fedact.data.lamda_apk_mutations.subprocess.run", toolchain)
    with pytest.raises(ApkSigningError, match="APK signing/alignment failed"):
        sign_and_align_apk(UNSIGNED_APK, _signing_identity(tmp_path), tmp_path / "signing")


def test_gadget_injection_runs_apktool_then_signs_the_rebuild(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    toolchain = _Toolchain()
    monkeypatch.setattr("fedact.data.lamda_apk_mutations.subprocess.run", toolchain)
    source = _apk_zip_bytes({"classes.dex": b"dex"})
    injected = unreachable_benign_gadget_injection(
        source, _signing_identity(tmp_path), tmp_path / "scratch"
    )
    assert bytes(injected) == REBUILT_APK
    decompile_call = toolchain.calls[0]
    assert decompile_call[0] == "apktool"
    assert "d" in decompile_call
    decompiled = Path(decompile_call[decompile_call.index("-o") + 1])
    gadget = decompiled / "smali" / "com" / "fedact" / "operator" / "BenignGadget.smali"
    assert gadget.is_file()
    assert "Lcom/fedact/operator/BenignGadget;" in gadget.read_text(encoding="utf-8")


def test_gadget_injection_refuses_a_source_that_already_contains_the_gadget(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    toolchain = _Toolchain()

    def _prepopulate(args: list[str], **kwargs: Any) -> Any:
        result = toolchain(args, **kwargs)
        decompiled = Path(args[args.index("-o") + 1])
        gadget = decompiled / "smali" / "com" / "fedact" / "operator" / "BenignGadget.smali"
        gadget.parent.mkdir(parents=True, exist_ok=True)
        gadget.write_text(".class public Lcom/fedact/operator/BenignGadget;\n", encoding="utf-8")
        return result

    monkeypatch.setattr("fedact.data.lamda_apk_mutations.subprocess.run", _prepopulate)
    source = _apk_zip_bytes({"classes.dex": b"dex"})
    with pytest.raises(ApkMutationError, match="already present in source APK"):
        unreachable_benign_gadget_injection(
            source, _signing_identity(tmp_path), tmp_path / "scratch"
        )


def test_gadget_injection_tool_failure_is_reported_as_a_mutation_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    toolchain = _Toolchain()
    toolchain.fail_on = "apktool"
    monkeypatch.setattr("fedact.data.lamda_apk_mutations.subprocess.run", toolchain)
    source = _apk_zip_bytes({"classes.dex": b"dex"})
    with pytest.raises(ApkMutationError, match="apktool gadget injection failed"):
        unreachable_benign_gadget_injection(
            source, _signing_identity(tmp_path), tmp_path / "scratch"
        )


def test_apk_operator_dispatch_routes_the_resource_injection_family(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    toolchain = _Toolchain()
    monkeypatch.setattr("fedact.data.lamda_apk_mutations.subprocess.run", toolchain)
    source = _apk_zip_bytes({"classes.dex": b"dex"})
    mutated = apply_apk_operator_family(
        ApkOperatorFamilyName.PERMISSION_NEUTRAL_RESOURCE_INJECTION,
        NormalizedParameterString(f"payload={PAYLOAD_SIZE}"),
        source,
        _signing_identity(tmp_path),
    )
    assert bytes(mutated) == REBUILT_APK


def test_apk_operator_dispatch_routes_the_gadget_injection_family(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    toolchain = _Toolchain()
    monkeypatch.setattr("fedact.data.lamda_apk_mutations.subprocess.run", toolchain)
    source = _apk_zip_bytes({"classes.dex": b"dex"})
    mutated = apply_apk_operator_family(
        ApkOperatorFamilyName.UNREACHABLE_BENIGN_GADGET_INJECTION,
        NormalizedParameterString("gadget-library=cutoff-safe-benign-gadget-library"),
        source,
        _signing_identity(tmp_path),
    )
    assert bytes(mutated) == REBUILT_APK
    assert toolchain.calls[0][0] == "apktool"


def test_gadget_injection_clears_a_stale_decompiled_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    toolchain = _Toolchain()
    monkeypatch.setattr("fedact.data.lamda_apk_mutations.subprocess.run", toolchain)
    scratch = tmp_path / "scratch"
    stale = scratch / "decompiled"
    stale.mkdir(parents=True)
    (stale / "stale-marker.txt").write_text("stale", encoding="utf-8")
    source = _apk_zip_bytes({"classes.dex": b"dex"})
    unreachable_benign_gadget_injection(source, _signing_identity(tmp_path), scratch)
    assert not (stale / "stale-marker.txt").exists()
