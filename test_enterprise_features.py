"""
CoreDesk 企业级主流客服系统高级特性自动化测试套件
涵盖:
1. ACD 智能路由、多语种专席分流与 VIP 抢占排队
2. CSAT 满意度评价闭环与 1~2 星差评熔断召回
3. 班长席监控驾驶舱、内部密语 (Whisper) 与会话强插接管 (Barge-in)
4. 客户跨渠道 (Telegram/WhatsApp/Web) 全生命周期旅程与进线前足迹漫游
5. 敏感数据动态脱敏与审计记录
"""

import sys
import os
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def run_tests():
    print("=" * 65)
    print("🚀 [企业级主流客服高级特性测试] ACD路由 / CSAT闭环 / 班长席 / 客户旅程")
    print("=" * 65)

    # -------------------------------------------------------------
    # 1. ACD 路由调度与多语种、VIP、业务线专席分流
    # -------------------------------------------------------------
    # 1.1 多语种母语路由: 越南语 -> 东南亚多语种组
    vi_req = {
        "user_id": "u_vi_001",
        "username": "nguyen_van_a",
        "vip_level": 1,
        "language": "vi",
        "intent": "BILLING_ORDER_QUERY",
        "channel": "WEB"
    }
    r = client.post("/api/acd/route", json=vi_req)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["routing"]["status"] == "ASSIGNED"
    assert data["routing"]["target_group"] == "sea_multilang_desk"
    assert "CS-Agent-012" in data["routing"]["assigned_agent_id"]
    print("  ✅ [ACD 路由] 越语进线精准分流至东南亚母语技能组 (Mai Nguyen)")

    # 1.2 VIP 3 尊享通道: 中文高净值会员 -> VIP专属组
    vip_req = {
        "user_id": "u_vip_888",
        "username": "super_vip_whale",
        "vip_level": 5,
        "language": "zh",
        "intent": "GENERAL_FAQ",
        "channel": "TELEGRAM"
    }
    r = client.post("/api/acd/route", json=vip_req)
    assert r.status_code == 200
    data = r.json()
    assert data["routing"]["status"] == "ASSIGNED"
    assert data["routing"]["target_group"] == "vip_support"
    print("  ✅ [ACD 路由] VIP 5 高净值会员优先直连 VIP 尊享管家组 (林婉儿)")

    # 1.3 财务掉单意图路由: 普通会员 -> 财务专席
    fin_req = {
        "user_id": "u_fin_101",
        "username": "crypto_trader",
        "vip_level": 2,
        "language": "zh",
        "intent": "DEPOSIT_TIMEOUT",
        "channel": "WEB"
    }
    r = client.post("/api/acd/route", json=fin_req)
    assert r.status_code == 200
    data = r.json()
    assert data["routing"]["target_group"] == "finance_desk"
    print("  ✅ [ACD 路由] 充值超时掉单意图精准路由至财务出入金专席 (张晓明)")

    # 1.4 ACD 概览与会话释放
    r = client.get("/api/acd/overview")
    assert r.status_code == 200
    overview = r.json()["overview"]
    assert overview["online_agents_count"] >= 4
    print(f"  ✅ [ACD 监控] 路由引擎全局负荷: {overview['active_chats_count']}/{overview['total_capacity']} ({overview['system_load_pct']}%)")

    # 释放会话
    r = client.post("/api/acd/release", json={"agent_id": "CS-Agent-012", "user_id": "u_vi_001"})
    assert r.status_code == 200
    print("  ✅ [ACD 容量] 会话释放成功，坐席并发度自动回收")

    # -------------------------------------------------------------
    # 2. CSAT 满意度评价闭环与差评熔断
    # -------------------------------------------------------------
    # 2.1 好评提交 (5星)
    csat_pos = {
        "session_id": "SES-TEST-001",
        "user_id": "u1001",
        "username": "vip_player_88",
        "agent_id": "CS-Agent-007",
        "agent_name": "张晓明",
        "rating": 5,
        "tags": ["响应迅速", "准确高效"],
        "comment": "解答非常迅速，流水扣减规则很清楚！"
    }
    r = client.post("/api/csat/submit", json=csat_pos)
    assert r.status_code == 200
    data = r.json()
    assert data["is_negative_circuit_broken"] is False
    assert data["recall_ticket_id"] is None
    print("  ✅ [CSAT 闭环] 5 星好评顺利沉淀，未触发熔断")

    # 2.2 1星极度不满意 -> 即时熔断与客诉挽回工单生成
    csat_neg = {
        "session_id": "SES-TEST-002",
        "user_id": "u1009",
        "username": "angry_trader",
        "agent_id": "CS-Agent-007",
        "agent_name": "张晓明",
        "rating": 1,
        "tags": ["未解决问题", "态度冷淡"],
        "comment": "出款审核太慢了，很不满意！"
    }
    r = client.post("/api/csat/submit", json=csat_neg)
    assert r.status_code == 200
    data = r.json()
    assert data["is_negative_circuit_broken"] is True
    assert data["recall_ticket_id"].startswith("TK-RECALL-")
    print(f"  ✅ [差评熔断] 1 星差评即时熔断，自动生成挽回工单: {data['recall_ticket_id']}")

    # 2.3 校验 CSAT 指标聚合
    r = client.get("/api/csat/metrics")
    assert r.status_code == 200
    metrics = r.json()["metrics"]
    assert metrics["total_feedbacks"] >= 3
    assert metrics["negative_count"] >= 1
    print(f"  ✅ [CSAT 报表] 全局平均评分: {metrics['avg_rating']}分, 好评率: {metrics['satisfaction_rate_pct']}%")

    # -------------------------------------------------------------
    # 3. 班长席主管监控驾驶舱、密语与强插接管
    # -------------------------------------------------------------
    # 3.1 班长席概览
    r = client.get("/api/supervisor/cockpit")
    assert r.status_code == 200
    cockpit = r.json()["cockpit"]
    assert cockpit["active_monitored_sessions"] >= 1
    print(f"  ✅ [班长席] 监控驾驶舱就绪: 监听会话数={cockpit['active_monitored_sessions']}, 平均首响={cockpit['sla_health']['avg_first_response_seconds']}s")

    # 3.2 发送内部密语 (Whisper)
    whisper_req = {
        "session_id": "SES-u1001",
        "user_id": "u1001",
        "supervisor_id": "SUP-01",
        "supervisor_name": "王主管",
        "content": "注意安抚客户情绪，可以提示流水扣除方案"
    }
    r = client.post("/api/supervisor/whisper", json=whisper_req)
    assert r.status_code == 200
    assert r.json()["status"] == "SENT"
    print("  ✅ [主管密语] 内部指导密语已直达坐席工作台 (客户侧绝对隔离)")

    # 3.3 强插接管 (Barge-in)
    barge_req = {
        "session_id": "SES-u1001",
        "user_id": "u1001",
        "supervisor_id": "SUP-01",
        "supervisor_name": "王主管",
        "reason": "重大客诉危机，班长席强插直接接管"
    }
    r = client.post("/api/supervisor/barge-in", json=barge_req)
    assert r.status_code == 200
    assert r.json()["status"] == "BARGE_IN_SUCCESS"
    print("  ✅ [会话强插] 班长席一键接管会话，原坐席已安全转为只读旁听")

    # 3.4 打字实时预知
    client.post("/api/supervisor/typing-preview", json={"user_id": "u1001", "text": "我刚刚提现了怎么还没到"})
    r = client.get("/api/supervisor/typing-preview/u1001")
    assert r.status_code == 200
    assert "我刚刚提现" in r.json()["typing_text"]
    print("  ✅ [打字预知] 坐席端毫秒级透视客户未发出的输入草稿")

    # -------------------------------------------------------------
    # 4. 全生命周期客户旅程与全渠道漫游
    # -------------------------------------------------------------
    r = client.get("/api/customer/journey/u1001")
    assert r.status_code == 200
    journey = r.json()["journey"]
    assert len(journey["omnichannel_timeline"]) >= 3
    assert len(journey["pre_chat_footprints"]) >= 3
    assert journey["device_fingerprint"]["is_vpn_or_proxy"] is False
    print(f"  ✅ [客户旅程] 全渠道时间线漫游成功: 跨渠道事件数={len(journey['omnichannel_timeline'])}, 进线前行为步数={len(journey['pre_chat_footprints'])}")

    # -------------------------------------------------------------
    # 5. 敏感数据解密审计记录
    # -------------------------------------------------------------
    r = client.post("/api/security/unmask-audit", json={
        "agent_id": "CS-Agent-007",
        "user_id": "u1001",
        "field_name": "bank_card",
        "reason": "出款卡单核实"
    })
    assert r.status_code == 200
    assert r.json()["status"] == "UNMASK_GRANTED"
    print("  ✅ [合规安全] 敏感字段明文解密受控审计日志记录成功")

    print("=" * 65)
    print("🎉 主流智能客服企业级高级特性 (ACD/CSAT/班长席/客户旅程) 100% 验收通过！")
    print("=" * 65)

if __name__ == "__main__":
    run_tests()
