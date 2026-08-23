from __future__ import annotations

from fedact.config.loading import LoadedConfiguration
from fedact.domain.records import SampleIdentifier
from fedact.models.detector import DetectorHead
from fedact.models.representation import RepresentationEncoder
from fedact.training.federated import train_federated_detector
from fedact.training.representation import TrainingObservation


def test_train_federated_detector(production_configuration: LoadedConfiguration) -> None:
    encoder = RepresentationEncoder(input_dimension=512)
    head = DetectorHead()
    client_pops = {
        "c1": (
            TrainingObservation(
                sample_id=SampleIdentifier("s1"),
                month_index=0,
                features=(0.1,) * 512,
                label=True,
            ),
            TrainingObservation(
                sample_id=SampleIdentifier("s2"),
                month_index=0,
                features=(0.0,) * 512,
                label=False,
            ),
        ),
    }
    result = train_federated_detector(encoder, head, client_pops, production_configuration.values)
    assert result.global_rounds_completed == 5
