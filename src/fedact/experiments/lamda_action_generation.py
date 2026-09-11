from __future__ import annotations

import logging
import subprocess
import tempfile
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import cast

import numpy as np
from androguard.core.apk import APK

from fedact.certification.actions import (
    CandidateValidityRecord,
    CompositionLengthLimit,
    MutationStructuralIntegrityError,
    OperatorCandidate,
    ValidityStatus,
    apk_dynamic_validity_of,
    apk_structural_validity_of,
    apply_and_verify_apk_operator_family,
    enumerate_candidates,
    lamda_families,
    maliciousness_validity_of,
)
from fedact.config.models import StrictModel
from fedact.data.androzoo import acquired_lamda_apk_sample_ids, androzoo_apk_destination
from fedact.data.clamav_signatures import acquire_supplementary_signatures
from fedact.data.lamda import (
    LamdaRawRecord,
    audited_label,
    label_derivation_rule,
    load_lamda_records,
    malicious_transition_displacement,
    validate_lamda_dataset,
    year_month_to_calendar_month,
)
from fedact.data.lamda_apk_emulator import EmulatorHandle
from fedact.data.lamda_apk_features import extract_lamda_apk_features, load_lamda_feature_vocabulary
from fedact.data.lamda_apk_mutations import (
    ApkFileBytes,
    ApkMutationError,
    ApkSigningError,
    ApkSigningIdentity,
    generate_deterministic_debug_keystore,
)
from fedact.data.records import LabelDerivationRule
from fedact.data.splits import (
    CalendarMonth,
    calendar_month,
    earliest_complete_transition_endpoint,
    windowed_mean,
)
from fedact.domain.types import (
    EvaluationCount,
    FamilyName,
    SampleCount,
    ScientificOutcome,
    SplitCutoffIdentity,
)
from fedact.experiments.identification import (
    ClientConstraintFit,
    cohort_has_sufficient_malicious_support,
    dominant_malicious_family_cohort,
    embed_features,
    fit_lamda_client_constraint,
    train_cutoff_representation_encoder,
)
from fedact.experiments.registry import ExperimentRuntime, experiment_directory
from fedact.experiments.validation import ActionArtifact, ActionObservation

LOGGER = logging.getLogger(__name__)

_KEYSTORE_ALIAS = "fedact-operator"
_DEBUG_KEYSTORE_STORE_PASSWORD = "changeit"
_MONKEY_SEED = 42

_REJECTION_MALICIOUS_SUPPORT = "malicious_support"
_REJECTION_ENCODER = "encoder"
_REJECTION_POINT_ESTIMATE = "point_estimate"
_REJECTION_TRANSITION_SUPPORT = "transition_support"
_REJECTION_HISTORICAL_DIAMETER_POOL = "historical_diameter_pool"


class EndpointFitCache(StrictModel):
    cohort: FamilyName
    record_count: SampleCount
    rejections: dict[str, str] = {} #TODO: do not use primitives. Fix by introducing a proper error type or message class and identify and fix why architecture tests didn't catch this


def _load_endpoint_fit_cache(
    cache_path: Path, cohort: FamilyName, record_count: SampleCount
) -> dict[int, str]:
    if not cache_path.is_file():
        return {}
    try:
        cache = EndpointFitCache.model_validate_json(cache_path.read_text(encoding="utf-8"))
    except ValueError:
        return {}
    if cache.cohort != cohort or cache.record_count != record_count:
        return {}
    return {int(endpoint): reason for endpoint, reason in cache.rejections.items()}


def _persist_endpoint_fit_cache(
    cache_path: Path, cohort: FamilyName, record_count: SampleCount, rejections: dict[int, str]
) -> None:
    cache = EndpointFitCache(
        cohort=cohort,
        record_count=record_count,
        rejections={str(endpoint): reason for endpoint, reason in rejections.items()},
    )
    temporary_destination = cache_path.with_suffix(".json.partial")
    temporary_destination.write_text(cache.model_dump_json(indent=2), encoding="utf-8")
    temporary_destination.replace(cache_path)


@dataclass(frozen=True)
class ActionGenerationReport:
    operator_eligible_source_samples: SampleCount
    candidates_considered: EvaluationCount
    valid_actions_written: EvaluationCount
    maliciousness_validation_unavailable_count: EvaluationCount
    scientific_outcome: ScientificOutcome


