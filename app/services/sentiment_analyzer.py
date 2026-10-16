import re
import time
from typing import Dict, Any

class SentimentUrgencyAnalyzer:
    """
    ⚡ Phase 2: 跨语言情绪识别与危机预警分析器
    支持中、英、越、泰四语种的情绪极性、焦虑指数与客诉危机等级研判
    """

    CRISIS_KEYWORDS = {
        "zh": [
            "报警", "打官司", "法务", "法院", "曝光", "投诉", "维权", "黑平台", "退钱", 
            "诈骗平台", "吃钱", "不给退", "找网警", "黑心", "黑钱", "套路", "垃圾"
        ],
        "en": [
            "lawyer", "police", "court", "sue", "scam", "fraud", "expose", "report to authority",
            "stolen", "thieves", "give back my money", "regulator", "chargeback"
        ],
        "vi": [
            "báo công an", "kiện", "lừa đảo", "ăn quỵt", "trả tiền", "bóc phốt", "tố cáo",
            "chiếm đoạt", "ăn cướp", "khốn nạn"
        ],
        "th": [
            "แจ้งความ", "ฟ้องร้อง", "ตำรวจ", "โกง", "หลอกลวง", "คืนเงิน", "ประจาน",
            "ไม่ยอมจ่าย", "เว็บโกง", "เอาเปรียบ"
        ]
    }

    ANXIOUS_KEYWORDS = {
        "zh": ["急", "快点", "到底要多久", "为什么还没到", "快处理", "催一下", "几点能好", "卡单"],
        "en": ["urgent", "hurry", "how long", "still waiting", "asap", "delay", "taking forever"],
        "vi": ["gấp", "nhanh lên", "bao lâu nữa", "sao lâu thế", "giải quyết mau", "kẹt đơn"],
        "th": ["ด่วน", "เร็วๆ หน่อย", "นานจัง", "เมื่อไรจะเข้า", "ทำไมช้า", "รีบๆ"]
    }

    def analyze(self, query: str, lang: str = "zh") -> Dict[str, Any]:
        start = time.perf_counter()
        text_lower = query.lower()

        crisis_words = self.CRISIS_KEYWORDS.get(lang, self.CRISIS_KEYWORDS["en"])
        anxious_words = self.ANXIOUS_KEYWORDS.get(lang, self.ANXIOUS_KEYWORDS["en"])

        matched_crisis = [w for w in crisis_words if w in text_lower]
        matched_anxious = [w for w in anxious_words if w in text_lower]

        # 情绪极性与评级计算
        if matched_crisis:
            sentiment = "ANGRY_CRISIS"
            score = 88 + min(12, len(matched_crisis) * 4)
            urgency = "P0_CRITICAL"
            recommendation = "IMMEDIATE_ESCALATE"
            label_zh = "严重愤怒/客诉危机"
        elif matched_anxious:
            sentiment = "FRUSTRATED"
            score = 55 + min(25, len(matched_anxious) * 5)
            urgency = "P1_URGENT"
            recommendation = "PACIFY_AND_INVESTIGATE"
            label_zh = "焦虑急促/催促进度"
        else:
            sentiment = "NEUTRAL"
            score = 15
            urgency = "P2_NORMAL"
            recommendation = "STANDARD_SERVICE"
            label_zh = "理性平和/常规咨询"

        latency_ms = (time.perf_counter() - start) * 1000

        return {
            "sentiment": sentiment,
            "sentiment_label": label_zh,
            "sentiment_score": score,  # 0 - 100
            "urgency": urgency,        # P0_CRITICAL, P1_URGENT, P2_NORMAL
            "recommendation": recommendation,
            "matched_signals": matched_crisis + matched_anxious,
            "latency_ms": round(latency_ms, 2)
        }

sentiment_analyzer = SentimentUrgencyAnalyzer()
