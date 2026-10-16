"""
CoreDesk 班长席主管监控协同中枢 (Supervisor Cockpit, Whisper & Barge-in)
提供管理层实时会话监控、内部密语指导 (Whisper)、会话强插接管 (Barge-in) 与打字实时预知
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import uuid

class SupervisorService:
    def __init__(self):
        # 内部密语与协同记录池 (仅坐席与主管可见，不对客户展示)
        self.whisper_notes: List[Dict[str, Any]] = [
            {
                "id": "WHP-101",
                "session_id": "SES-u1001",
                "user_id": "u1001",
                "supervisor_id": "SUP-01",
                "supervisor_name": "王主管 (班长席)",
                "target_agent_id": "CS-Agent-007",
                "content": "该用户今日第二次咨询提现打码量，注意耐心告知扣减优惠方案，勿起冲突！",
                "created_at": "2026-10-06T10:15:00Z"
            }
        ]

        # 强插接管审计记录
        self.barge_in_logs: List[Dict[str, Any]] = []

        # 实时打字预览缓存
        self.typing_previews: Dict[str, str] = {
            "u1001": "我刚刚按照要求打完流水了，现在能审核通过吗？"
        }

    def send_whisper_note(self, session_id: str, user_id: str, supervisor_id: str, supervisor_name: str, content: str) -> Dict[str, Any]:
        """
        班长席发送内部指导密语（客户完全不可见）
        """
        note = {
            "id": f"WHP-{uuid.uuid4().hex[:6]}",
            "session_id": session_id,
            "user_id": user_id,
            "supervisor_id": supervisor_id,
            "supervisor_name": supervisor_name,
            "content": content,
            "is_whisper": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        self.whisper_notes.insert(0, note)
        return {
            "status": "SENT",
            "whisper_id": note["id"],
            "note": note,
            "message": "内部密语已直达坐席工作台，客户侧已安全隔离"
        }

    def execute_barge_in(self, session_id: str, user_id: str, supervisor_id: str, supervisor_name: str, reason: str) -> Dict[str, Any]:
        """
        班长席强插接管会话：原坐席降为旁听，主管直接接管
        """
        log = {
            "id": f"BGI-{uuid.uuid4().hex[:6]}",
            "session_id": session_id,
            "user_id": user_id,
            "supervisor_id": supervisor_id,
            "supervisor_name": supervisor_name,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.barge_in_logs.insert(0, log)

        return {
            "status": "BARGE_IN_SUCCESS",
            "session_id": session_id,
            "new_handler": f"{supervisor_name} ({supervisor_id})",
            "reason": reason,
            "system_notice": f"【系统提示】班长席主管 {supervisor_name} 已接管此会话，转为专人高级跟进。",
            "logged_at": log["timestamp"]
        }

    def update_typing_preview(self, user_id: str, text: str) -> Dict[str, Any]:
        """更新客户实时打字中的内容（坐席侧毫秒级透视）"""
        self.typing_previews[user_id] = text
        return {"user_id": user_id, "preview_text": text}

    def get_typing_preview(self, user_id: str) -> Optional[str]:
        return self.typing_previews.get(user_id)

    def get_supervisor_cockpit(self) -> Dict[str, Any]:
        """获取班长席监控驾驶舱数据"""
        return {
            "active_monitored_sessions": 4,
            "crisis_alerts_count": 1,
            "whisper_notes_count": len(self.whisper_notes),
            "barge_in_count": len(self.barge_in_logs),
            "recent_whispers": self.whisper_notes[:5],
            "recent_takeovers": self.barge_in_logs[:5],
            "sla_health": {
                "avg_first_response_seconds": 1.8,
                "first_contact_resolution_pct": 84.8,
                "p0_escalation_pct": 1.2
            }
        }

supervisor_service = SupervisorService()
