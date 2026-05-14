import json

from flask import Blueprint, current_app, render_template

ui_bp = Blueprint("ui", __name__)


@ui_bp.get("/")
def dashboard():
    container = current_app.extensions["container"]
    sample_path = container.settings.resolved_synthetic_dataset_path
    sample = {}
    if sample_path.exists():
        with sample_path.open("r", encoding="utf-8") as handle:
            sample = json.load(handle)["conversations"][0]
    return render_template(
        "dashboard.html", sample=json.dumps({"conversation": sample}, indent=2)
    )
