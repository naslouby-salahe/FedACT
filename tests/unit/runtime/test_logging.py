from __future__ import annotations

import logging

from fedact.domain.records import LogNamespace
from fedact.runtime.logging import configure_execution_logging, execution_logger


def test_execution_loggers_are_namespaced_and_diagnostic_only() -> None:
    logger = execution_logger(LogNamespace("executor"))
    assert logger.name == "fedact.executor"
    configure_execution_logging(logging.WARNING)
    assert logging.getLogger("fedact").level == logging.WARNING
