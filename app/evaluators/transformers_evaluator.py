import json
import re
from functools import lru_cache
from typing import Any

from app.evaluators.base import BaseEvaluator
from app.models.schemas import ConversationTurn, Facet, FacetEvaluation


class TransformersEvaluator(BaseEvaluator):
    """Open-weight LLM adapter for batched facet scoring.

    The adapter uses one prompt per turn/facet batch and asks the model to
    return strict JSON. Production deployments can replace the local
    transformers call with vLLM/TGI behind this same interface.
    """

    def __init__(
        self,
        model_family: str,
        model_name: str,
        max_new_tokens: int = 768,
        temperature: float = 0.0,
    ):
        self.model_family = model_family
        self.model_name = model_name
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self.name = f"{model_family}:{model_name}"

    def evaluate_turn(self, turn: ConversationTurn, facets: list[Facet]) -> list[FacetEvaluation]:
        tokenizer, model, device = self.load_model(self.model_name)
        prompt = self._build_prompt(turn, facets)
        input_ids = self._encode_prompt(tokenizer, prompt, device)
        generation_kwargs: dict[str, Any] = {
            "max_new_tokens": self.max_new_tokens,
            "do_sample": self.temperature > 0,
            "pad_token_id": tokenizer.eos_token_id,
        }
        if self.temperature > 0:
            generation_kwargs["temperature"] = self.temperature

        output_ids = model.generate(input_ids, **generation_kwargs)
        generated_ids = output_ids[0][input_ids.shape[-1] :]
        raw_text = tokenizer.decode(generated_ids, skip_special_tokens=True)
        parsed = self._parse_response(raw_text)
        return [self._evaluation_from_payload(turn, facet, parsed.get(facet.facet_id)) for facet in facets]

    @staticmethod
    @lru_cache(maxsize=2)
    def load_model(model_name: str):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(model_name)
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=dtype)
        device = _best_device()
        model.to(device)
        model.eval()
        return tokenizer, model, device

    def _build_prompt(self, turn: ConversationTurn, facets: list[Facet]) -> str:
        facet_specs = [
            {
                "facet_id": facet.facet_id,
                "name": facet.name,
                "category": facet.category,
                "description": facet.description,
                "scale": facet.score_scale.model_dump(),
                "strategy": facet.evaluation_strategy.value,
            }
            for facet in facets
        ]
        return (
            "You are an evaluation model scoring one conversation turn.\n"
            "Return only valid JSON. Do not include markdown or commentary.\n"
            "For each facet, produce score, confidence, and reasoning_summary.\n"
            "Confidence must be between 0 and 1. Score must stay within the facet scale.\n\n"
            f"Conversation turn:\n{json.dumps(turn.model_dump(mode='json'), ensure_ascii=False)}\n\n"
            f"Facets:\n{json.dumps(facet_specs, ensure_ascii=False)}\n\n"
            "Required response schema:\n"
            "{\"evaluations\":[{\"facet_id\":\"...\",\"score\":0.0,\"confidence\":0.0,"
            "\"reasoning_summary\":\"short reason\"}]}"
        )

    def _encode_prompt(self, tokenizer, prompt: str, device: str):
        messages = [
            {"role": "system", "content": "You are a precise, conservative conversation quality evaluator."},
            {"role": "user", "content": prompt},
        ]
        if hasattr(tokenizer, "apply_chat_template") and tokenizer.chat_template:
            encoded = tokenizer.apply_chat_template(
                messages,
                add_generation_prompt=True,
                return_tensors="pt",
            )
        else:
            encoded = tokenizer(prompt, return_tensors="pt").input_ids
        return encoded.to(device)

    def _parse_response(self, raw_text: str) -> dict[str, dict[str, Any]]:
        payload = _extract_json(raw_text)
        evaluations = payload.get("evaluations", []) if isinstance(payload, dict) else []
        parsed: dict[str, dict[str, Any]] = {}
        for item in evaluations:
            if isinstance(item, dict) and isinstance(item.get("facet_id"), str):
                parsed[item["facet_id"]] = item
        return parsed

    def _evaluation_from_payload(
        self,
        turn: ConversationTurn,
        facet: Facet,
        payload: dict[str, Any] | None,
    ) -> FacetEvaluation:
        if not payload:
            return FacetEvaluation(
                facet_id=facet.facet_id,
                score=facet.score_scale.min,
                confidence=0.05,
                reasoning_summary="Model did not return a valid evaluation for this facet.",
                evaluator=self.name,
                strategy=facet.evaluation_strategy,
                metadata={"model_family": self.model_family, "parse_fallback": True, "turn_id": turn.turn_id},
            )

        score = _clamp_float(payload.get("score"), facet.score_scale.min, facet.score_scale.max)
        confidence = _clamp_float(payload.get("confidence"), 0.0, 1.0)
        reason = str(payload.get("reasoning_summary") or "Model returned a score without a reasoning summary.")
        return FacetEvaluation(
            facet_id=facet.facet_id,
            score=round(score, 3),
            confidence=round(confidence, 3),
            reasoning_summary=reason[:500],
            evaluator=self.name,
            strategy=facet.evaluation_strategy,
            metadata={"model_family": self.model_family, "model_name": self.model_name},
        )


def _extract_json(raw_text: str) -> dict[str, Any]:
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw_text, flags=re.DOTALL)
        if not match:
            return {}
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return {}


def _clamp_float(value: Any, lower: float, upper: float) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return lower
    return max(lower, min(upper, numeric))


def _best_device() -> str:
    import torch

    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"
