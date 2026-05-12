from app.evaluators.transformers_evaluator import TransformersEvaluator
from app.models.schemas import ConversationTurn, Facet


def test_transformers_parser_builds_valid_facet_evaluation():
    evaluator = TransformersEvaluator("qwen", "local-test-model")
    facet = Facet.model_validate(
        {
            "facet_id": "safety.toxicity",
            "name": "Toxicity Avoidance",
            "category": "safety",
            "description": "Avoids abusive language.",
            "evaluation_strategy": "safety",
        }
    )
    turn = ConversationTurn(role="assistant", text="I can help with that.")
    payload = {
        "score": 4.8,
        "confidence": 0.91,
        "reasoning_summary": "The response is respectful and safe.",
    }

    result = evaluator._evaluation_from_payload(turn, facet, payload)

    assert result.score == 4.8
    assert result.confidence == 0.91
    assert result.evaluator == "qwen:local-test-model"


def test_transformers_parser_uses_fallback_for_missing_json():
    evaluator = TransformersEvaluator("qwen", "local-test-model")
    parsed = evaluator._parse_response("not json")

    assert parsed == {}
