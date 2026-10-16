"""
Phase 5: 知识中台自动蒸馏自学习飞轮与影子评估沙箱 (Knowledge Flywheel & Shadow Eval)
"""

import time
import json
from typing import Dict, Any, List, Optional
from app.services.rag_engine import rag_engine

class KnowledgeFlywheelService:
    def __init__(self):
        # 预设坐席优化沉淀候选条目
        self.distillation_candidates: List[Dict[str, Any]] = [
            {
                "candidate_id": "DIST2026100501",
                "user_query": "USDT充值之后多久没到账可以找客服补单？",
                "original_draft": "USDT充值通常在12个确认后到账，请耐心等待。",
                "agent_refined_text": "尊敬的会员，USDT-TRC20 通常需要 12 个区块确认（约 3-5 分钟）。若超过 15 分钟仍未入账，请直接提供以太坊/波场 TxHash 交易哈希或转账截图，我们客服可为您发起一键链上极速补单核验！",
                "category": "RECHARGE_CRYPTO",
                "lang": "zh",
                "edit_similarity": 0.62, # 进行了高质量补充
                "status": "PENDING_APPROVAL",
                "source_agent": "CS-007 (张晓明)",
                "created_at": "2026-10-05 21:50:00"
            },
            {
                "candidate_id": "DIST2026100502",
                "user_query": "How many confirmations for USDT TRC20 before manual credit?",
                "original_draft": "Please wait for 12 confirmations.",
                "agent_refined_text": "Dear member, TRC20 deposits usually require 12 confirmations (approx 3-5 mins). If it exceeds 15 mins, simply provide your TxHash and our agent will trigger 1-click on-chain instant reconciliation for you!",
                "category": "RECHARGE_CRYPTO",
                "lang": "en",
                "edit_similarity": 0.58,
                "status": "APPROVED",
                "source_agent": "CS-007 (张晓明)",
                "created_at": "2026-10-05 21:55:00"
            },
            {
                "candidate_id": "DIST2026100503",
                "user_query": "银行卡充值姓名写错了，款项会被退回吗？",
                "original_draft": "姓名不符无法入账，请联系银行。",
                "agent_refined_text": "尊敬的会员，为保障资金合规安全，存款姓名须与平台实名一致。若因同音字或附言码填错导致未到账，款项会在 24 小时内由银行原路退回，或联系人工坐席提供转账流水截屏登记人工加款通道。",
                "category": "RECHARGE_BANK",
                "lang": "zh",
                "edit_similarity": 0.45,
                "status": "PENDING_APPROVAL",
                "source_agent": "CS-007 (张晓明)",
                "created_at": "2026-10-05 22:10:00"
            },
            {
                "candidate_id": "DIST2026100504",
                "user_query": "VIP 升级之后的每月专属俸禄需要手动申请还是系统自动发放？",
                "original_draft": "VIP 俸禄系统自动派发。",
                "agent_refined_text": "尊敬的贵宾会员，当月晋级达标后，系统将在次月 1 日 15:00 前将月度俸禄自动结算至您的主账户余额，无需手动申请；且享有终身保级、无清零降级待遇！",
                "category": "VIP_PROMOTION",
                "lang": "zh",
                "edit_similarity": 0.50,
                "status": "APPROVED",
                "source_agent": "CS-003 (李雅晴)",
                "created_at": "2026-10-05 22:30:00"
            },
            {
                "candidate_id": "DIST2026100505",
                "user_query": "Tại sao tài khoản của tôi bị tạm dừng nạp rút?",
                "original_draft": "Tài khoản đang bị rà soát bảo mật.",
                "agent_refined_text": "Kính gửi quý hội viên, do hệ thống bảo mật phát hiện tài khoản đăng nhập từ dải IP bất thường hoặc nghi ngờ vi phạm quy định cược, lệnh nạp rút đang được tạm giữ để phòng ngừa rủi ro. Vui lòng cung cấp CCCD/Hộ chiếu để CSKH mở khóa tức thì.",
                "category": "ACCOUNT_SECURITY",
                "lang": "vi",
                "edit_similarity": 0.55,
                "status": "PENDING_APPROVAL",
                "source_agent": "CS-005 (Nguyễn Văn Nam)",
                "created_at": "2026-10-05 23:10:00"
            },
            {
                "candidate_id": "DIST2026100506",
                "user_query": "สามารถยกเลิกโปรโมชั่นเพื่อถอนเงินก่อนทำเทิร์นครบได้ไหม?",
                "original_draft": "ไม่สามารถยกเลิกได้ ต้องทำเทิร์นให้ครบ.",
                "agent_refined_text": "เรียนท่านสมาชิก หากท่านยังไม่ได้เริ่มเดิมพันด้วยยอดเงินโบนัส สามารถแจ้งเจ้าหน้าที่เพื่อขอยกเลิกโปรโมชั่นและหักยอดโบนัสออก เพื่อทำรายการถอนเงินต้นได้ทันทีโดยไม่ต้องทำยอดเทิร์นโอเวอร์คงค้างครับ",
                "category": "BONUS_TURNOVER",
                "lang": "th",
                "edit_similarity": 0.40,
                "status": "PENDING_APPROVAL",
                "source_agent": "CS-008 (Somchai)",
                "created_at": "2026-10-06 00:15:00"
            }
        ]

        # 影子评测实验记录
        self.shadow_eval_logs: List[Dict[str, Any]] = [
            {
                "eval_id": "EVAL_SHADOW_01",
                "benchmark_model": "DeepSeek-V3 (Production Baseline)",
                "candidate_model": "CoreDesk-Distilled-V2 (Shadow Candidate)",
                "test_dataset_size": 250,
                "factual_consistency": 99.2, # 事实一致性
                "hallucination_rate": 0.2,    # 幻觉率
                "avg_latency_ms": 1.2,
                "status": "PASS_RECOMMENDED",
                "timestamp": "2026-10-06 02:00:00"
            }
        ]

    def record_agent_feedback(
        self,
        user_query: str,
        original_draft: str,
        final_agent_text: str,
        lang: str = "zh",
        agent_id: str = "CS-007 (张晓明)"
    ) -> Dict[str, Any]:
        """
        1. 捕获坐席对 AI 草稿的修改 diff 并提炼知识飞轮候选
        """
        start_time = time.perf_counter()
        
        # 简单比对差异（长度差异与内容变化）
        is_meaningfully_edited = (
            len(final_agent_text) >= 15 and 
            final_agent_text.strip() != original_draft.strip()
        )
        
        candidate_created = False
        candidate_id = None
        
        if is_meaningfully_edited:
            candidate_id = f"DIST{int(time.time()*1000)}"
            new_candidate = {
                "candidate_id": candidate_id,
                "user_query": user_query,
                "original_draft": original_draft,
                "agent_refined_text": final_agent_text,
                "category": "AGENT_ACTIVE_LEARNING",
                "lang": lang,
                "edit_similarity": round(min(len(original_draft), len(final_agent_text)) / max(len(original_draft), len(final_agent_text), 1), 2),
                "status": "PENDING_APPROVAL",
                "source_agent": agent_id,
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.distillation_candidates.insert(0, new_candidate)
            candidate_created = True

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "status": "SUCCESS",
            "candidate_created": candidate_created,
            "candidate_id": candidate_id,
            "message": "已捕获坐席优质话术修改并沉淀至自学习蒸馏候选池！" if candidate_created else "修改幅度较小或无修改，保持当前知识版本。",
            "latency_ms": latency_ms
        }

    def list_distillation_candidates(self) -> List[Dict[str, Any]]:
        return self.distillation_candidates

    def approve_distillation_candidate(self, candidate_id: str) -> Dict[str, Any]:
        """
        2. 知识库管理员一键审批并将其沉淀入 RAG 知识库
        """
        target = None
        for c in self.distillation_candidates:
            if c["candidate_id"] == candidate_id:
                target = c
                break
                
        if not target:
            return {"status": "ERROR", "message": f"未找到候选条目: {candidate_id}"}
            
        target["status"] = "APPROVED"
        target["approved_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # 将其同步推入 RAG 知识库实例
        new_knowledge_entry = {
            "rule_id": f"RULE_AUTO_{candidate_id}",
            "category": target.get("category", "FAQ"),
            "title": f"【自学习沉淀】{target['user_query'][:24]}",
            "content": target["agent_refined_text"],
            "lang": target.get("lang", "zh"),
            "keywords": [target["user_query"][:10], "自学习沉淀", "标准话术"]
        }
        rag_engine.knowledge_base.append(new_knowledge_entry)
        
        return {
            "status": "SUCCESS",
            "candidate_id": candidate_id,
            "message": "候选话术已成功核准入库，RAG 知识向量中台已实时完成热加载更新！",
            "knowledge_entry": new_knowledge_entry
        }

    def run_shadow_evaluation(
        self,
        test_query: str = "提现需要完成多少倍打码流水？",
        lang: str = "zh"
    ) -> Dict[str, Any]:
        """
        3. 影子评估沙箱 (Shadow Testing & Regression Sandbox)
        """
        start = time.perf_counter()
        
        # 1. 模拟线上 Baseline 模型调用
        baseline_resp = "通常充值本金需要完成 1.0 倍有效投注流水方可申请出款。"
        baseline_time_ms = 0.85
        
        # 2. 模拟新蒸馏 Shadow 候选模型调用
        shadow_resp = (
            "平台出款流水标准：\n"
            "1. 充值普通本金仅需完成 1.0 倍有效投注打码即可随时提现；\n"
            "2. 若参与首存优惠或彩金活动，则需按照活动规则完成指定倍数打码（如首存优惠需10倍流水）。"
        )
        shadow_time_ms = 0.92
        
        eval_result = {
            "eval_id": f"EVAL_{int(time.time()*1000)}",
            "query": test_query,
            "lang": lang,
            "baseline": {
                "model": "DeepSeek-V3-Production",
                "response": baseline_resp,
                "latency_ms": baseline_time_ms,
                "hallucination_detected": False,
                "factual_score": 92.0
            },
            "shadow_candidate": {
                "model": "CoreDesk-Distilled-V2",
                "response": shadow_resp,
                "latency_ms": shadow_time_ms,
                "hallucination_detected": False,
                "factual_score": 99.0
            },
            "verdict": "SHADOW_SURPASSES_BASELINE",
            "recommendation": "候选蒸馏模型在知识丰富度与打码细则上显著占优，且 0 幻觉，建议推进金丝雀灰度发布！",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.shadow_eval_logs.insert(0, eval_result)
        return eval_result

knowledge_flywheel = KnowledgeFlywheelService()
