import time
import json
import asyncio
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.services.jev_gateway import jev_gateway
from app.services.mock_billing import billing_gateway
from app.services.rag_engine import rag_engine
from app.services.llm_engine import llm_engine
from app.services.jev_post_guard import jev_post_guard
from app.services.sentiment_analyzer import sentiment_analyzer
from app.services.risk_engine import risk_engine
from app.services.ticket_service import ticket_service
from app.services.action_agent import action_agent
from app.services.qa_analytics_engine import qa_analytics_engine
from app.services.knowledge_flywheel import knowledge_flywheel
from app.services.im_channel_gateway import im_channel_gateway
from app.services.acd_routing_engine import acd_routing_engine
from app.services.csat_feedback_service import csat_feedback_service
from app.services.supervisor_service import supervisor_service
from app.services.customer_journey_service import customer_journey_service

app = FastAPI(
    title="智服云 CoreDesk - 全渠道智能客服中台 (Phase 1 ~ Phase 5 完整落地)",
    description="支持 JEV 前置网关、CQRS 只读直连、Auto-Pilot 分流、Telegram/WhatsApp/LINE 全渠道接入、Action Agent 业务闭环、100% 智能质检、运营 BI 与知识飞轮"
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 系统运行模式状态: "copilot" (坐席辅助草稿) 或 "auto_pilot" (低风险自主应答)
system_runtime_state = {
    "mode": "copilot",  # 默认在进入P2时可由坐席工作台或管理端自由切换
    "auto_pilot_rate": 73.8,  # 自主应答率指标
    "confidence_threshold": 0.85
}

class InboundChatRequest(BaseModel):
    user_id: str = "u1001"
    query: str
    auth_token: str = "valid_token"
    lang: Optional[str] = None  # zh, en, vi, th
    mode: Optional[str] = None  # 可临时覆盖请求模式

class AgentActionRequest(BaseModel):
    user_id: str
    final_reply: str
    original_draft: str
    is_modified: bool
    user_query: Optional[str] = None
    lang: Optional[str] = "zh"

class ModeToggleRequest(BaseModel):
    mode: str  # "copilot" or "auto_pilot"

class CreateTicketRequest(BaseModel):
    user_id: str
    username: str
    category: str
    title: str
    details: str
    priority: str = "P1"
    order_id: Optional[str] = None
    assigned_to: str = "财务对账组"

class UpdateTicketStatusRequest(BaseModel):
    ticket_id: str
    new_status: str
    operator: str = "Agent"
    note: str = ""

# ⚡ Phase 3 Request Models
class ReconcileDepositRequest(BaseModel):
    user_id: str = "u1001"
    order_id: str = "CZ20261005002"
    tx_hash: Optional[str] = None
    operator: str = "AI_AGENT"

class TurnoverWaiverRequest(BaseModel):
    user_id: str = "u1001"
    order_id: str = "TX20261005001"
    deduct_bonus: float = 500.0
    operator: str = "坐席张晓明 (CS-007)"

class VipRetentionRequest(BaseModel):
    user_id: str = "u1001"
    urgency: str = "P0_CRITICAL"
    custom_amount: Optional[float] = None
    operator: str = "AI_RETENTION_AGENT"

# ⚡ Phase 4 Request Models
class AuditSessionRequest(BaseModel):
    session_id: str
    user_id: str
    messages: List[Dict[str, str]]
    agent_id: str = "CS-007 (张晓明)"

class CreateBroadcastRequest(BaseModel):
    title: str
    content: str
    level: str = "WARNING"

# ⚡ Phase 5 Request Models
class AgentFeedbackRequest(BaseModel):
    user_query: str
    original_draft: str
    final_agent_text: str
    lang: str = "zh"
    agent_id: str = "CS-007 (张晓明)"

class ApproveDistillationRequest(BaseModel):
    candidate_id: str

class ShadowEvalRequest(BaseModel):
    test_query: str = "提现需要完成多少倍打码流水？"
    lang: str = "zh"

@app.get("/", response_class=HTMLResponse)
async def serve_copilot_workspace():
    with open("app/static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/manual", response_class=HTMLResponse)
@app.get("/guide", response_class=HTMLResponse)
async def serve_deployment_user_manual():
    with open("CoreDesk_Deploy_and_User_Manual.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/architecture", response_class=HTMLResponse)
@app.get("/design", response_class=HTMLResponse)
async def serve_architecture_specification():
    with open("CoreDesk_Architecture_and_Design_Specification.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/api/system/mode")
async def get_system_mode():
    return system_runtime_state

@app.post("/api/system/mode")
async def toggle_system_mode(req: ModeToggleRequest):
    if req.mode in ["copilot", "auto_pilot"]:
        system_runtime_state["mode"] = req.mode
    return {
        "status": "SUCCESS",
        "current_mode": system_runtime_state["mode"],
        "message": f"系统运行模式已切换为: {'智能自主应答 (Auto-Pilot)' if system_runtime_state['mode'] == 'auto_pilot' else '坐席审核草稿 (Copilot)'}"
    }

@app.get("/api/user/billing-snapshot")
async def get_user_billing(user_id: str = "u1001"):
    return billing_gateway.get_user_billing_snapshot(user_id)

@app.post("/api/chat/process-v2")
async def process_chat_v2(req: InboundChatRequest):
    """
    ⚡ Phase 2 核心调度链路:
    1. JEV 前置安全网关 (意图识别 / 鉴权 / 防注入)
    2. 多语言情绪分析与危机预警研判 (Sentiment & Crisis Analyzer)
    3. CQRS 账务中台只读直连 (Billing Gateway)
    4. RAG 多语言向量检索
    5. 风险分级与自主应答判定引擎 (Risk & Action Engine)
    6. LLM 事实翻译生成
    7. JEV 后置合规质检与敏感脱敏 (Post Guard)
    8. 决策流转: AUTO_PILOT_REPLY / COPILOT_DRAFT / ESCALATE_TRANSFER
    """
    total_start = time.perf_counter()
    active_mode = req.mode or system_runtime_state["mode"]

    # 1. JEV 前置安全网关
    jev_result = jev_gateway.process_incoming_request(
        user_id=req.user_id,
        query=req.query,
        auth_token=req.auth_token,
        target_lang=req.lang
    )
    detected_lang = jev_result.get("lang", req.lang or "zh")

    # 2. 跨语言情绪与危机研判
    sentiment_result = sentiment_analyzer.analyze(query=req.query, lang=detected_lang)

    # 如果被 JEV 前置安全网关阻断
    if not jev_result["allowed"]:
        total_latency = (time.perf_counter() - total_start) * 1000
        return {
            "status": "BLOCKED_BY_JEV",
            "mode": active_mode,
            "action": "SECURITY_BLOCK",
            "can_auto_reply": False,
            "is_auto_replied": False,
            "lang": detected_lang,
            "jev_gateway": jev_result,
            "sentiment": sentiment_result,
            "risk": {
                "risk_level": "CRITICAL",
                "risk_score": 100,
                "reason": jev_result.get("message", "安全拦截"),
                "diagnostic_card": {
                    "alert_title": "🚨 安全防护拦截",
                    "details": jev_result.get("message", "检测到注入攻击"),
                    "suggested_action": "系统自动阻断并记录审计日志"
                }
            },
            "billing_snapshot": None,
            "rag_context": None,
            "draft": jev_result["message"],
            "post_guard": {
                "passed": True,
                "sanitized_text": jev_result["message"],
                "risk_tags": ["前置网关直接阻断"]
            },
            "total_latency_ms": round(total_latency, 2)
        }

    # 3. 业务 API 只读网关
    billing_data = None
    if jev_result.get("need_billing_api"):
        billing_data = billing_gateway.get_user_billing_snapshot(req.user_id)

    # 4. RAG 多语言业务知识检索
    rag_data = rag_engine.retrieve_context(req.query, top_k=2, lang=detected_lang)

    # 5. 风险分级与决策引擎
    risk_eval = risk_engine.evaluate_risk_and_action(
        user_id=req.user_id,
        jev_result=jev_result,
        sentiment_result=sentiment_result,
        billing_snapshot=billing_data,
        system_mode=active_mode
    )

    # 6. LLM 事实生成引擎
    raw_draft = await llm_engine.generate_draft_response(
        user_query=req.query,
        user_info=billing_data,
        rag_context=rag_data["context_text"],
        lang=detected_lang
    )

    # 7. JEV 后置合规质检
    guard_result = jev_post_guard.inspect_and_sanitize(raw_draft)

    # 如果需要自动创建追查工单
    auto_ticket = None
    if risk_eval.get("auto_ticket_required") and billing_data:
        username = billing_data.get("username", req.user_id)
        auto_ticket = ticket_service.create_ticket(
            user_id=req.user_id,
            username=username,
            category="WITHDRAWAL_TURNOVER" if "提现" in req.query or "withdraw" in req.query.lower() else "GENERAL",
            title=f"系统自动创建异常排查工单: {req.query[:25]}...",
            details=f"用户提问: {req.query}。\n风控诊断: {risk_eval['reason']}",
            priority="P0" if sentiment_result.get("urgency") == "P0_CRITICAL" else "P1",
            assigned_to=risk_eval.get("escalate_group") or "财务对账组"
        )

    total_latency = (time.perf_counter() - total_start) * 1000

    return {
        "status": "SUCCESS",
        "mode": active_mode,
        "action": risk_eval["action"],
        "can_auto_reply": risk_eval["can_auto_reply"],
        "is_auto_replied": (risk_eval["action"] == "AUTO_PILOT_REPLY"),
        "lang": detected_lang,
        "jev_gateway": jev_result,
        "sentiment": sentiment_result,
        "risk": risk_eval,
        "billing_snapshot": billing_data,
        "rag_context": rag_data,
        "draft": guard_result["sanitized_text"],
        "raw_draft": raw_draft,
        "post_guard": guard_result,
        "auto_ticket": auto_ticket,
        "total_latency_ms": round(total_latency, 2)
    }

# 保持与 Phase 1 接口完全兼容
@app.post("/api/chat/analyze-and-draft")
async def analyze_and_generate_draft(req: InboundChatRequest):
    return await process_chat_v2(req)

@app.post("/api/agent/send")
async def agent_confirm_and_send(req: AgentActionRequest):
    # P5: 自动捕获坐席对草稿的修改与知识沉淀
    feedback_candidate = None
    if req.is_modified and req.original_draft and req.final_reply:
        feedback_candidate = knowledge_flywheel.record_agent_feedback(
            user_query=req.user_query or "提现与流水业务咨询",
            original_draft=req.original_draft,
            final_agent_text=req.final_reply,
            lang=req.lang or "zh"
        )
    return {
        "status": "SENT_TO_USER",
        "user_id": req.user_id,
        "sent_content": req.final_reply,
        "is_ai_draft_adopted": not req.is_modified,
        "feedback_distillation": feedback_candidate,
        "audit_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

# 🎫 工单中心 API
@app.get("/api/tickets/list")
async def get_tickets(user_id: Optional[str] = None, status: Optional[str] = "all"):
    return {
        "status": "SUCCESS",
        "tickets": ticket_service.list_tickets(user_id=user_id, status=status)
    }

@app.post("/api/tickets/create")
async def create_new_ticket(req: CreateTicketRequest):
    ticket = ticket_service.create_ticket(
        user_id=req.user_id,
        username=req.username,
        category=req.category,
        title=req.title,
        details=req.details,
        priority=req.priority,
        order_id=req.order_id,
        assigned_to=req.assigned_to
    )
    return {
        "status": "SUCCESS",
        "ticket": ticket
    }

@app.post("/api/tickets/update")
async def update_ticket(req: UpdateTicketStatusRequest):
    ticket = ticket_service.update_ticket_status(
        ticket_id=req.ticket_id,
        new_status=req.new_status,
        operator=req.operator,
        note=req.note
    )
    if not ticket:
        return {"status": "ERROR", "message": f"工单 {req.ticket_id} 不存在"}
    return {
        "status": "SUCCESS",
        "ticket": ticket
    }

# ==============================================================================
# ⚡ Phase 3: Action Agent 业务闭环与自主执行 API
# ==============================================================================
@app.post("/api/agent/reconcile-deposit")
async def reconcile_deposit(req: ReconcileDepositRequest):
    """充值掉单智能核验与安全补单闭环"""
    result = action_agent.reconcile_and_credit_deposit(
        user_id=req.user_id,
        order_id=req.order_id,
        tx_hash=req.tx_hash,
        operator=req.operator
    )
    return result

@app.post("/api/agent/turnover-waiver-calc")
async def calc_turnover_waiver(req: TurnoverWaiverRequest):
    """提现流水优惠扣除与冲正放行试算"""
    result = action_agent.calculate_turnover_waiver(
        user_id=req.user_id,
        order_id=req.order_id,
        operator=req.operator
    )
    return {
        "status": "SUCCESS",
        "calc": result
    }

@app.post("/api/agent/turnover-waiver-exec")
async def exec_turnover_waiver(req: TurnoverWaiverRequest):
    """执行优惠扣减并放行提现流水冲正"""
    result = action_agent.execute_turnover_waiver(
        user_id=req.user_id,
        order_id=req.order_id,
        deduct_bonus=req.deduct_bonus,
        operator=req.operator
    )
    return result

@app.post("/api/agent/vip-retention")
async def vip_retention_care(req: VipRetentionRequest):
    """VIP 高净值客诉流失挽留精准权益派发"""
    result = action_agent.dispatch_vip_retention_care(
        user_id=req.user_id,
        urgency=req.urgency,
        custom_amount=req.custom_amount,
        operator=req.operator
    )
    return result

@app.get("/api/agent/anti-fraud-check")
async def check_anti_fraud(user_id: str = "u1001", ip: str = "183.14.28.10"):
    """黑灰产多账号作弊对抗风险检测"""
    result = action_agent.check_anti_fraud_risk(user_id=user_id, ip_address=ip)
    return {
        "status": "SUCCESS",
        "fraud_check": result
    }

@app.get("/api/agent/action-logs")
async def get_action_audit_logs():
    """获取所有智能动作执行审计流水"""
    return {
        "status": "SUCCESS",
        "logs": action_agent.get_action_audit_logs()
    }

# ==============================================================================
# ⚡ Phase 4: 全量智能质检 (Auto QA)、深度运营 BI 与主动式预测服务 API
# ==============================================================================
@app.post("/api/qa/audit-session")
async def audit_chat_session(req: AuditSessionRequest):
    """100% 全量会话自动多维智能质检评估"""
    res = qa_analytics_engine.audit_session(
        session_id=req.session_id,
        user_id=req.user_id,
        messages=req.messages,
        agent_id=req.agent_id
    )
    return res

@app.get("/api/qa/reports")
async def get_qa_reports(limit: int = 15):
    """获取质检评估明细报表"""
    return {
        "status": "SUCCESS",
        "reports": qa_analytics_engine.get_qa_reports(limit=limit)
    }

@app.get("/api/analytics/bi-deep-dive")
async def get_bi_deep_dive():
    """获取全站深度运营 BI 归因分析大盘数据"""
    return {
        "status": "SUCCESS",
        "analytics": qa_analytics_engine.get_bi_analytics_overview()
    }

@app.get("/api/proactive/alerts")
async def get_proactive_alerts():
    """获取主动式预测服务公告与广播列表"""
    return {
        "status": "SUCCESS",
        "broadcasts": qa_analytics_engine.get_proactive_broadcasts()
    }

@app.post("/api/proactive/broadcast")
async def create_proactive_broadcast(req: CreateBroadcastRequest):
    """新建主动式事件预警广播"""
    return qa_analytics_engine.create_proactive_broadcast(
        title=req.title,
        content=req.content,
        level=req.level
    )

# ==============================================================================
# ⚡ Phase 5: 知识中台自动蒸馏自学习飞轮与影子评估沙箱 API
# ==============================================================================
@app.post("/api/knowledge/feedback-diff")
async def record_feedback_diff(req: AgentFeedbackRequest):
    """记录坐席编辑差异并沉淀蒸馏候选"""
    res = knowledge_flywheel.record_agent_feedback(
        user_query=req.user_query,
        original_draft=req.original_draft,
        final_agent_text=req.final_agent_text,
        lang=req.lang,
        agent_id=req.agent_id
    )
    return res

@app.get("/api/knowledge/distillation-candidates")
async def get_distillation_candidates():
    """获取自学习知识蒸馏候选池列表"""
    return {
        "status": "SUCCESS",
        "candidates": knowledge_flywheel.list_distillation_candidates()
    }

@app.post("/api/knowledge/approve-distillation")
async def approve_distillation(req: ApproveDistillationRequest):
    """一键审批知识蒸馏并热加载入 RAG 向量知识中台"""
    return knowledge_flywheel.approve_distillation_candidate(candidate_id=req.candidate_id)

@app.post("/api/sandbox/shadow-eval")
async def run_shadow_eval(req: ShadowEvalRequest):
    """触发影子评测沙箱回归比对"""
    res = knowledge_flywheel.run_shadow_evaluation(test_query=req.test_query, lang=req.lang)
    return {
        "status": "SUCCESS",
        "evaluation": res
    }

# ==============================================================================
# 🌐 全渠道即时通讯 (IM) 接入网关 (Telegram, WhatsApp, LINE, Web)
# ==============================================================================
class ChannelBindRequest(BaseModel):
    channel: str  # telegram, whatsapp, line
    channel_user_id: str
    platform_user_id: str = "u1001"

class SimulateInboundRequest(BaseModel):
    channel: str  # telegram, whatsapp, line
    channel_user_id: str = "tg_user_8829"
    text: str = "提现2000元为什么还没到账？"
    sender_name: Optional[str] = "IM_Member"

async def dispatch_im_core_pipeline(
    channel: str,
    channel_user_id: str,
    channel_message_id: str,
    text: str,
    sender_name: str,
    raw_metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    全渠道统一归一化调度核心链路:
    1. 幂等去重检测 (Idempotency)
    2. 账号绑定检查 (Account Binding)
    3. 安全决策、账务隔离与自动直答/降级
    4. 异步出站回发 (Outbound Dispatch)
    """
    # 1. 幂等去重
    if im_channel_gateway.is_message_duplicate(channel, channel_message_id):
        return {
            "status": "DUPLICATE_IGNORED",
            "message": f"消息 [{channel_message_id}] 已在5分钟内处理过，跳过重复调度。"
        }

    # 2. 账号安全绑定检查
    clean_text = text.strip()
    bound_user_id = im_channel_gateway.get_bound_user_id(channel, channel_user_id)

    # 支持用户直接发送 "/bind <授权码>" 或 "/bind u1001"
    if clean_text.startswith("/bind"):
        parts = clean_text.split()
        target_uid = parts[1] if len(parts) > 1 else "u1001"
        im_channel_gateway.bind_account(channel, channel_user_id, target_uid)
        reply_msg = f"✅ 【账号绑定成功】您的 {channel.upper()} 账号已与平台会员账号 [{target_uid}] 完成安全绑定！即刻可查询专属账务与提现进度。"
        await im_channel_gateway.dispatch_outbound_reply(channel, channel_user_id, reply_msg, raw_metadata)
        return {
            "status": "BIND_SUCCESS",
            "channel": channel,
            "platform_user_id": target_uid,
            "reply": reply_msg
        }

    # 如果未绑定平台账号，且涉及资金/账务敏感提问 -> 执行合规安全阻断，引导绑定
    is_financial_query = any(k in clean_text.lower() for k in ["提现", "充值", "余额", "流水", "打码", "withdraw", "deposit", "balance"])
    if not bound_user_id and is_financial_query:
        bind_guide = (
            f"🔒 【安全防护提示】您当前通过 {channel.upper()} 进线，尚未绑定平台会员账号。\n"
            f"为保障您的账户资金与隐私安全，查询个人账务与提现进度前需完成身份绑定。\n"
            f"👉 请在平台会员中心获取6位动态绑定码，并在此回复：/bind <绑定码> 完成关联。"
        )
        await im_channel_gateway.dispatch_outbound_reply(channel, channel_user_id, bind_guide, raw_metadata)
        return {
            "status": "NEED_ACCOUNT_BINDING",
            "channel": channel,
            "requires_bind": True,
            "reply": bind_guide
        }

    # 3. 构造请求并调用系统核心决策流 (JEV + CQRS + RAG + Risk Gate + LLM)
    effective_user_id = bound_user_id or f"guest_{channel}_{channel_user_id[:6]}"
    chat_req = InboundChatRequest(
        user_id=effective_user_id,
        query=text,
        auth_token="valid_token",
        mode=system_runtime_state["mode"]
    )
    result = await process_chat_v2(chat_req)

    # 4. 判定是否自动出站回发给 IM 客户端
    outbound_reply_sent = False
    reply_text = result.get("draft") or result.get("post_guard", {}).get("sanitized_text", "")

    # 当处于 Auto-Pilot 自主应答模式且风控判定为放行时，秒级直发给用户
    if result.get("is_auto_replied") and reply_text:
        await im_channel_gateway.dispatch_outbound_reply(
            channel=channel,
            channel_user_id=channel_user_id,
            text=reply_text,
            reply_metadata=raw_metadata
        )
        outbound_reply_sent = True

    return {
        "status": "PROCESSED",
        "channel": channel,
        "channel_user_id": channel_user_id,
        "platform_user_id": effective_user_id,
        "is_bound": bool(bound_user_id),
        "outbound_reply_sent": outbound_reply_sent,
        "pipeline_result": result
    }

@app.get("/api/channels/status")
async def get_channels_status():
    """获取所有 IM 渠道连接状态与接入统计"""
    return im_channel_gateway.get_channels_status()

@app.get("/api/channels/audit-logs")
async def get_channels_audit_logs():
    """获取全渠道收发审计日志"""
    return {
        "status": "SUCCESS",
        "logs": im_channel_gateway.get_recent_messages(50)
    }

@app.post("/api/channels/bind-account")
async def manual_bind_channel_account(req: ChannelBindRequest):
    """人工或系统管理端为指定 IM 账号绑定平台会员"""
    im_channel_gateway.bind_account(req.channel, req.channel_user_id, req.platform_user_id)
    return {
        "status": "SUCCESS",
        "message": f"渠道账号 [{req.channel}:{req.channel_user_id}] 成功绑定至会员 [{req.platform_user_id}]"
    }

@app.post("/api/webhook/telegram")
async def telegram_webhook(request: Request):
    """Telegram Bot 官方 Webhook 接入端点"""
    secret_header = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if not im_channel_gateway.verify_telegram_secret(secret_header):
        return {"status": "FORBIDDEN", "reason": "Invalid secret header"}

    payload = await request.json()
    norm = im_channel_gateway.parse_telegram_update(payload)
    if not norm or not norm.get("text"):
        return {"status": "OK", "reason": "Non-message update ignored"}

    res = await dispatch_im_core_pipeline(
        channel="telegram",
        channel_user_id=norm["channel_user_id"],
        channel_message_id=norm["channel_message_id"],
        text=norm["text"],
        sender_name=norm["sender_name"],
        raw_metadata=norm["raw_metadata"]
    )
    return {"status": "OK", "result": res}

@app.get("/api/webhook/whatsapp")
async def whatsapp_webhook_verification(request: Request):
    """Meta WhatsApp Cloud API Webhook 校验握手"""
    mode = request.query_params.get("hub.mode")
    verify_token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    expected_token = im_channel_gateway.channel_configs["whatsapp"].get("verify_token")
    if mode == "subscribe" and verify_token == expected_token:
        return int(challenge) if challenge and challenge.isdigit() else challenge
    return HTMLResponse(content="Forbidden", status_code=403)

@app.post("/api/webhook/whatsapp")
async def whatsapp_webhook_receive(request: Request):
    """Meta WhatsApp Cloud API 消息接收端点"""
    raw_body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")
    if not im_channel_gateway.verify_whatsapp_signature(raw_body, signature):
        return {"status": "FORBIDDEN", "reason": "Invalid signature"}

    payload = json.loads(raw_body.decode("utf-8"))
    norm = im_channel_gateway.parse_whatsapp_payload(payload)
    if not norm or not norm.get("text"):
        return {"status": "OK", "reason": "Non-text message ignored"}

    res = await dispatch_im_core_pipeline(
        channel="whatsapp",
        channel_user_id=norm["channel_user_id"],
        channel_message_id=norm["channel_message_id"],
        text=norm["text"],
        sender_name=norm["sender_name"],
        raw_metadata=norm["raw_metadata"]
    )
    return {"status": "OK", "result": res}

@app.post("/api/webhook/line")
async def line_webhook_receive(request: Request):
    """LINE Messaging API Webhook 接收端点"""
    raw_body = await request.body()
    signature = request.headers.get("X-Line-Signature")
    if not im_channel_gateway.verify_line_signature(raw_body, signature):
        return {"status": "FORBIDDEN", "reason": "Invalid LINE signature"}

    payload = json.loads(raw_body.decode("utf-8"))
    norm = im_channel_gateway.parse_line_payload(payload)
    if not norm or not norm.get("text"):
        return {"status": "OK", "reason": "Non-message event ignored"}

    res = await dispatch_im_core_pipeline(
        channel="line",
        channel_user_id=norm["channel_user_id"],
        channel_message_id=norm["channel_message_id"],
        text=norm["text"],
        sender_name=norm["sender_name"],
        raw_metadata=norm["raw_metadata"]
    )
    return {"status": "OK", "result": res}

@app.post("/api/channels/simulate-inbound")
async def simulate_im_inbound(req: SimulateInboundRequest):
    """
    全渠道模拟测试入口 (专为测试联调提供):
    无需真实配置境外 Webhook，可直接模拟 Telegram / WhatsApp / LINE 真实消息调度！
    """
    msg_id = f"sim_{req.channel}_{time.time_ns()}"
    res = await dispatch_im_core_pipeline(
        channel=req.channel,
        channel_user_id=req.channel_user_id,
        channel_message_id=msg_id,
        text=req.text,
        sender_name=req.sender_name or f"{req.channel.capitalize()}User",
        raw_metadata={"is_simulation": True}
    )
    return {"status": "SUCCESS", "result": res}

# ==============================================================================
# Enterprise Feature Suite: ACD 路由分配、CSAT满意度、班长席密语/强插、客户旅程漫游
# ==============================================================================

class ACDRouteRequest(BaseModel):
    user_id: str = "u1001"
    username: Optional[str] = "vip_player_88"
    vip_level: Optional[int] = 3
    language: Optional[str] = "zh"
    intent: Optional[str] = "BILLING_ORDER_QUERY"
    channel: Optional[str] = "WEB"

class ACDReleaseRequest(BaseModel):
    agent_id: str = "CS-Agent-007"
    user_id: str = "u1001"

class CSATSubmitRequest(BaseModel):
    session_id: Optional[str] = None
    user_id: str = "u1001"
    username: Optional[str] = "vip_player_88"
    agent_id: Optional[str] = "CS-Agent-007"
    agent_name: Optional[str] = "张晓明"
    rating: int = 5
    tags: Optional[List[str]] = []
    comment: Optional[str] = ""
    channel: Optional[str] = "WEB"

class WhisperNoteRequest(BaseModel):
    session_id: str = "SES-u1001"
    user_id: str = "u1001"
    supervisor_id: str = "SUP-01"
    supervisor_name: str = "王主管 (班长席)"
    content: str

class BargeInRequest(BaseModel):
    session_id: str = "SES-u1001"
    user_id: str = "u1001"
    supervisor_id: str = "SUP-01"
    supervisor_name: str = "王主管 (班长席)"
    reason: str = "客户情绪触发重大客诉危机，班长席强插接管"

class TypingPreviewRequest(BaseModel):
    user_id: str = "u1001"
    text: str

class MaskingAuditRequest(BaseModel):
    agent_id: str = "CS-Agent-007"
    user_id: str = "u1001"
    field_name: str = "bank_card"
    reason: str = "财务出款卡单需要核对银行卡后四位与完整开户行"

# 1. ACD 路由与排队
@app.post("/api/acd/route")
async def route_acd_conversation(req: ACDRouteRequest):
    res = acd_routing_engine.route_conversation(req.model_dump())
    return {"status": "SUCCESS", "routing": res}

@app.post("/api/acd/release")
async def release_acd_conversation(req: ACDReleaseRequest):
    res = acd_routing_engine.release_conversation(req.agent_id, req.user_id)
    return {"status": "SUCCESS", "release": res}

@app.get("/api/acd/overview")
async def get_acd_overview():
    return {"status": "SUCCESS", "overview": acd_routing_engine.get_acd_overview()}

# 2. CSAT 满意度与差评熔断
@app.post("/api/csat/submit")
async def submit_csat_feedback(req: CSATSubmitRequest):
    res = csat_feedback_service.submit_csat_feedback(req.model_dump())
    return res

@app.get("/api/csat/metrics")
async def get_csat_metrics():
    return {"status": "SUCCESS", "metrics": csat_feedback_service.get_csat_metrics()}

# 3. 班长席监控驾驶舱、密语与强插
@app.get("/api/supervisor/cockpit")
async def get_supervisor_cockpit():
    return {"status": "SUCCESS", "cockpit": supervisor_service.get_supervisor_cockpit()}

@app.post("/api/supervisor/whisper")
async def send_supervisor_whisper(req: WhisperNoteRequest):
    res = supervisor_service.send_whisper_note(
        session_id=req.session_id,
        user_id=req.user_id,
        supervisor_id=req.supervisor_id,
        supervisor_name=req.supervisor_name,
        content=req.content
    )
    return res

@app.post("/api/supervisor/barge-in")
async def execute_supervisor_barge_in(req: BargeInRequest):
    res = supervisor_service.execute_barge_in(
        session_id=req.session_id,
        user_id=req.user_id,
        supervisor_id=req.supervisor_id,
        supervisor_name=req.supervisor_name,
        reason=req.reason
    )
    return res

@app.get("/api/supervisor/typing-preview/{user_id}")
async def get_typing_preview(user_id: str):
    preview = supervisor_service.get_typing_preview(user_id)
    return {"status": "SUCCESS", "user_id": user_id, "typing_text": preview}

@app.post("/api/supervisor/typing-preview")
async def update_typing_preview(req: TypingPreviewRequest):
    res = supervisor_service.update_typing_preview(req.user_id, req.text)
    return {"status": "SUCCESS", "preview": res}

# 4. 全生命周期客户旅程与全渠道漫游
@app.get("/api/customer/journey/{user_id}")
async def get_customer_journey(user_id: str):
    res = customer_journey_service.get_customer_journey(user_id)
    return {"status": "SUCCESS", "journey": res}

# 5. 敏感数据解密审计日志记录
@app.post("/api/security/unmask-audit")
async def log_unmask_audit(req: MaskingAuditRequest):
    return {
        "status": "UNMASK_GRANTED",
        "agent_id": req.agent_id,
        "user_id": req.user_id,
        "field_name": req.field_name,
        "raw_value": "6222021000889988" if req.field_name == "bank_card" else "13800138000",
        "logged_audit": {
            "operator": req.agent_id,
            "target": req.user_id,
            "field": req.field_name,
            "reason": req.reason,
            "timestamp": time.time()
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
