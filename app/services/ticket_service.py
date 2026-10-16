import time
from typing import Dict, Any, List, Optional

class TicketLifecycleService:
    """
    ⚡ Phase 2: 账务客诉工单全生命周期流转服务
    支持异常追查工单创建、跨组协同流转、状态机核销与操作审计流
    """

    def __init__(self):
        # 预设种子工单数据
        self.tickets: List[Dict[str, Any]] = [
            {
                "ticket_id": "TK20261005001",
                "user_id": "u1001",
                "username": "vip_player_88",
                "order_id": "TX20261005001",
                "category": "WITHDRAWAL_TURNOVER",
                "title": "提现2000元流水核验差额工单",
                "priority": "P1",
                "status": "NEED_TURNOVER",
                "status_label": "需补足流水",
                "status_color": "amber",
                "assigned_to": "Felix (财务对账组)",
                "created_at": "2026-10-05 21:42:00",
                "updated_at": "2026-10-05 21:45:10",
                "details": "会员申请提现2000元，后台计算打码流水45000/50000，尚差5000有效流水未满足1.0倍出款门槛。",
                "logs": [
                    {"time": "2026-10-05 21:42:00", "operator": "AI_SYSTEM", "action": "自动触发创建追查工单"},
                    {"time": "2026-10-05 21:45:10", "operator": "Felix", "action": "核验流水缺口确认，状态流转为 [需补足流水]"}
                ]
            },
            {
                "ticket_id": "TK20261005002",
                "user_id": "u1002",
                "username": "lucky_tiger_99",
                "order_id": "CZ20261005105",
                "category": "BLOCKCHAIN_CONFIRM",
                "title": "TRC20 充值 1000 USDT 链上区块确认追踪",
                "priority": "P2",
                "status": "IN_PROGRESS",
                "status_label": "协同确认中",
                "status_color": "blue",
                "assigned_to": "AI 自动调度引擎",
                "created_at": "2026-10-05 22:16:00",
                "updated_at": "2026-10-05 22:18:22",
                "details": "链上哈希 4f7a9b...c83e12 已达8个区块确认，等待达到12个主网确认自动上分。",
                "logs": [
                    {"time": "2026-10-05 22:16:00", "operator": "AI_SYSTEM", "action": "识别充值链上打包状态，创建自动化监控工单"}
                ]
            }
        ]

    def list_tickets(self, user_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        results = self.tickets
        if user_id:
            results = [t for t in results if t["user_id"] == user_id]
        if status and status != "all":
            results = [t for t in results if t["status"] == status]
        return results

    def get_ticket(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        for t in self.tickets:
            if t["ticket_id"] == ticket_id:
                return t
        return None

    def create_ticket(
        self,
        user_id: str,
        username: str,
        category: str,
        title: str,
        details: str,
        priority: str = "P1",
        order_id: Optional[str] = None,
        assigned_to: str = "财务对账组"
    ) -> Dict[str, Any]:
        new_id = f"TK20261006{str(len(self.tickets) + 1).padStart(3, '0') if hasattr(str, 'padStart') else str(len(self.tickets) + 1).zfill(3)}"
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")

        status_meta = {
            "WITHDRAWAL_TURNOVER": ("NEED_TURNOVER", "需补足流水", "amber"),
            "BLOCKCHAIN_CONFIRM": ("IN_PROGRESS", "协同确认中", "blue"),
            "CRISIS_COMPLAINT": ("PENDING_REVIEW", "待主管复核", "rose"),
            "GENERAL": ("IN_PROGRESS", "处理中", "blue")
        }
        status, label, color = status_meta.get(category, ("IN_PROGRESS", "处理中", "blue"))

        ticket = {
            "ticket_id": new_id,
            "user_id": user_id,
            "username": username,
            "order_id": order_id or "N/A",
            "category": category,
            "title": title,
            "priority": priority,
            "status": status,
            "status_label": label,
            "status_color": color,
            "assigned_to": assigned_to,
            "created_at": now_str,
            "updated_at": now_str,
            "details": details,
            "logs": [
                {"time": now_str, "operator": "AI_SYSTEM", "action": f"工单创建成功，指派至【{assigned_to}】"}
            ]
        }
        self.tickets.insert(0, ticket)
        return ticket

    def update_ticket_status(
        self,
        ticket_id: str,
        new_status: str,
        operator: str = "Agent",
        note: str = ""
    ) -> Optional[Dict[str, Any]]:
        ticket = self.get_ticket(ticket_id)
        if not ticket:
            return None

        labels = {
            "PENDING_REVIEW": ("待核查", "amber"),
            "IN_PROGRESS": ("处理中", "blue"),
            "NEED_TURNOVER": ("需补足流水", "amber"),
            "PAYOUT_APPROVED": ("审核通过已出款", "emerald"),
            "REJECTED": ("已驳回", "rose"),
            "RESOLVED": ("已办结归档", "emerald")
        }
        label, color = labels.get(new_status, ("未知状态", "slate"))

        now_str = time.strftime("%Y-%m-%d %H:%M:%S")
        ticket["status"] = new_status
        ticket["status_label"] = label
        ticket["status_color"] = color
        ticket["updated_at"] = now_str
        
        log_entry = {
            "time": now_str,
            "operator": operator,
            "action": f"工单状态变更 -> [{label}]" + (f" (附言: {note})" if note else "")
        }
        ticket["logs"].append(log_entry)
        return ticket

ticket_service = TicketLifecycleService()
