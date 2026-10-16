"""
CoreDesk CSAT (Customer Satisfaction) 满意度评价与差评即时熔断回访服务
支持会话结束自动邀评、多维度标签打标、1~2 星差评即时熔断与主管挽回工单自动化
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import uuid

class CSATFeedbackService:
    def __init__(self):
        # 历史评价日志表
        self.feedback_records: List[Dict[str, Any]] = [
            {
                "id": "CSAT-1001",
                "session_id": "SES-20261005-001",
                "user_id": "u1002",
                "username": "lucky_tiger_99",
                "agent_id": "CS-Agent-007",
                "agent_name": "张晓明",
                "rating": 5,
                "dimension_tags": ["响应迅速", "准确高效"],
                "comment": "USDT 区块确认很快帮我查到了，解答很专业！",
                "channel": "WEB",
                "submitted_at": "2026-10-06T14:20:00Z",
                "is_negative": False,
                "ticket_created": None
            },
            {
                "id": "CSAT-1002",
                "session_id": "SES-20261006-004",
                "user_id": "u1008",
                "username": "dragon_slayer",
                "agent_id": "CS-Agent-001",
                "agent_name": "林婉儿",
                "rating": 5,
                "dimension_tags": ["服务贴心", "VIP尊享"],
                "comment": "VIP返水核算及时入账，点赞！",
                "channel": "TELEGRAM",
                "submitted_at": "2026-10-06T16:45:00Z",
                "is_negative": False,
                "ticket_created": None
            }
        ]

        # 差评熔断告警池
        self.negative_alerts: List[Dict[str, Any]] = []

    def submit_csat_feedback(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        提交满意度评分并进行差评熔断研判
        """
        session_id = payload.get("session_id", f"SES-{uuid.uuid4().hex[:8]}")
        user_id = payload.get("user_id", "u1001")
        username = payload.get("username", "vip_player_88")
        agent_id = payload.get("agent_id", "CS-Agent-007")
        agent_name = payload.get("agent_name", "张晓明")
        rating = int(payload.get("rating", 5))  # 1 到 5 星
        tags = payload.get("tags", [])
        comment = payload.get("comment", "")
        channel = payload.get("channel", "WEB")

        is_negative = (rating <= 2)
        recall_ticket_id = None
        alert_info = None

        # 差评触发即时熔断
        if is_negative:
            recall_ticket_id = f"TK-RECALL-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            alert_info = {
                "alert_id": f"ALT-{uuid.uuid4().hex[:6]}",
                "severity": "P1_URGENT",
                "ticket_id": recall_ticket_id,
                "user_id": user_id,
                "username": username,
                "agent_id": agent_id,
                "rating": rating,
                "reason": f"客户提交 {rating} 星极低满意度评价: {comment or ', '.join(tags)}",
                "suggested_action": "指派班长席/客诉专员在 15 分钟内执行电话/即时通讯回访挽回",
                "status": "PENDING_RECALL",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            self.negative_alerts.insert(0, alert_info)

        record = {
            "id": f"CSAT-{uuid.uuid4().hex[:6]}",
            "session_id": session_id,
            "user_id": user_id,
            "username": username,
            "agent_id": agent_id,
            "agent_name": agent_name,
            "rating": rating,
            "dimension_tags": tags,
            "comment": comment,
            "channel": channel,
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "is_negative": is_negative,
            "recall_ticket_id": recall_ticket_id
        }
        self.feedback_records.insert(0, record)

        return {
            "status": "SUCCESS",
            "csat_id": record["id"],
            "rating": rating,
            "is_negative_circuit_broken": is_negative,
            "recall_ticket_id": recall_ticket_id,
            "alert": alert_info,
            "message": "感谢您的真诚反馈！" if not is_negative else "检测到服务不满意，系统已为您自动挂起高优先级主管关怀工单并跟进！"
        }

    def get_csat_metrics(self) -> Dict[str, Any]:
        """统计 CSAT 运营指标与好评率"""
        total = len(self.feedback_records)
        if total == 0:
            return {"total_feedbacks": 0, "avg_rating": 5.0, "satisfaction_rate_pct": 100.0}

        positive_count = sum(1 for r in self.feedback_records if r["rating"] >= 4)
        avg_rating = sum(r["rating"] for r in self.feedback_records) / total

        tag_distribution: Dict[str, int] = {}
        for r in self.feedback_records:
            for t in r.get("dimension_tags", []):
                tag_distribution[t] = tag_distribution.get(t, 0) + 1

        return {
            "total_feedbacks": total,
            "positive_count": positive_count,
            "negative_count": sum(1 for r in self.feedback_records if r["is_negative"]),
            "avg_rating": round(avg_rating, 2),
            "satisfaction_rate_pct": round(positive_count / total * 100, 1),
            "tag_distribution": tag_distribution,
            "recent_feedbacks": self.feedback_records[:10],
            "active_negative_alerts": self.negative_alerts[:5]
        }

csat_feedback_service = CSATFeedbackService()
