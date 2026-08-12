import json
from pathlib import Path
from typing import Any

from engines.affiliate_registry import (
    load_affiliate_registry,
)
from engines.revenue_action_queue import (
    classify_action,
)
from engines.revenue_feedback import (
    evaluate_service,
)


BASE_DIR = Path(__file__).resolve().parents[1]

WEBSITE_DIR = BASE_DIR.parent

DMM_ARTICLE_FILE = (
    WEBSITE_DIR
    / "content"
    / "blog"
    / "dmm-genai-camp-reviews.mdx"
)

REVENUE_SUMMARY_FILE = (
    BASE_DIR
    / "data"
    / "revenue"
    / "revenue_summary.json"
)

REVENUE_FEEDBACK_FILE = (
    BASE_DIR
    / "data"
    / "revenue"
    / "revenue_feedback.json"
)

REVENUE_ACTION_QUEUE_FILE = (
    BASE_DIR
    / "data"
    / "revenue"
    / "revenue_action_queue.json"
)

DOMESTIC_ASP_QUEUE_FILE = (
    BASE_DIR
    / "data"
    / "affiliate_programs"
    / "domestic_asp_candidate_queue.json"
)

DASHBOARD_FILE = (
    BASE_DIR
    / "data"
    / "dashboard"
    / "dashboard.json"
)


class TestFailure(RuntimeError):
    """Phase E E2E Test失敗。"""


def load_json(
    filepath: Path,
) -> dict[str, Any]:
    """JSONファイルを読み込む。"""

    if not filepath.exists():
        raise TestFailure(
            "必要なJSONファイルが"
            "見つかりません："
            f"{filepath}"
        )

    try:
        data = json.loads(
            filepath.read_text(
                encoding="utf-8",
            )
        )
    except json.JSONDecodeError as error:
        raise TestFailure(
            "JSON形式が不正です："
            f"{filepath}"
        ) from error

    if not isinstance(
        data,
        dict,
    ):
        raise TestFailure(
            "JSON最上位がobjectでは"
            "ありません："
            f"{filepath}"
        )

    return data


def assert_true(
    condition: bool,
    message: str,
) -> None:
    """条件を満たさなければテスト失敗。"""

    if not condition:
        raise TestFailure(
            message
        )


def print_ok(
    label: str,
) -> None:
    """成功表示。"""

    print(
        f"[PASS] {label}"
    )


def test_dmm_registry() -> None:
    """DMM案件がpending状態で登録されているか確認。"""

    registry = (
        load_affiliate_registry()
    )

    dmm = registry.get(
        "DMM 生成AI CAMP"
    )

    assert_true(
        isinstance(
            dmm,
            dict,
        ),
        "DMM 生成AI CAMPが"
        "Affiliate Registryにありません。",
    )

    status = str(
        dmm.get(
            "affiliate_status",
            "",
        )
    )

    affiliate_url = str(
        dmm.get(
            "affiliate_url",
            "",
        )
    )

    official_url = str(
        dmm.get(
            "official_url",
            "",
        )
    )

    assert_true(
        status == "pending",
        "DMM 生成AI CAMPの"
        f"statusがpendingではありません：{status}",
    )

    assert_true(
        not affiliate_url,
        "pending案件なのに"
        "affiliate_urlが設定されています。",
    )

    assert_true(
        official_url.startswith(
            "http"
        ),
        "DMM 生成AI CAMPの"
        "official_urlが不正です。",
    )

    print_ok(
        "DMM pending案件のRegistry状態"
    )


def test_dmm_published_article() -> None:
    """DMM記事とofficial CTAを確認。"""

    assert_true(
        DMM_ARTICLE_FILE.exists(),
        "DMM記事がありません："
        f"{DMM_ARTICLE_FILE}",
    )

    content = (
        DMM_ARTICLE_FILE.read_text(
            encoding="utf-8",
        )
    )

    assert_true(
        'service="DMM 生成AI CAMP"'
        in content,
        "DMM記事にAffiliateLinkの"
        "service指定がありません。",
    )

    assert_true(
        'linkType="official"'
        in content,
        "DMM pending記事のCTAが"
        "officialになっていません。",
    )

    assert_true(
        'ctaPlacement="before_faq"'
        in content,
        "DMM記事のCTA placementが"
        "before_faqではありません。",
    )

    assert_true(
        "## よくある質問"
        in content,
        "DMM記事にFAQがありません。",
    )

    assert_true(
        "https://genai.dmm.com/"
        in content,
        "DMM公式URLが記事にありません。",
    )

    print_ok(
        "DMM記事公開・official CTA・FAQ"
    )


