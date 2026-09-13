from __future__ import annotations

import io
import os
import shutil
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

from fedact.domain.types import (
    ApkArchiveEntryName,
    ApkFileBytes,
    ApkOperatorFamilyName,
    ApkSigningKeyAlias,
    ApkSigningPassword,
    NormalizedParameterString,
    PayloadBytes,
    SubprocessEnvironment,
    ToolchainComponent,
    ValidationFlag,
)

_JAVA_NON_BLOCKING_ENTROPY_OPTION = "-Djava.security.egd=file:/dev/./urandom"

UNREFERENCED_RESOURCE_ENTRY_NAME = "assets/fedact_operator_payload.bin"
_SIGNATURE_FILE_SUFFIXES = (".rsa", ".dsa", ".ec", ".sf")
_MANIFEST_ENTRY_NAME = "meta-inf/manifest.mf"

BENIGN_GADGET_CLASS_NAME = "com.fedact.operator.BenignGadget"
_BENIGN_GADGET_SMALI_RELATIVE_PATH = "smali/com/fedact/operator/BenignGadget.smali"
_BENIGN_GADGET_SMALI_CONTENT = """.class public Lcom/fedact/operator/BenignGadget;
.super Ljava/lang/Object;
.source "BenignGadget.smali"

.method public constructor <init>()V
    .registers 1
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    return-void
.end method

.method public static unreachableHelper()I
    .registers 1
    const/16 v0, 0x2a
    return v0
.end method
"""

_SOURCE_APK_FILENAME = "source.apk"
_UNSIGNED_APK_FILENAME = "unsigned.apk"
_ALIGNED_APK_FILENAME = "aligned.apk"
_REBUILT_APK_FILENAME = "rebuilt.apk"
_DECOMPILED_OUTPUT_DIRECTORY = Path("decompiled")
_SIGNING_OUTPUT_DIRECTORY = Path("signing")


class ApkMutationError(RuntimeError):
    pass


class ApkSigningError(RuntimeError):
    pass


@dataclass(frozen=True)
class ApkSigningIdentity:
    keystore_path: Path
    key_alias: ApkSigningKeyAlias
    store_password: ApkSigningPassword


def java_subprocess_environment() -> SubprocessEnvironment:
    environment = SubprocessEnvironment(dict(os.environ))
    existing_options = environment.get("_JAVA_OPTIONS", "")
    if _JAVA_NON_BLOCKING_ENTROPY_OPTION not in existing_options:
        environment["_JAVA_OPTIONS"] = (
            f"{existing_options} {_JAVA_NON_BLOCKING_ENTROPY_OPTION}".strip()
        )
    return environment


def _is_signature_entry(entry_name: ApkArchiveEntryName) -> ValidationFlag:
    lowered = entry_name.lower()
    if not lowered.startswith("meta-inf/"):
        return False
    if lowered == _MANIFEST_ENTRY_NAME:
        return True
    return lowered.endswith(_SIGNATURE_FILE_SUFFIXES)


def permission_neutral_resource_injection(
    apk_bytes: ApkFileBytes, payload_size: PayloadBytes
) -> ApkFileBytes:
    source = io.BytesIO(bytes(apk_bytes))
    destination = io.BytesIO()
    with zipfile.ZipFile(source, "r") as source_zip:
        entry_names = set(source_zip.namelist())
        if UNREFERENCED_RESOURCE_ENTRY_NAME in entry_names:
            raise ApkMutationError(
                f"resource entry {UNREFERENCED_RESOURCE_ENTRY_NAME!r} already present; "
                "injection would collide"
            )
        with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as destination_zip:
            for item in source_zip.infolist():
                if _is_signature_entry(ApkArchiveEntryName(item.filename)):
                    continue
                destination_zip.writestr(item, source_zip.read(item.filename))
            destination_zip.writestr(UNREFERENCED_RESOURCE_ENTRY_NAME, bytes(payload_size))
    return ApkFileBytes(destination.getvalue())


def generate_deterministic_debug_keystore(signing_identity: ApkSigningIdentity) -> None:
    if signing_identity.keystore_path.exists():
        return
    signing_identity.keystore_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            ToolchainComponent.KEYTOOL,
            "-genkeypair",
            "-keystore",
            signing_identity.keystore_path,
            "-alias",
            signing_identity.key_alias,
            "-storepass",
            signing_identity.store_password,
            "-keypass",
            signing_identity.store_password,
            "-keyalg",
            "RSA",
            "-keysize",
            "2048",
            "-validity",
            "10000",
            "-dname",
            "CN=fedact-operator-signing, OU=fedact, O=fedact, L=fedact, S=fedact, C=US",
        ],
        check=True,
        capture_output=True,
        env=java_subprocess_environment(),
    )


