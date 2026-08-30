from __future__ import annotations

from fedact.config.loading import LoadedConfiguration
from fedact.domain.records import ClientIdentifier, SampleIdentifier
from fedact.models.detector import DetectorHead
from fedact.models.representation import RepresentationEncoder
from fedact.training.federated import ClientTrainingPopulation, train_federated_detector
from fedact.training.representation import TrainingObservation


def test_train_federated_detector(production_configuration: LoadedConfiguration) -> None:
    encoder = RepresentationEncoder(input_dimension=512)
    head = DetectorHead()
    client_pops = (
        ClientTrainingPopulation(
            client=ClientIdentifier("c1"),
            observations=(
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
        ),
    )
    result = train_federated_detector(encoder, head, client_pops, production_configuration.values)
    assert result.global_rounds_completed == production_configuration.values.training.maximum_epochs
    assert result.final_loss >= 0.0
