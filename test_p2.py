import asyncio
import sys
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_phase2_suite():
    print("=" * 60)
    print("🚀 开始执行 Phase 2 (P2) 核心能力全链路自动化测试")
    print("=" * 60)

    # 1. 测试运行模式切换
    print("\n[测试 1] 运行模式动态切换 (Copilot <-> Auto-Pilot)")
    res = client.get("/api/system/mode")
    assert res.status_code == 200, f"获取系统模式失败: {res.text}"
    print(f"  当前系统运行模式: {res.json()['mode']}")

    res_toggle = client.post("/api/system/mode", json={"mode": "auto_pilot"})
    assert res_toggle.status_code == 200 and res_toggle.json()["current_mode"] == "auto_pilot"
    print("  ✅ 成功切换至 [智能自主应答 (Auto-Pilot)] 模式")

    # 2. 测试低风险标准 FAQ 的 Auto-Pilot 自主应答放行
    print("\n[测试 2] 低风险 FAQ 业务咨询 -> Auto-Pilot 自动直答放行")
    faq_payload = {
        "user_id": "u1001",
        "query": "请问平台的洗码和返水结算时间是什么时候？",
        "auth_token": "valid_token",
        "lang": "zh",
        "mode": "auto_pilot"
    }
    res_faq = client.post("/api/chat/process-v2", json=faq_payload)
    assert res_faq.status_code == 200
    faq_data = res_faq.json()

    assert faq_data["risk"]["risk_level"] == "LOW", f"预期低风险，实际: {faq_data['risk']['risk_level']}"
    assert faq_data["action"] == "AUTO_PILOT_REPLY", f"预期自主直答，实际: {faq_data['action']}"
    assert faq_data["is_auto_replied"] is True
    print(f"  ⚡ 耗时: {faq_data['total_latency_ms']} ms")
    print(f"  🤖 自主应答判定: action={faq_data['action']}, can_auto_reply={faq_data['can_auto_reply']}")
    print(f"  📝 自主回复内容摘要: {faq_data['draft'][:60]}...")
    print("  ✅ 低风险场景顺利通过 JEV 质检并执行 Auto-Pilot 自主应答！")

    # 3. 测试高风险账务流水未满场景 -> 自动拦截自主应答，降级为 Copilot 或转接
    print("\n[测试 3] 高风险账务流水卡单 -> 拦截自主直答，生成诊断并自动创建工单")
    billing_payload = {
        "user_id": "u1001",
        "query": "为什么我的提现一直不到账？快帮我看看！",
        "auth_token": "valid_token",
        "lang": "zh",
        "mode": "auto_pilot"
    }
    res_billing = client.post("/api/chat/process-v2", json=billing_payload)
    assert res_billing.status_code == 200
    billing_data = res_billing.json()

    assert billing_data["risk"]["risk_level"] == "HIGH", f"预期高风险，实际: {billing_data['risk']['risk_level']}"
    assert billing_data["can_auto_reply"] is False, "高风险流水差额严禁自动自主应答！"
    assert billing_data["is_auto_replied"] is False
    assert billing_data["auto_ticket"] is not None, "高风险账务异常必须自动创建追查工单！"
    print(f"  🚨 风险评估: level={billing_data['risk']['risk_level']}, score={billing_data['risk']['risk_score']}")
    print(f"  🎫 自动创建追查工单: ID={billing_data['auto_ticket']['ticket_id']}, 标题={billing_data['auto_ticket']['title']}")
    print(f"  📋 诊断卡告警: {billing_data['risk']['diagnostic_card']['alert_title']} -> {billing_data['risk']['diagnostic_card']['details']}")
    print("  ✅ 成功阻断高风险自动应答，生成事件诊断卡并进入人工复核闭环！")

    # 4. 测试跨语言多维情绪危机识别 (Sentiment & Crisis Analyzer)
    print("\n[测试 4] 多语言客诉危机识别 (Angry / P0 Crisis)")
    crisis_queries = [
        ("zh", "你们这什么黑平台？！吃了我两千块钱不给出款，再不退钱我马上去报警打官司！"),
        ("en", "You scammers stole my funds! Give back my money or I will report to police and sue!"),
        ("vi", "Lừa đảo ăn quỵt tiền của tôi, tôi sẽ báo công an bóc phốt tụi bây!"),
        ("th", "เว็บโกง ไม่ยอมจ่ายเงิน จะแจ้งความตำรวจฟ้องร้องให้ถึงที่สุด!")
    ]

    for lang, q in crisis_queries:
        res_crisis = client.post("/api/chat/process-v2", json={
            "user_id": "u1001",
            "query": q,
            "auth_token": "valid_token",
            "lang": lang
        })
        c_data = res_crisis.json()
        sentiment = c_data["sentiment"]
        assert sentiment["urgency"] == "P0_CRITICAL", f"语种 {lang} 危机级别未识别为 P0: {sentiment}"
        print(f"  [{lang.upper()}] 情绪判定={sentiment['sentiment_label']}, 焦虑分值={sentiment['sentiment_score']}, 紧急度={sentiment['urgency']}")

    print("  ✅ 四国语言多维危机预警与升级策略 100% 识别达标！")

    # 5. 测试全生命周期工单状态流转
    print("\n[测试 5] 全生命周期工单流转与闭环测试")
    create_res = client.post("/api/tickets/create", json={
        "user_id": "u1001",
        "username": "vip_player_88",
        "category": "WITHDRAWAL_TURNOVER",
        "title": "测试流水核验终审工单",
        "details": "有效投注已补齐至52000元，满足出款条件",
        "priority": "P1",
        "order_id": "TX20261005001",
        "assigned_to": "Felix (财务对账组)"
    })
    assert create_res.status_code == 200
    new_ticket = create_res.json()["ticket"]
    t_id = new_ticket["ticket_id"]
    print(f"  1. 成功创建工单: {t_id}, 初始状态: {new_ticket['status_label']}")

    update_res = client.post("/api/tickets/update", json={
        "ticket_id": t_id,
        "new_status": "PAYOUT_APPROVED",
        "operator": "Felix",
        "note": "经人工复核有效打码已超额达标，审核放行通过"
    })
    assert update_res.status_code == 200
    updated_ticket = update_res.json()["ticket"]
    assert updated_ticket["status"] == "PAYOUT_APPROVED"
    print(f"  2. 状态流转 -> [{updated_ticket['status_label']}], 操作审计日志数: {len(updated_ticket['logs'])}")

    # 恢复模式为默认
    client.post("/api/system/mode", json={"mode": "copilot"})
    print("\n" + "=" * 60)
    print("🎉 Phase 2 (P2) 所有核心服务与业务模型测试 100% 通过！")
    print("=" * 60)

if __name__ == "__main__":
    test_phase2_suite()
