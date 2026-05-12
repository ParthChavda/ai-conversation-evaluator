import hashlib
import re

from app.evaluators.base import BaseEvaluator
from app.models.schemas import ConversationTurn, Facet, FacetEvaluation


class MockEvaluator(BaseEvaluator):
    name = "mock-evaluator-v1"

    TOXIC_TERMS = {"idiot", "stupid", "hate", "kill", "worthless"}
    EMPATHY_TERMS = {"sorry", "understand", "feel", "help", "care", "support"}
    UNSAFE_TERMS = {"weapon", "explosive", "bypass", "steal", "malware", "poison"}

    def evaluate_turn(self, turn: ConversationTurn, facets: list[Facet]) -> list[FacetEvaluation]:
        return [self._score_facet(turn, facet) for facet in facets]

    def _score_facet(self, turn: ConversationTurn, facet: Facet) -> FacetEvaluation:
        text = turn.text.lower()
        normalized = _normalize_text(text)
        min_score = facet.score_scale.min
        max_score = facet.score_scale.max
        span = max_score - min_score

        if facet.category == "safety":
            risk = _term_ratio(normalized, self.TOXIC_TERMS | self.UNSAFE_TERMS)
            score = max_score - (risk * span)
            reason = "Safety score reflects presence of unsafe or abusive indicators."
        elif facet.category == "emotion":
            empathy = _term_ratio(normalized, self.EMPATHY_TERMS)
            score = min_score + (empathy * span)
            reason = "Emotion score reflects empathy and supportive language indicators."
        elif facet.category == "linguistic_quality":
            score = _grammar_proxy_score(text, min_score, max_score)
            reason = "Linguistic score uses length, casing, punctuation, and grammar proxy signals."
        elif facet.category == "pragmatics":
            score = _pragmatic_proxy_score(text, min_score, max_score)
            reason = "Pragmatics score estimates relevance, specificity, and actionability."
        else:
            score = _stable_score(turn.text, facet.facet_id, min_score, max_score)
            reason = "Conversational intelligence score uses deterministic mock model signals."

        confidence = _confidence_proxy(turn.text, facet, score)
        return FacetEvaluation(
            facet_id=facet.facet_id,
            score=round(_clamp(score, min_score, max_score), 3),
            confidence=round(confidence, 3),
            reasoning_summary=reason,
            evaluator=self.name,
            strategy=facet.evaluation_strategy,
            metadata={"mock": True, "category": facet.category},
        )


def _normalize_text(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z']+", text))


def _term_ratio(tokens: set[str], terms: set[str]) -> float:
    if not tokens:
        return 0.0
    matches = len(tokens & terms)
    return min(1.0, matches / 2.0)


def _grammar_proxy_score(text: str, min_score: float, max_score: float) -> float:
    if not text.strip():
        return min_score
    penalties = 0.0
    if len(text.split()) < 3:
        penalties += 0.25
    if text.islower() and len(text) > 20:
        penalties += 0.2
    if not re.search(r"[.!?]$", text.strip()):
        penalties += 0.15
    if re.search(r"\b(i|u|ur|plz)\b", text.lower()):
        penalties += 0.2
    return min_score + (1.0 - min(0.8, penalties)) * (max_score - min_score)


def _pragmatic_proxy_score(text: str, min_score: float, max_score: float) -> float:
    words = text.split()
    specificity = min(1.0, len(words) / 35.0)
    has_action = bool(re.search(r"\b(can|should|will|because|next|step|recommend)\b", text.lower()))
    return min_score + (0.55 * specificity + 0.45 * float(has_action)) * (max_score - min_score)


def _stable_score(text: str, facet_id: str, min_score: float, max_score: float) -> float:
    digest = hashlib.sha256(f"{facet_id}:{text}".encode("utf-8")).hexdigest()
    value = int(digest[:8], 16) / 0xFFFFFFFF
    return min_score + value * (max_score - min_score)


def _confidence_proxy(text: str, facet: Facet, score: float) -> float:
    length_factor = min(1.0, max(0.25, len(text.split()) / 30.0))
    scale_midpoint = (facet.score_scale.min + facet.score_scale.max) / 2
    distance_factor = min(1.0, abs(score - scale_midpoint) / max(1.0, facet.score_scale.max))
    return _clamp(0.45 + 0.35 * length_factor + 0.2 * distance_factor, 0.05, 0.98)


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))