def test_revenue_summary() -> None:
    """Revenue Summaryの主要指標を確認。"""

    data = load_json(
        REVENUE_SUMMARY_FILE
    )

    required_keys = {
        "total_clicks",
        "total_conversions",
        "total_revenue",
        "conversion_rate",
        "epc",
        "by_service",
        "by_article",
        "by_cta_placement",
        "by_cta_type",
        "by_link_type",
        "by_network",
    }

    missing = (
        required_keys
        - set(
            data.keys()
        )
    )

    assert_true(
        not missing,
        "Revenue Summaryに"
        "必要項目がありません："
        + ", ".join(
            sorted(
                missing
            )
        ),
    )

    assert_true(
        int(
            data.get(
                "total_clicks",
                0,
            )
        )
        >= 0,
        "total_clicksが不正です。",
    )

    print_ok(
        "Revenue Summary集計"
    )


def test_revenue_feedback() -> None:
    """実Revenue Feedbackを確認。"""

    data = load_json(
        REVENUE_FEEDBACK_FILE
    )

    actions = data.get(
        "service_actions",
        [],
    )

    assert_true(
        isinstance(
            actions,
            list,
        ),
        "service_actionsが"
        "listではありません。",
    )

    assert_true(
        len(actions) > 0,
        "Revenue Feedbackに"
        "service actionがありません。",
    )

    print_ok(
        "Revenue Feedback生成"
    )


def test_revenue_action_queue() -> None:
    """Revenue Action Queueを確認。"""

    data = load_json(
        REVENUE_ACTION_QUEUE_FILE
    )

    summary = data.get(
        "summary",
        {},
    )

    actions = data.get(
        "actions",
        [],
    )

    assert_true(
        isinstance(
            summary,
            dict,
        ),
        "Revenue Action Queueの"
        "summaryが不正です。",
    )

    assert_true(
        isinstance(
            actions,
            list,
        ),
        "Revenue Action Queueの"
        "actionsが不正です。",
    )

    assert_true(
        int(
            summary.get(
                "total",
                0,
            )
        )
        == len(actions),
        "Revenue Action Queueの"
        "summary.totalとactions件数が"
        "一致しません。",
    )

    print_ok(
        "Revenue Action Queue"
    )


def test_domestic_asp_feedback_loop() -> None:
    """Revenue SignalがASP候補へ戻っているか確認。"""

    data = load_json(
        DOMESTIC_ASP_QUEUE_FILE
    )

    candidates = data.get(
        "candidates",
        [],
    )

    assert_true(
        isinstance(
            candidates,
            list,
        ),
        "Domestic ASP Candidate Queueの"
        "candidatesが不正です。",
    )

    chatgpt = None

    for item in candidates:
        if not isinstance(
            item,
            dict,
        ):
            continue

        if (
            str(
                item.get(
                    "service",
                    "",
                )
            )
            == "ChatGPT"
        ):
            chatgpt = item
            break

    assert_true(
        isinstance(
            chatgpt,
            dict,
        ),
        "ChatGPTが国内ASP候補に"
        "存在しません。",
    )

    revenue_signal = (
        chatgpt.get(
            "revenue_signal",
            {},
        )
    )

    assert_true(
        isinstance(
            revenue_signal,
            dict,
        ),
        "ChatGPTのrevenue_signalが"
        "不正です。",
    )

    assert_true(
        int(
            revenue_signal.get(
                "clicks",
                0,
            )
        )
        > 0,
        "ChatGPTのRevenue clickが"
        "ASP候補へ反映されていません。",
    )

    assert_true(
        str(
            revenue_signal.get(
                "destination",
                "",
            )
        )
        == "monetization",
        "ChatGPTのRevenue destinationが"
        "monetizationではありません。",
    )

    print_ok(
        "Revenue → Domestic ASP Feedback Loop"
    )


