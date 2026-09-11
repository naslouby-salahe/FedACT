from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, cast

import numpy as np
import pandas as pd
from androguard.core.analysis.analysis import Analysis
from androguard.core.apk import APK
from androguard.misc import AnalyzeAPK
from numpy.typing import NDArray

MANIFEST_ANDROID_NAMESPACE = "{http://schemas.android.com/apk/res/android}"
URL_DOMAIN_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z0-9+.-]*://([a-zA-Z0-9.-]+)")


class ManifestElement(Protocol):
    tag: str #TODO: do not use primitives. Fix by introducing a proper error type or message class and identify and fix why architecture tests didn't catch this

    def iter(self) -> Iterator[ManifestElement]: ...

    def get(self, key: str) -> str | None: ... #TODO: do not use primitives. Fix by introducing a proper error type or message class and identify and fix why architecture tests didn't catch this


REPRODUCIBLE_FEATURE_CATEGORIES = (
    "ActivityList",
    "BroadcastReceiverList",
    "ServiceList",
    "RequestedPermissionList",
    "IntentFilterList",
    "HardwareComponentsList",
    "RestrictedApiList",
    "SuspiciousApiList",
    "URLDomainList",
)
UNVERIFIABLE_FEATURE_CATEGORIES = ("UsedPermissionsList",)


class LamdaFeatureVocabularyError(ValueError):
    pass


@dataclass(frozen=True)
class LamdaFeatureVocabulary:
    dimension: int
    category_by_index: tuple[str, ...] #TODO: do not use primitives. Fix by introducing a proper error type or message class and identify and fix why architecture tests didn't catch this
    name_by_index: tuple[str, ...] #TODO: do not use primitives. Fix by introducing a proper error type or message class and identify and fix why architecture tests didn't catch this
    unverifiable_indices: frozenset[int]


def load_lamda_feature_vocabulary(mapping_path: Path) -> LamdaFeatureVocabulary:
    mapping = pd.read_csv(mapping_path)
    known_categories = REPRODUCIBLE_FEATURE_CATEGORIES + UNVERIFIABLE_FEATURE_CATEGORIES
    feature_index = cast(pd.Series, mapping["mapped_name"].str.removeprefix("feat_")).astype(int)
    ordered = mapping.assign(feature_index=feature_index).sort_values(by="feature_index")
    feature_names = cast(list[str], ordered["feature_name"].tolist())
    categories: list[str] = [] #TODO: do not use primitives. Fix by introducing a proper error type or message class and identify and fix why architecture tests didn't catch this
    names: list[str] = [] #TODO: do not use primitives. Fix by introducing a proper error type or message class and identify and fix why architecture tests didn't catch this
    unverifiable_indices: set[int] = set()
    for index, feature_name in enumerate(feature_names):
        matched_category = next(
            (category for category in known_categories if feature_name.startswith(category + "_")),
            None,
        )
        if matched_category is None:
            raise LamdaFeatureVocabularyError(
                f"feature {feature_name!r} does not match any known LAMDA feature category"
            )
        categories.append(matched_category)
        names.append(feature_name[len(matched_category) + 1 :])
        if matched_category in UNVERIFIABLE_FEATURE_CATEGORIES:
            unverifiable_indices.add(index)
    return LamdaFeatureVocabulary(
        dimension=len(names),
        category_by_index=tuple(categories),
        name_by_index=tuple(names),
        unverifiable_indices=frozenset(unverifiable_indices),
    )


@dataclass(frozen=True)
class LamdaApkFeatureExtraction:
    feature_vector: NDArray[np.float64]
    unverifiable_feature_indices: frozenset[int]


def _canonical_api_reference(reference: str) -> str: #TODO: do not use primitives. Fix by introducing a proper error type or message class and identify and fix why architecture tests didn't catch this
    normalized = reference.replace("->", ".").replace(";", "").replace("/", ".")
    if normalized.startswith("L") and "." in normalized:
        normalized = normalized[1:]
    return normalized


def _manifest_xml(apk: APK) -> ManifestElement:
    xml = cast("ManifestElement | None", apk.get_android_manifest_xml())
    if xml is None:
        raise LamdaFeatureVocabularyError("APK has no parseable AndroidManifest.xml")
    return xml


def _raw_manifest_name_attributes(xml: ManifestElement, tags: tuple[str, ...]) -> set[str]: #TODO: do not use primitives. Fix by introducing a proper error type or message class and identify and fix why architecture tests didn't catch this
    names: set[str] = set() #TODO: do not use primitives. Fix by introducing a proper error type or message class and identify and fix why architecture tests didn't catch this
    for element in xml.iter():
        if element.tag in tags:
            value = element.get(MANIFEST_ANDROID_NAMESPACE + "name")
            if value:
                names.add(value)
    return names


def _called_api_references(dx: Analysis) -> set[str]:
    references: set[str] = set() #TODO: do not use primitives. Fix by introducing a proper error type or message class and identify and fix why architecture tests didn't catch this
    for method_analysis in dx.get_methods():
        method = method_analysis.get_method()
        references.add(_canonical_api_reference(f"{method.get_class_name()}.{method.get_name()}"))
    return references


def _url_domains(dx: Analysis) -> set[str]:
    domains: set[str] = set() #TODO: do not use primitives. Fix by introducing a proper error type or message class and identify and fix why architecture tests didn't catch this
    for string_value in dx.get_strings():
        for match in URL_DOMAIN_PATTERN.findall(str(string_value)):
            domains.add(match.rstrip(".").lower())
    return domains


def extract_lamda_apk_features(
    apk_path: Path, vocabulary: LamdaFeatureVocabulary
) -> LamdaApkFeatureExtraction:
    apk, _, dx = cast("tuple[APK, list[object], Analysis]", AnalyzeAPK(str(apk_path)))
    xml = _manifest_xml(apk)
    observed_by_category: dict[str, set[str]] = {
        "ActivityList": _raw_manifest_name_attributes(xml, ("activity",)), #TODO: should be enums not hardcoded strings
        "BroadcastReceiverList": _raw_manifest_name_attributes(xml, ("receiver",)), #TODO: should be enums not hardcoded strings
        "ServiceList": _raw_manifest_name_attributes(xml, ("service",)), #TODO: should be enums not hardcoded strings
        "RequestedPermissionList": set(apk.get_permissions()), #TODO: should be enums not hardcoded strings
        "IntentFilterList": _raw_manifest_name_attributes(xml, ("action", "category")), #TODO: should be enums not hardcoded strings
        "HardwareComponentsList": set(apk.get_features()), #TODO: should be enums not hardcoded strings
        "RestrictedApiList": _called_api_references(dx), #TODO: should be enums not hardcoded strings
        "SuspiciousApiList": _called_api_references(dx), #TODO: should be enums not hardcoded strings
        "URLDomainList": _url_domains(dx), #TODO: should be enums not hardcoded strings
    }
    feature_vector = np.zeros(vocabulary.dimension, dtype=np.float64)
    for index, (category, name) in enumerate(
        zip(vocabulary.category_by_index, vocabulary.name_by_index, strict=True)
    ):
        if index in vocabulary.unverifiable_indices:
            continue
        observed = observed_by_category[category]
        if category in ("RestrictedApiList", "SuspiciousApiList"):
            present = _canonical_api_reference(name) in observed
        else:
            present = name in observed
        feature_vector[index] = 1.0 if present else 0.0
    return LamdaApkFeatureExtraction(
        feature_vector=feature_vector,
        unverifiable_feature_indices=vocabulary.unverifiable_indices,
    )
