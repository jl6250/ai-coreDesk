import time
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_im_channels_suite():
    print("=" * 65)
    print("🚀 [IM 渠道网关集成测试] Telegram / WhatsApp / LINE / 账号绑定与幂等")
    print("=" * 65)

    # 1. 测试全渠道连接状态接口
    res = client.get("/api/channels/status")
    assert res.status_code == 200
    status_data = res.json()
    assert status_data["status"] == "HEALTHY"
    assert "telegram" in status_data["channels"]
    assert "whatsapp" in status_data["channels"]
    assert "line" in status_data["channels"]
    print("  ✅ 渠道状态与元数据查询成功: 渠道数量 =", len(status_data["channels"]))

    # 2. 测试 Telegram Webhook 模拟进线
    tg_payload = {
        "update_id": 10001,
        "message": {
            "message_id": 9901,
            "from": {"id": 8829, "username": "tg_trader_88", "first_name": "Alex"},
            "chat": {"id": 8829, "type": "private"},
            "date": int(time.time()),
            "text": "洗码返水结算时间是什么时候？"
        }
    }
    res = client.post("/api/webhook/telegram", json=tg_payload)
    assert res.status_code == 200
    tg_data = res.json()
    assert tg_data["status"] == "OK"
    assert tg_data["result"]["channel"] == "telegram"
    print("  ✅ Telegram 进线调度成功 (FAQ 咨询)")

    # 3. 测试 Meta WhatsApp Webhook 验证握手 (GET)
    res = client.get("/api/webhook/whatsapp?hub.mode=subscribe&hub.verify_token=coredesk_wa_verify_token_2026&hub.challenge=115599")
    assert res.status_code == 200
    assert res.text == "115599"
    print("  ✅ WhatsApp Cloud API Webhook 验证握手成功 (hub.challenge = 115599)")

    # 4. 测试 Meta WhatsApp 消息接收 (POST)
    wa_payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "10002",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {"display_phone_number": "123456", "phone_number_id": "109876"},
                    "contacts": [{"profile": {"name": "Sophea"}, "wa_id": "+85596888888"}],
                    "messages": [{
                        "from": "+85596888888",
                        "id": "wamid.HBgLODU1OTY4ODg4ODgVAgASGBQz",
                        "timestamp": str(int(time.time())),
                        "text": {"body": "查一下我的提现流水还差多少？"},
                        "type": "text"
                    }]
                },
                "field": "messages"
            }]
        }]
    }
    res = client.post("/api/webhook/whatsapp", json=wa_payload)
    assert res.status_code == 200
    wa_data = res.json()
    assert wa_data["status"] == "OK"
    assert wa_data["result"]["platform_user_id"] == "u1001"
    print("  ✅ WhatsApp 进线调度成功 (绑定用户 u1001 账务查询)")

    # 5. 测试 LINE Webhook 消息接收
    line_payload = {
        "destination": "Uxxx",
        "events": [{
            "type": "message",
            "message": {
                "type": "text",
                "id": "line_msg_7788",
                "text": "ฝากเงินทำไมยังไม่เข้า (充值怎么还没到账)"
            },
            "timestamp": int(time.time() * 1000),
            "source": {"type": "user", "userId": "line_user_th01"},
            "replyToken": "token_abc123"
        }]
    }
    res = client.post("/api/webhook/line", json=line_payload)
    assert res.status_code == 200
    line_data = res.json()
    assert line_data["status"] == "OK"
    print("  ✅ LINE 进线调度成功 (泰语多语言自然语言识别)")

    # 6. 测试幂等防重机制 (重复消息阻断)
    res_repeat = client.post("/api/webhook/line", json=line_payload)
    assert res_repeat.status_code == 200
    repeat_data = res_repeat.json()
    assert repeat_data["result"]["status"] == "DUPLICATE_IGNORED"
    print("  ✅ 幂等防重拦截成功 (重复消息自动忽略)")

    # 7. 测试未绑定账号的安全风控拦截与引导
    unbound_sim = {
        "channel": "telegram",
        "channel_user_id": "tg_stranger_9999",
        "text": "我要查我的提现订单 TX20261005001"
    }
    res_unbound = client.post("/api/channels/simulate-inbound", json=unbound_sim)
    assert res_unbound.status_code == 200
    unbound_data = res_unbound.json()
    assert unbound_data["result"]["status"] == "NEED_ACCOUNT_BINDING"
    print("  ✅ 未绑定账号越权查账拦截成功: 提示绑定安全码")

    # 8. 测试通过指令 /bind 完成账号绑定
    bind_sim = {
        "channel": "telegram",
        "channel_user_id": "tg_stranger_9999",
        "text": "/bind u1001"
    }
    res_bind = client.post("/api/channels/simulate-inbound", json=bind_sim)
    assert res_bind.status_code == 200
    bind_data = res_bind.json()
    assert bind_data["result"]["status"] == "BIND_SUCCESS"
    print("  ✅ 动态指令 /bind 安全绑定成功")

    # 9. 再次查询账务，验证已绑定状态直接放行
    res_bound_now = client.post("/api/channels/simulate-inbound", json=unbound_sim)
    assert res_bound_now.status_code == 200
    bound_now_data = res_bound_now.json()
    assert bound_now_data["result"]["status"] == "PROCESSED"
    assert bound_now_data["result"]["is_bound"] is True
    print("  ✅ 绑定后账务只读查询顺利放行通过")

    # 10. 验证全渠道出站与审计日志接口
    res_logs = client.get("/api/channels/audit-logs")
    assert res_logs.status_code == 200
    logs_data = res_logs.json()
    assert len(logs_data["logs"]) > 0
    print("  ✅ 全渠道审计日志追踪成功，日志条数 =", len(logs_data["logs"]))

    print("=" * 65)
    print("🎉 Telegram / WhatsApp / LINE 全渠道即时通讯接入套件测试 100% 通过！")
    print("=" * 65)

if __name__ == "__main__":
    test_im_channels_suite()