def sign_and_align_apk(
    unsigned_apk: ApkFileBytes,
    signing_identity: ApkSigningIdentity,
    working_directory: Path,
) -> ApkFileBytes:
    working_directory.mkdir(parents=True, exist_ok=True)
    unsigned_path = working_directory / _UNSIGNED_APK_FILENAME
    aligned_path = working_directory / _ALIGNED_APK_FILENAME
    unsigned_path.write_bytes(bytes(unsigned_apk))
    try:
        subprocess.run(
            [ToolchainComponent.ZIPALIGN, "-f", "-p", "4", unsigned_path, aligned_path],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                ToolchainComponent.APKSIGNER,
                "sign",
                "--ks",
                signing_identity.keystore_path,
                "--ks-key-alias",
                signing_identity.key_alias,
                "--ks-pass",
                f"pass:{signing_identity.store_password}",
                "--key-pass",
                f"pass:{signing_identity.store_password}",
                aligned_path,
            ],
            check=True,
            capture_output=True,
            env=java_subprocess_environment(),
        )
    except subprocess.CalledProcessError as error:
        raise ApkSigningError(
            f"APK signing/alignment failed: {error.stderr.decode(errors='replace')}"
        ) from error
    return ApkFileBytes(aligned_path.read_bytes())


def unreachable_benign_gadget_injection(
    apk_bytes: ApkFileBytes, signing_identity: ApkSigningIdentity, working_directory: Path
) -> ApkFileBytes:
    working_directory.mkdir(parents=True, exist_ok=True)
    source_path = working_directory / _SOURCE_APK_FILENAME
    source_path.write_bytes(bytes(apk_bytes))
    decompiled_directory = working_directory / _DECOMPILED_OUTPUT_DIRECTORY
    if decompiled_directory.exists():
        shutil.rmtree(decompiled_directory)
    rebuilt_path = working_directory / _REBUILT_APK_FILENAME
    try:
        subprocess.run(
            [
                ToolchainComponent.APKTOOL,
                "d",
                "-f",
                "-r",
                "-o",
                decompiled_directory,
                source_path,
            ],
            check=True,
            capture_output=True,
            env=java_subprocess_environment(),
        )
        gadget_path = decompiled_directory / _BENIGN_GADGET_SMALI_RELATIVE_PATH
        if gadget_path.exists():
            raise ApkMutationError(
                f"gadget class {BENIGN_GADGET_CLASS_NAME!r} already present in source APK"
            )
        gadget_path.parent.mkdir(parents=True, exist_ok=True)
        gadget_path.write_text(_BENIGN_GADGET_SMALI_CONTENT, encoding="utf-8")
        subprocess.run(
            [ToolchainComponent.APKTOOL, "b", "-f", "-o", rebuilt_path, decompiled_directory],
            check=True,
            capture_output=True,
            env=java_subprocess_environment(),
        )
    except subprocess.CalledProcessError as error:
        raise ApkMutationError(
            f"apktool gadget injection failed: {error.stderr.decode(errors='replace')}"
        ) from error
    rebuilt_bytes = ApkFileBytes(rebuilt_path.read_bytes())
    return sign_and_align_apk(
        rebuilt_bytes, signing_identity, working_directory / _SIGNING_OUTPUT_DIRECTORY
    )


def apply_apk_operator_family(
    family_name: ApkOperatorFamilyName,
    parameter: NormalizedParameterString,
    apk_bytes: ApkFileBytes,
    signing_identity: ApkSigningIdentity,
) -> ApkFileBytes:
    with tempfile.TemporaryDirectory(prefix="fedact-apk-operator-") as scratch_directory:
        working_directory = Path(scratch_directory)
        match family_name:
            case ApkOperatorFamilyName.UNREACHABLE_BENIGN_GADGET_INJECTION:
                return unreachable_benign_gadget_injection(
                    apk_bytes, signing_identity, working_directory
                )
            case ApkOperatorFamilyName.PERMISSION_NEUTRAL_RESOURCE_INJECTION:
                payload_size = PayloadBytes(int(parameter.split("=", 1)[1]))
                mutated = permission_neutral_resource_injection(apk_bytes, payload_size)
                return sign_and_align_apk(
                    mutated, signing_identity, working_directory / _SIGNING_OUTPUT_DIRECTORY
                )
