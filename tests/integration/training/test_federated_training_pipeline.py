from __future__ import annotations

from fedact.config.loading import LoadedConfiguration
from fedact.domain.types import ClientIdentifier, SampleIdentifier
from fedact.learning.detector import DetectorHead
from fedact.learning.federation import ClientTrainingPopulation, train_federated_detector
from fedact.learning.representation import RepresentationEncoder, TrainingObservation


def test_federated_training_pipeline_integration(
    production_configuration: LoadedConfiguration,
) -> None:
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
                    features=(0.9,) * 512,
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
