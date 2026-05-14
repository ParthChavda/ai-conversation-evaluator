import json
import logging
import time
from contextlib import contextmanager
from typing import Any
from uuid import uuid4

logger = logging.getLogger("ace.tracing")
logging.basicConfig(level=logging.INFO, format="%(message)s")


class EvaluationTracer:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    @contextmanager
    def span(self, name: str, **attributes: Any):
        trace_id = str(uuid4())
        started = time.perf_counter()
        if self.enabled:
            logger.info(
                json.dumps(
                    {
                        "event": "span_start",
                        "trace_id": trace_id,
                        "span": name,
                        **attributes,
                    }
                )
            )
        try:
            yield
        finally:
            if self.enabled:
                elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
                logger.info(
                    json.dumps(
                        {
                            "event": "span_end",
                            "trace_id": trace_id,
                            "span": name,
                            "elapsed_ms": elapsed_ms,
                            **attributes,
                        }
                    )
                )
