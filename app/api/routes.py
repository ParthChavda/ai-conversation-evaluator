from flask import Blueprint, current_app, jsonify, request
from pydantic import ValidationError

from app.models.schemas import EvaluateRequest, HealthResponse

api_bp = Blueprint("api", __name__)


@api_bp.get("/health")
def health():
    container = current_app.extensions["container"]
    payload = HealthResponse(
        status="ok",
        service=current_app.config["APP_NAME"],
        evaluator_backend=container.settings.evaluator_backend,
        evaluator_model=container.settings.qwen_model_name,
        enabled_facets=len(container.facet_registry.all()),
        facet_batch_size=container.settings.facet_batch_size,
        max_facets_per_request=container.settings.max_facets_per_request,
    )
    return jsonify(payload.model_dump(mode="json"))


@api_bp.get("/facets")
def facets():
    container = current_app.extensions["container"]
    include_disabled = request.args.get("include_disabled", "false").lower() == "true"
    category = request.args.get("category")
    categories = [category] if category else None
    items = container.facet_registry.filter(
        categories=categories, include_disabled=include_disabled
    )
    return jsonify(
        {
            "facets": [facet.model_dump(mode="json") for facet in items],
            "count": len(items),
            "categories": container.facet_registry.categories(),
        }
    )


@api_bp.post("/evaluate")
def evaluate():
    container = current_app.extensions["container"]
    try:
        payload = EvaluateRequest.model_validate(request.get_json(force=True))
    except ValidationError as exc:
        return jsonify({"error": "validation_error", "details": exc.errors()}), 422

    selected_facets = container.facet_registry.filter(
        facet_ids=payload.facet_ids,
        categories=payload.categories,
        include_disabled=payload.include_disabled,
    )
    if len(selected_facets) > container.settings.max_facets_per_request:
        return (
            jsonify(
                {
                    "error": "too_many_facets",
                    "max_facets_per_request": container.settings.max_facets_per_request,
                    "selected_facets": len(selected_facets),
                }
            ),
            400,
        )

    result = container.pipeline.run(payload)
    return jsonify(result.model_dump(mode="json"))


@api_bp.get("/conversation/<conversation_id>")
def conversation(conversation_id: str):
    container = current_app.extensions["container"]
    conversation_record = container.store.get_conversation(conversation_id)
    result = container.store.get_result(conversation_id)
    if not conversation_record:
        return jsonify({"error": "not_found", "conversation_id": conversation_id}), 404
    return jsonify(
        {
            "conversation": conversation_record.model_dump(mode="json"),
            "latest_evaluation": result.model_dump(mode="json") if result else None,
        }
    )
