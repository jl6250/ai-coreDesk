import re
import time
from typing import Dict, Any, List

class JEVPostComplianceGuard:
    """
    🔒 JEV 后置合规质检 (拦截超额承诺与敏感泄露)
    职责:
    1. 敏感信息 (PII) 脱敏: 隐藏手机号、银行卡号完整位数
    2. 拦截超额承诺: 严禁出现绝对化承诺 (如"保证100%到账", "10分钟必赔", "包赚不赔")
    3. 输出合规标记与告警
    """

    PROHIBITED_PROMISES = [
        (r"保证\s*(100%|绝对|肯定).*到账", "禁止对出款时效做绝对性承诺"),
        (r"(100%|包赔|稳赢|必中|稳赚)", "严禁出现赌资包赔或盈利误导话术"),
        (r"我(私下|马上|单独)给您(退款|补款|入账)", "严禁坐席私自承诺补偿"),
        (r"不用(打码|流水)直接提现", "严禁违背平台资金流水合规政策")
    ]

    def inspect_and_sanitize(self, raw_text: str) -> Dict[str, Any]:
        start = time.perf_counter()
        passed = True
        risk_tags: List[str] = []
        sanitized_text = raw_text

        # 1. 超额承诺检测
        for pattern, reason in self.PROHIBITED_PROMISES:
            if re.search(pattern, raw_text):
                passed = False
                risk_tags.append(reason)
                # 自动降级修正或打上阻断标记
                sanitized_text = re.sub(pattern, "【合规修正：请以系统实际审核结果为准】", sanitized_text)

        # 2. PII 数据脱敏 (银行卡号脱敏: 保留前4后4)
        def mask_bank_card(match):
            card = match.group(0)
            if len(card) >= 16:
                return card[:4] + "****" * ((len(card) - 8) // 4) + card[-4:]
            return card

        sanitized_text = re.sub(r"\b\d{16,19}\b", mask_bank_card, sanitized_text)

        # 3. 手机号脱敏 (保留前3后4: 138****8888)
        sanitized_text = re.sub(r"\b(1[3-9]\d)\d{4}(\d{4})\b", r"\1****\2", sanitized_text)

        latency_ms = (time.perf_counter() - start) * 1000

        return {
            "passed": passed,
            "has_pii_masked": (sanitized_text != raw_text),
            "risk_tags": risk_tags,
            "sanitized_text": sanitized_text,
            "latency_ms": round(latency_ms, 2)
        }

jev_post_guard = JEVPostComplianceGuard()
