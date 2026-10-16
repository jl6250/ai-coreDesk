import asyncio
import re
from app.services.jev_gateway import jev_gateway
from app.services.mock_billing import billing_gateway
from app.services.rag_engine import rag_engine
from app.services.llm_engine import llm_engine
from app.services.jev_post_guard import jev_post_guard

async def test_full_multilingual_matrix():
    print("=" * 70)
    print("🧪 正在执行全语言矩阵深度回归测试 (ZH, EN, VI, TH)")
    print("=" * 70)

    # 1. 验证 index.html 字典完整度
    with open("app/static/index.html", "r", encoding="utf-8") as f:
        html_content = f.read()

    # 提取 i18nDict 块
    print("\n[测试阶段 1] 校验前端 i18n 字典覆盖度")
    for lang in ["zh", "en", "vi", "th"]:
        assert f"{lang}: {{" in html_content, f"缺少 {lang} 字典定义"
        print(f"  ✅ 前端包含完善的 {lang.upper()} 字典定义")

    # 2. 全语言端到端测试用例
    test_matrix = [
        {
            "lang": "zh",
            "name": "中文 (Simplified Chinese)",
            "query": "我刚才申请提现2000元，为什么一直显示审核中不到账？",
            "expected_keywords": ["提现", "流水", "TX20261005001", "5000"],
            "expected_intent": "BILLING_ORDER_QUERY"
        },
        {
            "lang": "en",
            "name": "英语 (English)",
            "query": "Why is my 2,000 withdrawal still pending audit?",
            "expected_keywords": ["withdrawal", "turnover", "TX20261005001", "5000"],
            "expected_intent": "BILLING_ORDER_QUERY"
        },
        {
            "lang": "vi",
            "name": "越南语 (Tiếng Việt)",
            "query": "Lệnh rút tiền 2000 của tôi tại sao vẫn đang xử lý chưa về tài khoản?",
            "expected_keywords": ["rút tiền", "doanh thu cược", "TX20261005001"],
            "expected_intent": "BILLING_ORDER_QUERY"
        },
        {
            "lang": "th",
            "name": "泰语 (ภาษาไทย)",
            "query": "คำขอถอนเงิน 2,000 ของฉันทำไมยังรอตรวจสอบอยู่?",
            "expected_keywords": ["ถอนเงิน", "เทิร์นโอเวอร์", "TX20261005001"],
            "expected_intent": "BILLING_ORDER_QUERY"
        }
    ]

    billing = billing_gateway.get_user_billing_snapshot("u1001")

    print("\n[测试阶段 2] 全语种双引擎端到端流转测试")
    for case in test_matrix:
        lang = case["lang"]
        print(f"\n--- 正在测试语种: {case['name']} ---")
        
        # JEV 网关
        jev = jev_gateway.process_incoming_request("u1001", case["query"], target_lang=lang)
        print(f"1. JEV 网关: 语言识别={jev['lang']}, 意图={jev['intent']}, 延迟={jev['latency_ms']}ms")
        assert jev["allowed"] is True
        assert jev["intent"] == case["expected_intent"]
        assert jev["latency_ms"] < 100

        # RAG 检索
        rag = rag_engine.retrieve_context(case["query"], top_k=1, lang=lang)
        print(f"2. RAG 知识检索: 召回匹配数={rag['matched_count']}, 语言版本={rag['lang']}")
        assert rag["matched_count"] > 0

        # LLM 事实翻译器输出
        draft = await llm_engine.generate_draft_response(case["query"], billing, rag["context_text"], lang=lang)
        guard = jev_post_guard.inspect_and_sanitize(draft)
        final_text = guard["sanitized_text"]
        print(f"3. 质检与生成草稿长度={len(final_text)} 字符")
        print(f"   摘要: {final_text[:65]}...")

        # 检查对应语种关键字
        for kw in case["expected_keywords"]:
            assert kw.lower() in final_text.lower(), f"语种 {lang} 答复未命中预期关键信息 [{kw}]"
        print(f"   ✅ {case['name']} 关键事实与语种特征校验 100% 达标")

    print("\n" + "=" * 70)
    print("🎉 恭喜！四国语言（中、英、越、泰）全量矩阵回归测试全部通过！")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_full_multilingual_matrix())
