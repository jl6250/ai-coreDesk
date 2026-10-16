"""
CoreDesk ACD (Automatic Call/Chat Distribution) 智能排队调度与技能组路由引擎
支持基于语种、业务线意图、VIP 等级抢占与坐席负荷平衡的企业级调度
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import uuid

class ACDRoutingEngine:
    def __init__(self):
        # 坐席技能组注册表
        self.skill_groups = {
            "finance_desk": {
                "id": "finance_desk",
                "name": "财务出入金专席组",
                "skills": ["finance", "turnover", "deposit", "withdraw"],
                "desc": "专门处理大额充提、打码量对账、掉单核验与流水冲正"
            },
            "vip_support": {
                "id": "vip_support",
                "name": "VIP 尊享管家组",
                "skills": ["vip", "high_value", "care"],
                "desc": "专属保障 VIP 3 及以上高净值用户，享有绝对优先接待权"
            },
            "sea_multilang_desk": {
                "id": "sea_multilang_desk",
                "name": "东南亚多语种专席组",
                "skills": ["vi", "th", "multilang"],
                "desc": "覆盖越南语 (Tiếng Việt)、泰语 (ภาษาไทย) 母语坐席"
            },
            "general_desk": {
                "id": "general_desk",
                "name": "综合业务与技术组",
                "skills": ["faq", "general", "rules", "tech"],
                "desc": "日常业务咨询、活动规则与通用客户接待"
            }
        }

        # 坐席人员池 (实时状态与能力矩阵)
        self.agent_pool: Dict[str, Dict[str, Any]] = {
            "CS-Agent-007": {
                "id": "CS-Agent-007",
                "name": "张晓明",
                "role": "SENIOR_AGENT",
                "skills": ["zh", "finance", "turnover", "vip", "general"],
                "status": "ONLINE",  # ONLINE, BUSY, OFFLINE
                "max_concurrency": 8,
                "active_chats": ["u1001"],
                "group_id": "finance_desk",
                "csat_score": 4.92,
                "today_handled": 42
            },
            "CS-Agent-012": {
                "id": "CS-Agent-012",
                "name": "阮氏梅 (Mai Nguyen)",
                "role": "SPECIALIST",
                "skills": ["vi", "en", "multilang", "finance"],
                "status": "ONLINE",
                "max_concurrency": 6,
                "active_chats": [],
                "group_id": "sea_multilang_desk",
                "csat_score": 4.88,
                "today_handled": 35
            },
            "CS-Agent-018": {
                "id": "CS-Agent-018",
                "name": "颂猜 (Somchai)",
                "role": "SPECIALIST",
                "skills": ["th", "en", "multilang", "general"],
                "status": "ONLINE",
                "max_concurrency": 6,
                "active_chats": [],
                "group_id": "sea_multilang_desk",
                "csat_score": 4.85,
                "today_handled": 29
            },
            "CS-Agent-001": {
                "id": "CS-Agent-001",
                "name": "林婉儿",
                "role": "VIP_MANAGER",
                "skills": ["vip", "finance", "care", "zh", "en"],
                "status": "ONLINE",
                "max_concurrency": 5,
                "active_chats": ["u1002"],
                "group_id": "vip_support",
                "csat_score": 4.98,
                "today_handled": 18
            }
        }

        # 排队队列 (等待分配中的会话)
        self.waiting_queue: List[Dict[str, Any]] = []

    def route_conversation(self, customer_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        核心智能路由算法：综合语种、意图、VIP 等级与负荷均衡决定派单目标
        """
        user_id = customer_payload.get("user_id", f"anon_{uuid.uuid4().hex[:6]}")
        username = customer_payload.get("username", "Guest")
        vip_level = int(customer_payload.get("vip_level", 1))
        language = customer_payload.get("language", "zh").lower()
        intent = customer_payload.get("intent", "GENERAL_FAQ")
        channel = customer_payload.get("channel", "WEB")

        # 1. 目标技能组判定
        target_group = "general_desk"
        match_reasons = []

        # (a) 语种优先策略：若为越语/泰语，优先匹配多语种技能组
        if language in ["vi", "th"]:
            target_group = "sea_multilang_desk"
            match_reasons.append(f"命中母语直连路由: {language.upper()}")
        # (b) VIP 尊享通道：VIP 3 及以上命中尊享组
        elif vip_level >= 3:
            target_group = "vip_support"
            match_reasons.append(f"命中高净值 VIP {vip_level} 绿色通道")
        # (c) 意图专席：出入金对账核验
        elif intent in ["BILLING_ORDER_QUERY", "DEPOSIT_TIMEOUT", "WITHDRAWAL_TURNOVER"]:
            target_group = "finance_desk"
            match_reasons.append(f"命中财务专业核验组 (意图: {intent})")
        else:
            match_reasons.append("常规综合咨询路由")

        # 2. 候选坐席检索 (技能匹配且在线)
        candidates = []
        for agent_id, agent in self.agent_pool.items():
            if agent["status"] != "ONLINE":
                continue
            
            # 技能覆盖检查
            has_lang = (language in agent["skills"]) or (language in ["vi", "th"] and "multilang" in agent["skills"])
            is_in_group = (agent["group_id"] == target_group) or ("vip" in agent["skills"] and vip_level >= 3)
            
            if has_lang or is_in_group:
                current_load = len(agent["active_chats"])
                available_capacity = agent["max_concurrency"] - current_load
                if available_capacity > 0:
                    candidates.append({
                        "agent": agent,
                        "available_capacity": available_capacity,
                        "current_load": current_load,
                        "csat_score": agent["csat_score"]
                    })

        # 3. 排序策略：优先可用并发容量最大、CSAT 得分最高者
        if candidates:
            # VIP 客户优先匹配 CSAT 评分最高的坐席
            if vip_level >= 3:
                candidates.sort(key=lambda x: (-x["agent"]["csat_score"], x["current_load"]))
            else:
                candidates.sort(key=lambda x: (-x["available_capacity"], x["current_load"]))

            best_match = candidates[0]["agent"]
            best_match["active_chats"].append(user_id)

            return {
                "status": "ASSIGNED",
                "assigned_agent_id": best_match["id"],
                "assigned_agent_name": best_match["name"],
                "target_group": target_group,
                "group_name": self.skill_groups[target_group]["name"],
                "match_reasons": match_reasons,
                "queue_position": 0,
                "estimated_wait_seconds": 0,
                "assigned_at": datetime.now(timezone.utc).isoformat()
            }
        else:
            # 4. 坐席全忙，进入排队队列 (VIP 拥有抢占排队权)
            queue_item = {
                "user_id": user_id,
                "username": username,
                "vip_level": vip_level,
                "language": language,
                "intent": intent,
                "channel": channel,
                "target_group": target_group,
                "entered_at": datetime.now(timezone.utc).isoformat()
            }
            
            # VIP 3+ 优先插入到普通用户前方
            if vip_level >= 3:
                insert_idx = 0
                for idx, q in enumerate(self.waiting_queue):
                    if q["vip_level"] < vip_level:
                        insert_idx = idx
                        break
                self.waiting_queue.insert(insert_idx, queue_item)
                queue_pos = insert_idx + 1
            else:
                self.waiting_queue.append(queue_item)
                queue_pos = len(self.waiting_queue)

            return {
                "status": "QUEUED",
                "assigned_agent_id": None,
                "assigned_agent_name": None,
                "target_group": target_group,
                "group_name": self.skill_groups[target_group]["name"],
                "match_reasons": match_reasons + ["当前目标技能组全量满载，进入优先等候队列"],
                "queue_position": queue_pos,
                "estimated_wait_seconds": queue_pos * 25,
                "assigned_at": None
            }

    def release_conversation(self, agent_id: str, user_id: str) -> Dict[str, Any]:
        """坐席会话结束，释放并发容量，并自动拉取排队队列中的下一位客户"""
        agent = self.agent_pool.get(agent_id)
        if agent and user_id in agent["active_chats"]:
            agent["active_chats"].remove(user_id)
            agent["today_handled"] += 1

        # 若队列中存在排队用户，立即触发分配
        next_customer = None
        if self.waiting_queue:
            next_customer = self.waiting_queue.pop(0)
            assign_result = self.route_conversation(next_customer)
            return {
                "freed_user_id": user_id,
                "agent_id": agent_id,
                "agent_remaining_load": len(agent["active_chats"]) if agent else 0,
                "next_routed_customer": assign_result
            }

        return {
            "freed_user_id": user_id,
            "agent_id": agent_id,
            "agent_remaining_load": len(agent["active_chats"]) if agent else 0,
            "next_routed_customer": None
        }

    def get_acd_overview(self) -> Dict[str, Any]:
        """获取整个客服中心路由引擎的实时监控数据"""
        total_capacity = sum(a["max_concurrency"] for a in self.agent_pool.values())
        active_load = sum(len(a["active_chats"]) for a in self.agent_pool.values())
        online_agents = sum(1 for a in self.agent_pool.values() if a["status"] == "ONLINE")

        return {
            "online_agents_count": online_agents,
            "total_agents_count": len(self.agent_pool),
            "total_capacity": total_capacity,
            "active_chats_count": active_load,
            "system_load_pct": round((active_load / total_capacity * 100) if total_capacity else 0, 1),
            "waiting_queue_count": len(self.waiting_queue),
            "waiting_queue_preview": self.waiting_queue[:5],
            "skill_groups": self.skill_groups,
            "agents": list(self.agent_pool.values())
        }

# 全局单例
acd_routing_engine = ACDRoutingEngine()
