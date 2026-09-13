from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import cast
from xml.etree.ElementTree import Element

import numpy as np
import pandas as pd
from androguard.core.analysis.analysis import Analysis
from androguard.core.apk import APK
from androguard.misc import AnalyzeAPK
from numpy.typing import NDArray

from fedact.domain.types import (
    AndroidManifestTag,
    ApiReference,
    DimensionValue,
    FeatureColumnName,
    FeatureIndex,
    LamdaFeatureCategory,
    LamdaFeatureName,
    ManifestAttributeName,
    ObservableFeatureToken,
    UrlDomain,
)

MANIFEST_ANDROID_NAMESPACE = "{http://schemas.android.com/apk/res/android}"
URL_DOMAIN_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z0-9+.-]*://([a-zA-Z0-9.-]+)")


REPRODUCIBLE_FEATURE_CATEGORIES = (
    LamdaFeatureCategory.ACTIVITY_LIST,
    LamdaFeatureCategory.BROADCAST_RECEIVER_LIST,
    LamdaFeatureCategory.SERVICE_LIST,
    LamdaFeatureCategory.REQUESTED_PERMISSION_LIST,
    LamdaFeatureCategory.INTENT_FILTER_LIST,
    LamdaFeatureCategory.HARDWARE_COMPONENTS_LIST,
    LamdaFeatureCategory.RESTRICTED_API_LIST,
    LamdaFeatureCategory.SUSPICIOUS_API_LIST,
    LamdaFeatureCategory.URL_DOMAIN_LIST,
)
UNVERIFIABLE_FEATURE_CATEGORIES = (LamdaFeatureCategory.USED_PERMISSIONS_LIST,)


class LamdaFeatureVocabularyError(ValueError):
    pass


@dataclass(frozen=True)
class LamdaFeatureVocabulary:
    dimension: DimensionValue
    category_by_index: tuple[LamdaFeatureCategory, ...]
    name_by_index: tuple[LamdaFeatureName, ...]
    unverifiable_indices: frozenset[FeatureIndex]


def load_lamda_feature_vocabulary(mapping_path: Path) -> LamdaFeatureVocabulary:
    mapping = pd.read_csv(mapping_path)
    known_categories = REPRODUCIBLE_FEATURE_CATEGORIES + UNVERIFIABLE_FEATURE_CATEGORIES
    feature_index = cast(pd.Series, mapping["mapped_name"].str.removeprefix("feat_")).astype(int)
    ordered = mapping.assign(feature_index=feature_index).sort_values(by="feature_index")
    feature_names = cast(list[FeatureColumnName], ordered["feature_name"].tolist())
    categories: list[LamdaFeatureCategory] = []
    names: list[LamdaFeatureName] = []
    unverifiable_indices: set[int] = set()
    for index, feature_name in enumerate(feature_names):
        matched_category = next(
            (category for category in known_categories if feature_name.startswith(f"{category}_")),
            None,
        )
        if matched_category is None:
            raise LamdaFeatureVocabularyError(
                f"feature {feature_name!r} does not match any known LAMDA feature category"
            )
        categories.append(matched_category)
        names.append(LamdaFeatureName(feature_name[len(matched_category) + 1 :]))
        if matched_category in UNVERIFIABLE_FEATURE_CATEGORIES:
            unverifiable_indices.add(index)
    return LamdaFeatureVocabulary(
        dimension=len(names),
        category_by_index=tuple(categories),
        name_by_index=tuple(names),
        unverifiable_indices=frozenset(FeatureIndex(index) for index in unverifiable_indices),
    )


@dataclass(frozen=True)
class LamdaApkFeatureExtraction:
    feature_vector: NDArray[np.float64]
    unverifiable_feature_indices: frozenset[FeatureIndex]


def _canonical_api_reference(reference: ApiReference) -> ApiReference:
    normalized = reference.replace("->", ".").replace(";", "").replace("/", ".")
    if normalized.startswith("L") and "." in normalized:
        normalized = normalized[1:]
    return ApiReference(normalized)