def _historical_diameter_pool(
    application: ExperimentRuntime,
    cohort_records: tuple[LamdaRawRecord, ...],
    cohort_features: np.ndarray,
    all_records: tuple[LamdaRawRecord, ...],
    all_features: np.ndarray,
    rule: LabelDerivationRule,
    inner_endpoints: tuple[CalendarMonth, ...],
    history: int,
    earliest_valid_endpoint: int,
) -> list[float]:
    diameters: list[float] = []
    for inner_endpoint in inner_endpoints:
        inner_historical = tuple(
            calendar_month(candidate)
            for candidate in range(
                max(earliest_valid_endpoint, int(inner_endpoint) - history), int(inner_endpoint)
            )
        )
        inner_earlier_malicious = tuple(
            calendar_month(candidate)
            for candidate in range(
                max(earliest_valid_endpoint, int(inner_endpoint) - history),
                int(inner_endpoint) - 1,
            )
        )
        result = fit_lamda_client_constraint(
            application,
            cohort_records,
            cohort_features,
            all_records,
            all_features,
            rule,
            inner_endpoint,
            inner_historical,
            inner_earlier_malicious,
        )
        if isinstance(result, ClientConstraintFit):
            diameters.append(2.0 * float(result.beta))
    return diameters


def _tool_version(command: list[str]) -> str: #TODO: do not use primitives. Fix by introducing a proper error type or message class and identify and fix why architecture tests didn't catch this
    try:
        result = subprocess.run(command, capture_output=True, check=False, timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        return "unavailable"
    output = (result.stdout or result.stderr).decode(errors="replace").strip().splitlines()
    return output[0] if output else "unavailable"


@lru_cache(maxsize=1)
def _real_toolchain_identity(android_system_image: str) -> str: #TODO: do not use primitives. Fix by introducing a proper error type or message class and identify and fix why architecture tests didn't catch this
    components = {
        "apktool": _tool_version(["apktool", "--version"]), #TODO: should be enums not hardcoded strings
        "apksigner": _tool_version(["apksigner", "--version"]), #TODO: should be enums not hardcoded strings
        "aapt2": _tool_version(["aapt2", "version"]), #TODO: should be enums not hardcoded strings
        "clamscan": _tool_version(["clamscan", "--version"]), #TODO: should be enums not hardcoded strings
        "android_system_image": android_system_image, #TODO: should be enums not hardcoded strings
    }
    return "; ".join(f"{name}={version}" for name, version in components.items())


def _apk_package_name(apk_bytes: bytes) -> str | None:
    try:
        apk = APK(cast(str, apk_bytes), raw=True)
    except Exception:
        return None
    package = apk.get_package()
    return package if package else None


def _apply_composition(
    candidate: OperatorCandidate, apk_bytes: ApkFileBytes, signing_identity: ApkSigningIdentity
) -> ApkFileBytes:
    current = apk_bytes
    for family, parameter in zip(
        candidate.composition.families, candidate.composition.parameters, strict=True
    ):
        current = apply_and_verify_apk_operator_family(
            family.name, parameter, current, signing_identity
        )
    return current


def _candidate_validity(
    original_apk_path: Path,
    transformed_apk_bytes: ApkFileBytes,
    package_name: str, #TODO: do not use primitives. Fix by introducing a proper error type or message class and identify and fix why architecture tests didn't catch this
    emulator_handle: EmulatorHandle,
    monkey_event_count: int,
    execution_timeout_seconds: float,
    minimum_behavior_jaccard: float,
    android_system_image: str, #TODO: do not use primitives. Fix by introducing a proper error type or message class and identify and fix why architecture tests didn't catch this
    supplementary_signature_directory: Path,
) -> CandidateValidityRecord:
    structural = apk_structural_validity_of(transformed_apk_bytes)
    maliciousness = maliciousness_validity_of(
        original_apk_path.read_bytes(),
        bytes(transformed_apk_bytes),
        ".apk",
        supplementary_signature_directory,
    )
    with tempfile.TemporaryDirectory(prefix="fedact-action-dynamic-") as scratch_directory:
        transformed_path = Path(scratch_directory) / "transformed.apk"
        transformed_path.write_bytes(bytes(transformed_apk_bytes))
        smoke, behavior = apk_dynamic_validity_of(
            emulator_handle,
            original_apk_path,
            transformed_path,
            package_name,
            monkey_event_count,
            _MONKEY_SEED,
            execution_timeout_seconds,
            minimum_behavior_jaccard,
        )
    return CandidateValidityRecord(
        structural=structural,
        smoke=smoke,
        maliciousness=maliciousness,
        behavior=behavior,
        toolchain_identity=_real_toolchain_identity(android_system_image),
        source_hash=original_apk_path.stem,
    )


def run_lamda_action_generation(
    application: ExperimentRuntime,
    emulator_handle: EmulatorHandle,
) -> ActionGenerationReport:
    config = application.configuration.values
    raw_root = application.repository_root / "data" / "raw" / "LAMDA" / "Baseline" #TODO: should be enums not hardcoded strings
    if not raw_root.is_dir():
        LOGGER.warning("lamda action generation has no LAMDA release at %s", raw_root)
        return ActionGenerationReport(0, 0, 0, 0, ScientificOutcome.INSUFFICIENT_EVIDENCE)

    acquired = acquired_lamda_apk_sample_ids(application.repository_root / "data" / "raw") #TODO: should be enums not hardcoded strings
    if not acquired:
        LOGGER.warning("lamda action generation has no AndroZoo-acquired APKs on disk")
        return ActionGenerationReport(0, 0, 0, 0, ScientificOutcome.INSUFFICIENT_EVIDENCE)

    loaded = load_lamda_records(raw_root)
    validate_lamda_dataset(loaded)
    rule = label_derivation_rule(config.datasets.lamda)
    index_by_sample = {record.sample_hash: index for index, record in enumerate(loaded.records)}

    cohort = dominant_malicious_family_cohort(loaded.records, rule)
    if cohort is None:
        return ActionGenerationReport(0, 0, 0, 0, ScientificOutcome.INSUFFICIENT_EVIDENCE)
    cohort_mask = np.fromiter(
        (record.family == cohort for record in loaded.records),
        dtype=bool,
        count=len(loaded.records),
    )
    cohort_records = tuple(
        record for record, keep in zip(loaded.records, cohort_mask, strict=True) if keep
    )
    cohort_index_by_sample = {
        record.sample_hash: index for index, record in enumerate(cohort_records)
    }
    raw_root_all = application.repository_root / "data" / "raw" #TODO: should be enums not hardcoded strings
    package_name_by_sample: dict[str, str] = {} #TODO: do not use primitives. Fix by introducing a proper error type or message class and identify and fix why architecture tests didn't catch this
    for record in cohort_records:
        if (
            audited_label(rule, record).binary_label is not True
            or record.sample_hash not in acquired
        ):
            continue
        apk_path = androzoo_apk_destination(raw_root_all, record.sample_hash)
        if not apk_path.is_file():
            continue
        package_name = _apk_package_name(apk_path.read_bytes())
        if package_name is None:
            LOGGER.warning("could not derive package name for %s; excluded", record.sample_hash)
            continue
        package_name_by_sample[record.sample_hash] = package_name

    eligible_source_records = tuple(
        record for record in cohort_records if record.sample_hash in package_name_by_sample
    )
    if not eligible_source_records:
        LOGGER.warning("no acquired, package-identified APK belongs to cohort %s", cohort)
        return ActionGenerationReport(0, 0, 0, 0, ScientificOutcome.INSUFFICIENT_EVIDENCE)

    months = np.fromiter(
        (int(year_month_to_calendar_month(record.year_month)) for record in cohort_records),
        dtype=np.int64,
        count=len(cohort_records),
    )
    history = config.temporal.historical_training_window_months
    horizon = config.temporal.primary_confirmatory_horizon_months
    transition_interval_months = config.temporal.transition_interval_months
    month_min, month_max = int(months.min()), int(months.max())
    earliest_valid_endpoint = int(
        earliest_complete_transition_endpoint(calendar_month(month_min), transition_interval_months)
    )

    vocabulary = load_lamda_feature_vocabulary(
        application.repository_root / "data" / "raw" / "LAMDA" / "Baseline" / "feature_mapping.csv" #TODO: should be enums not hardcoded strings
    )
    signing_identity = ApkSigningIdentity(
        keystore_path=experiment_directory(application, "action-certificate-validation") #TODO: should be enums not hardcoded strings
        / "signing" #TODO: should be enums not hardcoded strings
        / "debug-keystore.jks", #TODO: should be enums not hardcoded strings
        key_alias=_KEYSTORE_ALIAS,
        store_password=_DEBUG_KEYSTORE_STORE_PASSWORD,
    )
    generate_deterministic_debug_keystore(signing_identity)
    supplementary_signatures = acquire_supplementary_signatures(
        application.repository_root / "data" / "raw" #TODO: should be enums not hardcoded strings
    ).directory

    families = lamda_families()
    max_composed = CompositionLengthLimit(config.operators.maximum_composed_atomic_actions)
    diameter_quantile_fraction = (
        config.certification.forecast_set_diameter_abstention.historical_realized_diameter_quantile
    )

    destination = (
        experiment_directory(application, "action-certificate-validation") / "actions.json" #TODO: should be enums not hardcoded strings
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    fit_cache_path = (
        experiment_directory(application, "action-certificate-validation") #TODO: should be enums not hardcoded strings
        / "endpoint_fit_cache.json" #TODO: should be enums not hardcoded strings
    )

    def _persist_written(actions: list[ActionObservation]) -> None:
        temporary_destination = destination.with_suffix(".json.partial")
        temporary_destination.write_text(
            ActionArtifact(actions=actions).model_dump_json(indent=2), encoding="utf-8"
        )
        temporary_destination.replace(destination)

    written: list[ActionObservation] = []
    candidates_considered = 0
    maliciousness_validation_unavailable_count = 0
    cached_rejections = _load_endpoint_fit_cache(fit_cache_path, cohort, len(loaded.records))
    rejections = dict(cached_rejections)

    def _reject(endpoint_ordinal: int, endpoint: CalendarMonth, stage: str) -> None: #TODO: do not use primitives. Fix by introducing a proper error type or message class and identify and fix why architecture tests didn't catch this
        LOGGER.info("action generation endpoint=%s rejected stage=%s", endpoint, stage)
        rejections[endpoint_ordinal] = stage
        _persist_endpoint_fit_cache(fit_cache_path, cohort, len(loaded.records), rejections)

    for endpoint_ordinal in range(
        max(earliest_valid_endpoint, month_min + 1), month_max - horizon + 1
    ):
        endpoint = calendar_month(endpoint_ordinal)
        if endpoint_ordinal in cached_rejections:
            LOGGER.info(
                "action generation endpoint=%s cached_rejection stage=%s",
                endpoint,
                cached_rejections[endpoint_ordinal],
            )
            continue
        if not cohort_has_sufficient_malicious_support(
            cohort_records,
            rule,
            endpoint,
            transition_interval_months,
            config.identification.minimum_support_per_class,
        ):
            _reject(endpoint_ordinal, endpoint, _REJECTION_MALICIOUS_SUPPORT)
            continue
        historical_endpoints = tuple(
            calendar_month(candidate)
            for candidate in range(
                max(earliest_valid_endpoint, endpoint_ordinal - history), endpoint_ordinal
            )
        )
        earlier_malicious_endpoints = tuple(
            calendar_month(candidate)
            for candidate in range(
                max(earliest_valid_endpoint, endpoint_ordinal - history), endpoint_ordinal - 1
            )
        )
        encoder = train_cutoff_representation_encoder(
            application, loaded.records, loaded.features, rule, endpoint
        )
        if encoder is None:
            _reject(endpoint_ordinal, endpoint, _REJECTION_ENCODER)
            continue
        embedded_features = embed_features(encoder, loaded.features)
        embedded_cohort_features = embedded_features[cohort_mask]

        fit = fit_lamda_client_constraint(
            application,
            cohort_records,
            embedded_cohort_features,
            loaded.records,
            embedded_features,
            rule,
            endpoint,
            historical_endpoints,
            earlier_malicious_endpoints,
        )
        if not isinstance(fit, ClientConstraintFit):
            _reject(endpoint_ordinal, endpoint, f"client_constraint_fit:{fit.value}")
            continue
        beta = float(fit.beta)

        point_estimate = malicious_transition_displacement(
            cohort_records, embedded_cohort_features, rule, endpoint, transition_interval_months
        )
        if point_estimate is None:
            _reject(endpoint_ordinal, endpoint, _REJECTION_POINT_ESTIMATE)
            continue
        ghat = point_estimate.displacement

        before_start = calendar_month(endpoint_ordinal - transition_interval_months * 2)
        before_end = calendar_month(endpoint_ordinal - transition_interval_months)
        after_end = calendar_month(endpoint_ordinal + horizon)
        before_mean, before_support = windowed_mean(
            embedded_cohort_features, months, before_start, before_end
        )
        after_mean, after_support = windowed_mean(
            embedded_cohort_features, months, endpoint, after_end
        )
        if before_support == 0 or after_support == 0:
            _reject(endpoint_ordinal, endpoint, _REJECTION_TRANSITION_SUPPORT)
            continue
        ghat_real = after_mean - before_mean

        historical_diameters = _historical_diameter_pool(
            application,
            cohort_records,
            embedded_cohort_features,
            loaded.records,
            embedded_features,
            rule,
            historical_endpoints,
            history,
            earliest_valid_endpoint,
        )
        if not historical_diameters:
            _reject(endpoint_ordinal, endpoint, _REJECTION_HISTORICAL_DIAMETER_POOL)
            continue
        historical_diameter_quantile = float(
            np.percentile(historical_diameters, diameter_quantile_fraction * 100.0, method="linear")
        )

        cutoff_id = SplitCutoffIdentity(f"lamda-{endpoint}")
        for source_record in eligible_source_records:
            source_index = index_by_sample[source_record.sample_hash]
            cohort_index = cohort_index_by_sample[source_record.sample_hash]
            if int(months[cohort_index]) >= endpoint_ordinal:
                continue
            apk_path = androzoo_apk_destination(
                application.repository_root / "data" / "raw", source_record.sample_hash #TODO: should be enums not hardcoded strings
            )
            if not apk_path.is_file():
                continue
            original_bytes = apk_path.read_bytes()
            embedded_original = embedded_features[source_index]
            candidates = enumerate_candidates(
                families, max_composed, source_record.sample_hash, cutoff_id
            )
            for candidate in candidates:
                candidates_considered += 1
                try:
                    mutated = _apply_composition(
                        candidate, ApkFileBytes(original_bytes), signing_identity
                    )
                except (
                    ApkMutationError,
                    ApkSigningError,
                    MutationStructuralIntegrityError,
                ) as error:
                    LOGGER.warning(
                        "operator candidate failed to construct: %s (%s)",
                        candidate.normalized_form,
                        error,
                    )
                    continue
                validity = _candidate_validity(
                    apk_path,
                    mutated,
                    package_name_by_sample[source_record.sample_hash],
                    emulator_handle,
                    config.operators.validation.android_monkey_events,
                    config.operators.validation.execution_timeout_seconds,
                    config.operators.validation.minimum_behavior_jaccard,
                    config.operators.validation.android_system_image,
                    supplementary_signatures,
                )
                if validity.status is ValidityStatus.MALICIOUSNESS_VALIDATION_UNAVAILABLE:
                    maliciousness_validation_unavailable_count += 1
                    continue
                if validity.status is not ValidityStatus.VALID:
                    continue
                with tempfile.TemporaryDirectory(prefix="fedact-action-features-") as scratch:
                    mutated_path = Path(scratch) / "mutated.apk"
                    mutated_path.write_bytes(bytes(mutated))
                    extraction = extract_lamda_apk_features(mutated_path, vocabulary)
                embedded_transformed = embed_features(
                    encoder, extraction.feature_vector.reshape(1, -1)
                )[0]
                displacement = np.asarray(embedded_transformed) - np.asarray(embedded_original)
                displacement_norm = float(np.linalg.norm(displacement))
                if displacement_norm < config.numerical.zero_displacement_floor:
                    continue
                q_o = displacement / displacement_norm

                projected_point = float(np.dot(q_o, ghat))
                lower_bound = projected_point - beta
                upper_bound = projected_point + beta
                point_score = (lower_bound + upper_bound) / 2.0
                later_real_alignment_score = float(np.dot(q_o, ghat_real))

                written.append(
                    ActionObservation(
                        sample_id=source_record.sample_hash,
                        lower_bound=lower_bound,
                        upper_bound=upper_bound,
                        domain_valid=True,
                        set_diameter=2.0 * beta,
                        historical_diameter_quantile=historical_diameter_quantile,
                        cutoff_id=cutoff_id,
                        cohort=cohort,
                        horizon_step=1,
                        source_sample_id=source_record.sample_hash,
                        action_count=len(candidate.composition.families),
                        point_score=point_score,
                        later_real_alignment_score=later_real_alignment_score,
                    )
                )
                _persist_written(written)

    _persist_written(written)
    return ActionGenerationReport(
        operator_eligible_source_samples=len(eligible_source_records),
        candidates_considered=candidates_considered,
        valid_actions_written=len(written),
        maliciousness_validation_unavailable_count=maliciousness_validation_unavailable_count,
        scientific_outcome=(
            ScientificOutcome.PASS if written else ScientificOutcome.INSUFFICIENT_EVIDENCE
        ),
    )
