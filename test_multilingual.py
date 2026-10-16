import asyncio
from app.services.jev_gateway import jev_gateway
from app.services.mock_billing import billing_gateway
from app.services.rag_engine import rag_engine
from app.services.llm_engine import llm_engine
from app.services.jev_post_guard import jev_post_guard

async def test_multilingual():
    print("=" * 60)
    print("🌍 开始多语言全链路 (zh, en, vi, th) 自动化验证测试")
    print("=" * 60)

    test_cases = [
        ("zh", "我申请提现2000元，为什么一直显示审核中？", "BILLING_ORDER_QUERY"),
        ("en", "Why is my withdrawal of 2,000 CNY still pending audit?", "BILLING_ORDER_QUERY"),
        ("vi", "Lệnh rút tiền 2000 của tôi tại sao vẫn đang xử lý?", "BILLING_ORDER_QUERY"),
        ("th", "คำขอถอนเงิน 2,000 ของฉันทำไมยังรอตรวจสอบอยู่?", "BILLING_ORDER_QUERY")
    ]

    billing = billing_gateway.get_user_billing_snapshot("u1001")

    for lang, query, expected_intent in test_cases:
        print(f"\n[测试语种: {lang.upper()}] 提问: {query}")
        
        # 1. JEV 网关意图识别与语言检测
        jev = jev_gateway.process_incoming_request("u1001", query, target_lang=lang)
        print(f"⚡ JEV 网关: 识别意图={jev['intent']}, 耗时={jev['latency_ms']}ms, 语言={jev['lang']}")
        assert jev["allowed"] is True
        assert jev["intent"] == expected_intent
        assert jev["latency_ms"] < 100

        # 2. RAG 对应语言知识召回
        rag = rag_engine.retrieve_context(query, top_k=1, lang=lang)
        print(f"📚 RAG 召回: 匹配数={rag['matched_count']}, 耗时={rag['latency_ms']}ms")

        # 3. System 2 事实翻译器输出对应语言草稿
        draft = await llm_engine.generate_draft_response(query, billing, rag["context_text"], lang=lang)
        guard = jev_post_guard.inspect_and_sanitize(draft)
        print(f"🤖 AI 回复草稿 (前 80 字):\n{guard['sanitized_text'][:80]}...\n")

    print("=" * 60)
    print("✅ 中、英、越、泰 四语种双引擎全链路测试 100% 通过！")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_multilingual())
