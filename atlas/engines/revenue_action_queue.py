import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]

FEEDBACK_FILE = (
    BASE_DIR
    / "data"
    / "revenue"
    / "revenue_feedback.json"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "revenue"
    / "revenue_action_queue.json"
)


def load_feedback() -> dict[str, Any]:
    """Revenue Feedbackを読み込む。"""

    if not FEEDBACK_FILE.exists():
        raise FileNotFoundError(
            "revenue_feedback.jsonが"
            "見つかりません："
            f"{FEEDBACK_FILE}"
        )

    try:
        data = json.loads(
            FEEDBACK_FILE.read_text(
                encoding="utf-8",
            )
        )
    except json.JSONDecodeError as error:
        raise ValueError(
            "revenue_feedback.jsonの"
            "JSON形式が不正です。"
        ) from error

    if not isinstance(
        data,
        dict,
    ):
        raise ValueError(
            "revenue_feedback.jsonの"
            "形式が不正です。"
        )

    return data


def classify_action(
    item: dict[str, Any],
) -> dict[str, Any]:
    """Revenue Feedbackを次工程向けに分類する。"""

    action = str(
        item.get(
            "action",
            "",
        )
    ).strip()

    service = str(
        item.get(
            "service",
            "",
        )
    ).strip()

    if action == "MONETIZE":
        destination = "monetization"
        next_engine = (
            "domestic_asp_candidate_queue"
        )

    elif action == "EXPAND_CONTENT":
        destination = "content"
        next_engine = (
            "affiliate_keyword_evaluator"
        )

    elif action == "IMPROVE_CTA":
        destination = "cta"
        next_engine = (
            "revenue_cta_action_queue"
        )

    elif action == "WAIT_APPROVAL":
        destination = "wait"
        next_engine = (
            "affiliate_action_queue"
        )

    elif action == "KEEP":
        destination = "monitor"
        next_engine = (
            "revenue_tracker"
        )

    else:
        destination = "monitor"
        next_engine = (
            "revenue_tracker"
        )

    return {
        "service": service,
        "source_action": action,
        "destination": destination,
        "next_engine": next_engine,
        "priority": int(
            item.get(
                "priority",
                0,
            )
            or 0
        ),
        "clicks": int(
            item.get(
                "clicks",
                0,
            )
            or 0
        ),
        "conversions": int(
            item.get(
                "conversions",
                0,
            )
            or 0
        ),
        "revenue": float(
            item.get(
                "revenue",
                0.0,
            )
            or 0.0
        ),
        "epc": float(
            item.get(
                "epc",
                0.0,
            )
            or 0.0
        ),
        "reason": str(
            item.get(
                "reason",
                "",
            )
        ).strip(),
        "next": str(
            item.get(
                "next",
                "",
            )
        ).strip(),
    }


def build_action_queue(
    feedback: dict[str, Any],
) -> dict[str, Any]:
    """次工程向けAction Queueを作る。"""

    service_actions = feedback.get(
        "service_actions",
        [],
    )

    if not isinstance(
        service_actions,
        list,
    ):
        service_actions = []

    actions: list[
        dict[str, Any]
    ] = []

    for item in service_actions:
        if not isinstance(
            item,
            dict,
        ):
            continue

        actions.append(
            classify_action(
                item
            )
        )

    actions.sort(
        key=lambda item: (
            item["priority"],
            item["clicks"],
        ),
        reverse=True,
    )

    summary = {
        "total": len(actions),
        "monetization": sum(
            1
            for item in actions
            if item["destination"]
            == "monetization"
        ),
        "content": sum(
            1
            for item in actions
            if item["destination"]
            == "content"
        ),
        "cta": sum(
            1
            for item in actions
            if item["destination"]
            == "cta"
        ),
        "wait": sum(
            1
            for item in actions
            if item["destination"]
            == "wait"
        ),
        "monitor": sum(
            1
            for item in actions
            if item["destination"]
            == "monitor"
        ),
    }

    return {
        "summary": summary,
        "actions": actions,
    }


def save_queue(
    data: dict[str, Any],
) -> Path:
    """Action Queueを保存する。"""

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return OUTPUT_FILE


def print_queue(
    data: dict[str, Any],
) -> None:
    """Action Queueを表示する。"""

    print(
        "\n===== Revenue Action Queue =====\n"
    )

    summary = data.get(
        "summary",
        {},
    )

    print(
        "total: "
        f"{summary.get('total', 0)}"
    )

    print(
        "monetization: "
        f"{summary.get('monetization', 0)}"
    )

    print(
        "content: "
        f"{summary.get('content', 0)}"
    )

    print(
        "cta: "
        f"{summary.get('cta', 0)}"
    )

    print(
        "wait: "
        f"{summary.get('wait', 0)}"
    )

    print(
        "monitor: "
        f"{summary.get('monitor', 0)}"
    )

    print()

    actions = data.get(
        "actions",
        [],
    )

    for index, item in enumerate(
        actions,
        start=1,
    ):
        print(
            f"[{index}] "
            f"{item['service']}"
        )

        print(
            "    source action: "
            f"{item['source_action']}"
        )

        print(
            "    destination: "
            f"{item['destination']}"
        )

        print(
            "    next engine: "
            f"{item['next_engine']}"
        )

        print(
            "    priority: "
            f"{item['priority']}"
        )

        print(
            "    clicks: "
            f"{item['clicks']}"
        )

        print()


def main() -> None:
    feedback = (
        load_feedback()
    )

    queue = (
        build_action_queue(
            feedback
        )
    )

    filepath = (
        save_queue(
            queue
        )
    )

    print_queue(
        queue
    )

    print(
        f"保存先：{filepath}"
    )


if __name__ == "__main__":
    main()