def test_dashboard() -> None:
    """DashboardへのRevenue統合を確認。"""

    data = load_json(
        DASHBOARD_FILE
    )

    revenue = data.get(
        "revenue",
        {},
    )

    assert_true(
        isinstance(
            revenue,
            dict,
        ),
        "Dashboard revenueが不正です。",
    )

    assert_true(
        "epc"
        in revenue,
        "DashboardにEPCがありません。",
    )

    action_counts = revenue.get(
        "action_counts",
        {},
    )

    assert_true(
        isinstance(
            action_counts,
            dict,
        ),
        "Dashboard Revenue Action Countsが"
        "不正です。",
    )

    top_action = revenue.get(
        "top_revenue_action"
    )

    assert_true(
        isinstance(
            top_action,
            dict,
        ),
        "Dashboard Top Revenue Actionが"
        "ありません。",
    )

    print_ok(
        "Revenue → Atlas Dashboard"
    )


def test_synthetic_improve_cta() -> None:
    """
    productionデータを書き換えず、
    active案件+クリック多数+CV0をテスト。
    """

    registry = {
        "TestService": {
            "affiliate_status": "active",
            "affiliate_url":
                "https://example.com/affiliate",
            "network": "A8.net",
        }
    }

    metrics = {
        "clicks": 25,
        "conversions": 0,
        "revenue": 0,
        "epc": 0,
    }

    result = evaluate_service(
        "TestService",
        metrics,
        registry,
    )

    assert_true(
        result.get(
            "action"
        )
        == "IMPROVE_CTA",
        "IMPROVE_CTA分岐が"
        "正しくありません。",
    )

    queue_item = (
        classify_action(
            result
        )
    )

    assert_true(
        queue_item.get(
            "destination"
        )
        == "cta",
        "IMPROVE_CTAがcta工程へ"
        "振り分けられていません。",
    )

    print_ok(
        "Synthetic IMPROVE_CTA分岐"
    )


def test_synthetic_expand_content() -> None:
    """
    productionデータを書き換えず、
    active案件+成果+高EPCをテスト。
    """

    registry = {
        "TestService": {
            "affiliate_status": "active",
            "affiliate_url":
                "https://example.com/affiliate",
            "network": "A8.net",
        }
    }

    metrics = {
        "clicks": 20,
        "conversions": 2,
        "revenue": 3000,
        "epc": 150,
    }

    result = evaluate_service(
        "TestService",
        metrics,
        registry,
    )

    assert_true(
        result.get(
            "action"
        )
        == "EXPAND_CONTENT",
        "EXPAND_CONTENT分岐が"
        "正しくありません。",
    )

    queue_item = (
        classify_action(
            result
        )
    )

    assert_true(
        queue_item.get(
            "destination"
        )
        == "content",
        "EXPAND_CONTENTがcontent工程へ"
        "振り分けられていません。",
    )

    assert_true(
        queue_item.get(
            "next_engine"
        )
        == "affiliate_keyword_evaluator",
        "EXPAND_CONTENTの次工程が"
        "affiliate_keyword_evaluator"
        "ではありません。",
    )

    print_ok(
        "Synthetic EXPAND_CONTENT分岐"
    )


def main() -> None:
    """Phase E End-to-End Test。"""

    print(
        "\n===== Phase E End-to-End Test =====\n"
    )

    tests = [
        test_dmm_registry,
        test_dmm_published_article,
        test_revenue_summary,
        test_revenue_feedback,
        test_revenue_action_queue,
        test_domestic_asp_feedback_loop,
        test_dashboard,
        test_synthetic_improve_cta,
        test_synthetic_expand_content,
    ]

    passed = 0

    for test in tests:
        try:
            test()
            passed += 1

        except Exception as error:
            print(
                "[FAIL] "
                f"{test.__name__}"
            )

            print(
                f"       {error}"
            )

            raise

    print(
        "\n===== Phase E Test Result =====\n"
    )

    print(
        f"PASS: {passed}/{len(tests)}"
    )

    print(
        "Production data mutation: NONE"
    )

    print(
        "\nPhase Eの主要接続は正常です。"
    )


if __name__ == "__main__":
    main()