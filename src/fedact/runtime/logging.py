from __future__ import annotations

import logging

from fedact.domain.records import LogNamespace

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"
FEDACT_LOG_NAMESPACE = "fedact"


def configure_execution_logging(level: int = logging.INFO) -> None:
    namespace = logging.getLogger(FEDACT_LOG_NAMESPACE)
    namespace.setLevel(level)
    if not namespace.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        namespace.addHandler(handler)


def execution_logger(name: LogNamespace) -> logging.Logger:
    return logging.getLogger(f"{FEDACT_LOG_NAMESPACE}.{name}")
