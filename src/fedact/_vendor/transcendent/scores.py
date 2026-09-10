from __future__ import annotations

from collections.abc import Sequence


def compute_single_cred_p_value(
    train_ncms: Sequence[float],
    groundtruth_train: Sequence[int],
    single_test_ncm: float,
    single_y_test: int,
) -> float:
    assert len(set(groundtruth_train)) == 2

    how_many_are_greater_than_single_test_ncm = 0

    for ncm, groundtruth in zip(train_ncms, groundtruth_train, strict=True):
        if groundtruth == single_y_test and ncm >= single_test_ncm:
            how_many_are_greater_than_single_test_ncm += 1

    return how_many_are_greater_than_single_test_ncm / sum(
        1 for y in groundtruth_train if y == single_y_test
    )


def compute_single_conf_p_value(
    train_ncms: Sequence[float],
    groundtruth_train: Sequence[int],
    single_test_ncm: float,
    single_y_test: int,
) -> float:
    assert len(set(groundtruth_train)) == 2

    single_y_test_opposite_class = 0 if single_y_test == 1 else 1
    single_test_ncm_opposite_class = -1 * single_test_ncm

    how_many_are_greater_than_single_test_ncm = 0

    for ncm, groundtruth in zip(train_ncms, groundtruth_train, strict=True):
        if groundtruth == single_y_test_opposite_class and ncm >= single_test_ncm_opposite_class:
            how_many_are_greater_than_single_test_ncm += 1

    single_cred_p_value_opposite_class = how_many_are_greater_than_single_test_ncm / sum(
        1 for y in groundtruth_train if y == single_y_test_opposite_class
    )

    return 1 - single_cred_p_value_opposite_class


def compute_p_values_cred_and_conf(
    train_ncms: Sequence[float],
    groundtruth_train: Sequence[int],
    test_ncms: Sequence[float],
    y_test: Sequence[int],
) -> dict[str, list[float]]:
    cred = [
        compute_single_cred_p_value(
            train_ncms=train_ncms,
            groundtruth_train=groundtruth_train,
            single_test_ncm=ncm,
            single_y_test=y,
        )
        for ncm, y in zip(test_ncms, y_test, strict=True)
    ]
    conf = [
        compute_single_conf_p_value(
            train_ncms=train_ncms,
            groundtruth_train=groundtruth_train,
            single_test_ncm=ncm,
            single_y_test=y,
        )
        for ncm, y in zip(test_ncms, y_test, strict=True)
    ]

    return {"cred": cred, "conf": conf}
