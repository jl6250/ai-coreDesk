import time
from typing import Dict, Any, Optional, List

class ReadOnlyBillingGateway:
    """
    业务 API 网关 (只读流水的只读代理)
    架构约束:
    1. 保持绝对'只读'安全边界，不直连主交易写库，不触发行锁
    2. 模拟毫秒级只读账务流水与充提状态查询
    """
    def __init__(self):
        # 模拟 CQRS 只读投影缓存数据 (Redis / Read Projection)
        self._user_accounts: Dict[str, Dict[str, Any]] = {
            "u1001": {
                "user_id": "u1001",
                "username": "vip_player_88",
                "vip_level": "VIP 3",
                "main_balance": 18560.50,
                "frozen_balance": 2000.00,
                "current_turnover": 45000.00,      # 当前已完成有效流水
                "required_turnover": 50000.00,     # 要求流水
                "turnover_satisfied": False,       # 流水未满足提现条件
                "phone": "13800138888",
                "bank_card": "62220210001889988",
                "recent_orders": [
                    {
                        "order_id": "TX20261005001",
                        "type": "WITHDRAWAL",
                        "amount": 2000.00,
                        "status": "PENDING_AUDIT",  # 审核中
                        "status_desc": "风控流水校验中 (还差 5000 流水)",
                        "created_at": "2026-10-05 21:40:12",
                        "channel": "银行卡出款"
                    },
                    {
                        "order_id": "CZ20261005099",
                        "type": "DEPOSIT",
                        "amount": 5000.00,
                        "status": "SUCCESS",
                        "status_desc": "充值成功已入账",
                        "created_at": "2026-10-05 18:20:00",
                        "channel": "USDT-TRC20"
                    }
                ]
            },
            "u1002": {
                "user_id": "u1002",
                "username": "lucky_tiger_99",
                "vip_level": "VIP 1",
                "main_balance": 350.00,
                "frozen_balance": 0.00,
                "current_turnover": 10000.00,
                "required_turnover": 1000.00,
                "turnover_satisfied": True,
                "phone": "13911122233",
                "bank_card": "6214830112345678",
                "recent_orders": [
                    {
                        "order_id": "CZ20261005105",
                        "type": "DEPOSIT",
                        "amount": 1000.00,
                        "status": "BLOCKCHAIN_CONFIRMING", # 链上确认中
                        "status_desc": "网络区块确认中 (已完成 8/12 确认)",
                        "created_at": "2026-10-05 22:20:10",
                        "channel": "USDT-TRC20"
                    }
                ]
            }
        }

    def get_user_billing_snapshot(self, user_id: str) -> Optional[Dict[str, Any]]:
        """只读获取用户账户及最近充提流水镜像 (模拟 < 5ms 查询)"""
        start = time.perf_counter()
        user_data = self._user_accounts.get(user_id)
        latency_ms = (time.perf_counter() - start) * 1000
        
        if not user_data:
            return {
                "found": False,
                "user_id": user_id,
                "query_latency_ms": round(latency_ms, 2)
            }
            
        return {
            "found": True,
            "user_id": user_data["user_id"],
            "username": user_data["username"],
            "vip_level": user_data["vip_level"],
            "main_balance": user_data["main_balance"],
            "frozen_balance": user_data["frozen_balance"],
            "turnover_status": {
                "current": user_data["current_turnover"],
                "required": user_data["required_turnover"],
                "diff": max(0.0, user_data["required_turnover"] - user_data["current_turnover"]),
                "is_satisfied": user_data["turnover_satisfied"]
            },
            "recent_orders": user_data["recent_orders"],
            "query_latency_ms": round(latency_ms, 2)
        }

billing_gateway = ReadOnlyBillingGateway()
