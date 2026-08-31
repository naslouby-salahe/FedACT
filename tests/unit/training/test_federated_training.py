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
    config = production_configuration.values
    result = train_federated_detector(
        encoder,
        head,
        client_pops,
        maximum_rounds=config.training.maximum_epochs,
        initial_learning_rate=config.training.initial_learning_rate,
        final_learning_rate=config.training.final_learning_rate,
    )
    assert result.global_rounds_completed == config.training.maximum_epochs
    assert result.final_loss >= 0.0
