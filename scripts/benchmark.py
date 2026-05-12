import json
import time

from app import create_app
from app.models.schemas import EvaluateRequest


def main() -> None:
    app = create_app()
    container = app.extensions["container"]
    dataset_path = container.settings.resolved_synthetic_dataset_path
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    started = time.perf_counter()
    results = []
    for conversation in dataset["conversations"]:
        request = EvaluateRequest.model_validate({"conversation": conversation})
        results.append(container.pipeline.run(request))
    elapsed = time.perf_counter() - started
    print(
        json.dumps(
            {
                "conversations": len(results),
                "elapsed_seconds": round(elapsed, 3),
                "turns_per_second": round(sum(len(item.turns) for item in results) / elapsed, 3),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
