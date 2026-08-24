from __future__ import annotations

import logging

from fedact.domain.records import LogNamespace
from fedact.domain.types import LogLevel

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"
FEDACT_LOG_NAMESPACE = "fedact"


def configure_execution_logging(level: LogLevel = logging.INFO) -> None:
    namespace = logging.getLogger(FEDACT_LOG_NAMESPACE)
    namespace.setLevel(level)
    if not namespace.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        namespace.addHandler(handler)


def execution_logger(name: LogNamespace) -> logging.Logger:
    return logging.getLogger(f"{FEDACT_LOG_NAMESPACE}.{name}")
