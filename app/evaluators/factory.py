from app.core.config import Settings
from app.evaluators.base import BaseEvaluator
from app.evaluators.transformers_evaluator import TransformersEvaluator


class EvaluatorFactory:
    BACKENDS = {
        "qwen": lambda settings: TransformersEvaluator(
            "qwen",
            settings.qwen_model_name,
            max_new_tokens=settings.generation_max_new_tokens,
            temperature=settings.generation_temperature,
        ),
    }

    def __init__(self, settings: Settings):
        self.settings = settings

    def create(self, backend: str) -> BaseEvaluator:
        try:
            return self.BACKENDS[backend](self.settings)
        except KeyError as exc:
            supported = ", ".join(sorted(self.BACKENDS))
            raise ValueError(
                f"unsupported evaluator backend '{backend}'. Supported: {supported}"
            ) from exc