def _manifest_xml(apk: APK) -> Element:
    xml = cast("Element | None", apk.get_android_manifest_xml())
    if xml is None:
        raise LamdaFeatureVocabularyError("APK has no parseable AndroidManifest.xml")
    return xml


def _raw_manifest_name_attributes(
    xml: Element, tags: tuple[AndroidManifestTag, ...]
) -> set[ObservableFeatureToken]:
    names: set[ObservableFeatureToken] = set()
    for element in xml.iter():
        if element.tag in tags:
            value = element.get(ManifestAttributeName(MANIFEST_ANDROID_NAMESPACE + "name"))
            if value:
                names.add(ObservableFeatureToken(value))
    return names


def _called_api_references(dx: Analysis) -> set[ObservableFeatureToken]:
    references: set[ObservableFeatureToken] = set()
    for method_analysis in dx.get_methods():
        method = method_analysis.get_method()
        references.add(
            ObservableFeatureToken(
                _canonical_api_reference(
                    ApiReference(f"{method.get_class_name()}.{method.get_name()}")
                )
            )
        )
    return references


def _url_domains(dx: Analysis) -> set[ObservableFeatureToken]:
    domains: set[ObservableFeatureToken] = set()
    for string_value in dx.get_strings():
        for match in URL_DOMAIN_PATTERN.findall(str(string_value)):
            domains.add(ObservableFeatureToken(UrlDomain(match.rstrip(".").lower())))
    return domains


def extract_lamda_apk_features(
    apk_path: Path, vocabulary: LamdaFeatureVocabulary
) -> LamdaApkFeatureExtraction:
    apk, _dex_objects, dx = AnalyzeAPK(apk_path.as_posix())
    xml = _manifest_xml(apk)
    observed_by_category: dict[LamdaFeatureCategory, set[ObservableFeatureToken]] = {
        LamdaFeatureCategory.ACTIVITY_LIST: _raw_manifest_name_attributes(
            xml, (AndroidManifestTag.ACTIVITY,)
        ),
        LamdaFeatureCategory.BROADCAST_RECEIVER_LIST: _raw_manifest_name_attributes(
            xml, (AndroidManifestTag.RECEIVER,)
        ),
        LamdaFeatureCategory.SERVICE_LIST: _raw_manifest_name_attributes(
            xml, (AndroidManifestTag.SERVICE,)
        ),
        LamdaFeatureCategory.REQUESTED_PERMISSION_LIST: {
            ObservableFeatureToken(permission) for permission in apk.get_permissions()
        },
        LamdaFeatureCategory.INTENT_FILTER_LIST: _raw_manifest_name_attributes(
            xml, (AndroidManifestTag.ACTION, AndroidManifestTag.CATEGORY)
        ),
        LamdaFeatureCategory.HARDWARE_COMPONENTS_LIST: {
            ObservableFeatureToken(feature) for feature in apk.get_features()
        },
        LamdaFeatureCategory.RESTRICTED_API_LIST: _called_api_references(dx),
        LamdaFeatureCategory.SUSPICIOUS_API_LIST: _called_api_references(dx),
        LamdaFeatureCategory.URL_DOMAIN_LIST: _url_domains(dx),
    }
    feature_vector = np.zeros(vocabulary.dimension, dtype=np.float64)
    for index, (category, name) in enumerate(
        zip(vocabulary.category_by_index, vocabulary.name_by_index, strict=True)
    ):
        if index in vocabulary.unverifiable_indices:
            continue
        observed = observed_by_category[category]
        if category in (
            LamdaFeatureCategory.RESTRICTED_API_LIST,
            LamdaFeatureCategory.SUSPICIOUS_API_LIST,
        ):
            present = (
                ObservableFeatureToken(_canonical_api_reference(ApiReference(name))) in observed
            )
        else:
            present = ObservableFeatureToken(name) in observed
        feature_vector[index] = 1.0 if present else 0.0
    return LamdaApkFeatureExtraction(
        feature_vector=feature_vector,
        unverifiable_feature_indices=vocabulary.unverifiable_indices,
    )
