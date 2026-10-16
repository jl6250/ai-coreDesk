import time
from typing import Dict, Any, Optional

class RiskDecisionEngine:
    """
    ⚡ Phase 2: 风险分级评估与自主应答判定引擎
    根据用户资产风险、意图置信度、账务流水健康度与情绪危机指数，
    决策是否放行 Auto-Pilot 自主应答，或智能分流升级为人工专员工单。
    """

    def evaluate_risk_and_action(
        self,
        user_id: str,
        jev_result: Dict[str, Any],
        sentiment_result: Dict[str, Any],
        billing_snapshot: Optional[Dict[str, Any]] = None,
        system_mode: str = "copilot"  # "copilot" or "auto_pilot"
    ) -> Dict[str, Any]:
        start = time.perf_counter()

        # 1. 安全阻断优先判定
        if not jev_result.get("allowed", True):
            return {
                "risk_level": "CRITICAL",
                "risk_score": 100,
                "action": "SECURITY_BLOCK",
                "can_auto_reply": False,
                "reason": "JEV前置网关拦截违规指令",
                "escalate_group": "RISK_COMPLIANCE",
                "auto_ticket_required": False,
                "diagnostic_card": {
                    "alert_title": "🚨 安全防护拦截",
                    "details": jev_result.get("message", "检测到注入攻击"),
                    "suggested_action": "系统自动阻断并记录审计日志"
                },
                "latency_ms": round((time.perf_counter() - start) * 1000, 2)
            }

        # 2. 情绪危机判定
        urgency = sentiment_result.get("urgency", "P2_NORMAL")
        if urgency == "P0_CRITICAL":
            return {
                "risk_level": "HIGH",
                "risk_score": 85,
                "action": "ESCALATE_TRANSFER",
                "can_auto_reply": False,
                "reason": "检测到客户严重情绪危机或维权意向",
                "escalate_group": "VIP_CONCIERGE",
                "auto_ticket_required": True,
                "diagnostic_card": {
                    "alert_title": "🔥 P0 级严重客诉警报",
                    "details": f"会员情绪指数超标 ({sentiment_result.get('sentiment_score')}分)，命中信号: {sentiment_result.get('matched_signals')}",
                    "suggested_action": "立即安抚并流转至大客户专属经理优先接入"
                },
                "latency_ms": round((time.perf_counter() - start) * 1000, 2)
            }

        # 3. 账务流水卡单与差额判定
        intent = jev_result.get("intent", "GENERAL_CONSULTATION")
        if intent == "BILLING_ORDER_QUERY" and billing_snapshot:
            turnover = billing_snapshot.get("turnover_status", {})
            orders = billing_snapshot.get("recent_orders", [])
            pending_orders = [o for o in orders if o.get("status") in ["PENDING_AUDIT", "BLOCKCHAIN_CONFIRMING"]]

            # 流水差额较大或者提现卡单
            if not turnover.get("is_satisfied", True):
                diff = turnover.get("required", 0) - turnover.get("current", 0)
                return {
                    "risk_level": "HIGH",
                    "risk_score": 75,
                    "action": "COPILOT_DRAFT",  # 账务不满足不可直接自主断言出款，需要审核草稿或流转
                    "can_auto_reply": False,
                    "reason": f"提现流水未满，差额 ¥{diff:,.2f}",
                    "escalate_group": "FINANCIAL_AUDIT",
                    "auto_ticket_required": True,
                    "diagnostic_card": {
                        "alert_title": "⚠️ 提现打码流水差额未达标",
                        "details": f"当前有效打码 ¥{turnover.get('current'):,.2f} / 要求打码 ¥{turnover.get('required'):,.2f}，缺口 ¥{diff:,.2f}",
                        "suggested_action": "由坐席或财务专员引导会员补足有效投注流水"
                    },
                    "latency_ms": round((time.perf_counter() - start) * 1000, 2)
                }

            # 正常账务查询（已满足流水，或一般进度查询）
            if pending_orders:
                risk_level = "MEDIUM"
                risk_score = 45
            else:
                risk_level = "LOW"
                risk_score = 20
        else:
            # FAQ 规则查询
            risk_level = "LOW"
            risk_score = 10

        # 4. 自主应答放行判定 (Auto-Pilot Gating)
        # 满足条件：
        # - 系统开启了 auto_pilot 模式
        # - 风险等级为 LOW 或 MEDIUM
        # - 意图置信度 >= 0.85
        # - 情绪评级不是 P0 危机
        confidence = jev_result.get("confidence", 0.9)
        can_auto_reply = (
            system_mode == "auto_pilot" and
            risk_level in ["LOW", "MEDIUM"] and
            confidence >= 0.85 and
            urgency != "P0_CRITICAL"
        )

        final_action = "AUTO_PILOT_REPLY" if can_auto_reply else "COPILOT_DRAFT"

        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "action": final_action,
            "can_auto_reply": can_auto_reply,
            "reason": "标准化低风险咨询，符合自主应答放行准则" if can_auto_reply else "处于坐席辅助模式或需人工二次复核",
            "escalate_group": None,
            "auto_ticket_required": False,
            "diagnostic_card": {
                "alert_title": "✅ 业务规则检索达标",
                "details": f"意图识别置信度 {int(confidence * 100)}%，风险分值 {risk_score}，符合质检安全标准",
                "suggested_action": "AI 自动化应答或由坐席一键采纳发送"
            },
            "latency_ms": round((time.perf_counter() - start) * 1000, 2)
        }

risk_engine = RiskDecisionEngine()
