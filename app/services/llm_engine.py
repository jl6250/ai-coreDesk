import os
import json
import asyncio
import httpx
from typing import AsyncGenerator, Dict, Any, Optional

class LLMGenerationEngine:
    """
    🧠 System 2: LLM 生成引擎 (多语言支持)
    支持 zh (中文), en (English), vi (Tiếng Việt), th (ภาษาไทย)
    """
    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY", "")
        self.api_base = os.getenv("LLM_API_BASE", "https://api.deepseek.com/v1")
        self.model_name = os.getenv("LLM_MODEL", "deepseek-chat")

    async def generate_draft_response(
        self,
        user_query: str,
        user_info: Optional[Dict[str, Any]],
        rag_context: str,
        lang: str = "zh"
    ) -> str:
        """生成多语言坐席草稿文本"""
        if self.api_key:
            try:
                lang_names = {"zh": "Chinese", "en": "English", "vi": "Vietnamese", "th": "Thai"}
                target_lang_str = lang_names.get(lang, "English")
                system_prompt = (
                    f"You are a professional customer support agent for a licensed gaming platform. "
                    f"Please answer strictly in {target_lang_str}. "
                    "You are a factual translator and must NEVER fabricate amounts, turnover, or make fake promises.\n"
                    f"Business Rules & FAQ:\n{rag_context}\n"
                )
                user_msg = f"User query: {user_query}\n"
                if user_info and user_info.get("found"):
                    user_msg += f"Realtime Billing Snapshot: {json.dumps(user_info, ensure_ascii=False)}\n"

                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(
                        f"{self.api_base}/chat/completions",
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        json={
                            "model": self.model_name,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_msg}
                            ],
                            "temperature": 0.3
                        }
                    )
                    if resp.status_code == 200:
                        return resp.json()["choices"][0]["message"]["content"]
            except Exception:
                pass

        # 本地智能事实翻译器渲染引擎 (支持 zh, en, vi, th 四语种)
        return self._render_multilingual_fact_draft(user_query, user_info, rag_context, lang)

    def _render_multilingual_fact_draft(
        self,
        user_query: str,
        user_info: Optional[Dict[str, Any]],
        rag_context: str,
        lang: str
    ) -> str:
        username = "Member"
        vip = "VIP"
        if user_info and user_info.get("found"):
            username = user_info.get("username", "Member")
            vip = user_info.get("vip_level", "VIP")

        turnover = user_info.get("turnover_status", {}) if (user_info and user_info.get("found")) else {}
        orders = user_info.get("recent_orders", []) if (user_info and user_info.get("found")) else []
        latest_tx = next((o for o in orders if o["type"] == "WITHDRAWAL"), None)
        latest_cz = next((o for o in orders if o["type"] == "DEPOSIT"), None)

        is_billing_withdraw = any(w in user_query.lower() for w in ["提现", "流水", "withdraw", "rút", "ถอน", "turnover"])
        is_billing_deposit = any(w in user_query.lower() for w in ["充值", "deposit", "nạp", "ฝาก"])
        is_rebate = any(w in user_query.lower() for w in ["返水", "洗码", "rebate", "cashback", "hoàn trả", "คืนเงิน"])

        # ==================== 1. 英语 (en) ====================
        if lang == "en":
            greeting = f"Dear {vip} member [{username}], hello!"
            if is_billing_withdraw and latest_tx and latest_tx["status"] == "PENDING_AUDIT":
                diff = turnover.get("diff", 0)
                return (
                    f"{greeting}\n\n"
                    f"We have verified your withdrawal request submitted at {latest_tx['created_at']} "
                    f"(Order: {latest_tx['order_id']}, Amount: {latest_tx['amount']:.2f} CNY).\n\n"
                    f"📊 [Turnover Status]:\n"
                    f"- Completed valid turnover: {turnover.get('current', 0):.2f}\n"
                    f"- Required minimum turnover: {turnover.get('required', 0):.2f}\n"
                    f"- Remaining turnover needed: {diff:.2f}\n\n"
                    f"Status: [{latest_tx['status_desc']}]. "
                    f"Once you complete the remaining turnover requirement in eligible games, "
                    f"our payout system will process the withdrawal immediately. Thank you for your patience!"
                )
            if is_billing_deposit and latest_cz:
                return (
                    f"{greeting}\n\n"
                    f"We have located your recent deposit (Order: {latest_cz['order_id']}, Amount: {latest_cz['amount']:.2f} USDT).\n\n"
                    f"⏳ Status: [{latest_cz['status_desc']}]. "
                    f"Blockchain confirmation usually takes 1-3 minutes. Your account balance will update automatically upon completion."
                )
            if is_rebate:
                return (
                    f"{greeting}\n\n"
                    f"Daily rebate is calculated at 03:00 AM next day and distributed automatically by 12:00 PM. "
                    f"Rebates carry 0x turnover requirement and can be withdrawn directly."
                )
            return (
                f"{greeting}\n\n"
                f"According to platform security regulations, all transactions follow transparent compliance policies. "
                f"Please provide your transaction order ID if you require further verification."
            )

        # ==================== 2. 越南语 (vi) ====================
        if lang == "vi":
            greeting = f"Kính chào quý hội viên {vip} [{username}]!"
            if is_billing_withdraw and latest_tx and latest_tx["status"] == "PENDING_AUDIT":
                diff = turnover.get("diff", 0)
                return (
                    f"{greeting}\n\n"
                    f"Hệ thống đã xác minh lệnh rút tiền của quý khách lúc {latest_tx['created_at']} "
                    f"(Mã đơn: {latest_tx['order_id']}, Số tiền: {latest_tx['amount']:.2f} CNY).\n\n"
                    f"📊 [Chi tiết doanh thu cược]:\n"
                    f"- Cược hợp lệ hiện tại: {turnover.get('current', 0):.2f}\n"
                    f"- Cược tối thiểu yêu cầu: {turnover.get('required', 0):.2f}\n"
                    f"- Cần thêm doanh thu cược: {diff:.2f}\n\n"
                    f"Trạng thái: [{latest_tx['status_desc']}]. "
                    f"Quý khách vui lòng hoàn tất phần doanh thu cược còn lại trong trò chơi, "
                    f"hệ thống sẽ tự động xuất khoản ngay sau khi đủ điều kiện. Xin cảm ơn!"
                )
            if is_billing_deposit and latest_cz:
                return (
                    f"{greeting}\n\n"
                    f"Hệ thống đã kiểm tra lệnh nạp gần nhất (Mã đơn: {latest_cz['order_id']}, Số tiền: {latest_cz['amount']:.2f} USDT).\n\n"
                    f"⏳ Trạng thái: [{latest_cz['status_desc']}]. "
                    f"Xác nhận chuỗi khối thường hoàn tất trong vòng 1-3 phút. Số dư sẽ tự động được cộng vào tài khoản."
                )
            if is_rebate:
                return (
                    f"{greeting}\n\n"
                    f"Tiền hoàn trả hàng ngày được tổng kết lúc 03:00 sáng hôm sau và tự động phát trước 12:00 trưa. "
                    f"Hoàn trả không yêu cầu vòng cược, quý khách có thể rút tiền trực tiếp."
                )
            return (
                f"{greeting}\n\n"
                f"Theo quy định kiểm soát rủi ro, mọi hoạt động tài chính đều được bảo mật minh bạch. "
                f"Quý khách vui lòng cung cấp mã đơn để được hỗ trợ kiểm tra chi tiết."
            )

        # ==================== 3. 泰语 (th) ====================
        if lang == "th":
            greeting = f"สวัสดีคุณลูกค้าสมาชิก {vip} [{username}]!"
            if is_billing_withdraw and latest_tx and latest_tx["status"] == "PENDING_AUDIT":
                diff = turnover.get("diff", 0)
                return (
                    f"{greeting}\n\n"
                    f"ระบบได้ตรวจสอบคำขอถอนเงินของคุณเมื่อ {latest_tx['created_at']} "
                    f"(รหัสคำสั่งซื้อ: {latest_tx['order_id']}, จำนวน: {latest_tx['amount']:.2f} CNY)\n\n"
                    f"📊 [สถานะยอดเทิร์นโอเวอร์]:\n"
                    f"- ยอดเทิร์นปัจจุบัน: {turnover.get('current', 0):.2f}\n"
                    f"- ยอดเทิร์นขั้นต่ำที่กำหนด: {turnover.get('required', 0):.2f}\n"
                    f"- ยอดเทิร์นคงเหลือที่ต้องทำ: {diff:.2f}\n\n"
                    f"สถานะ: [{latest_tx['status_desc']}]. "
                    f"เมื่อคุณทำยอดเทิร์นโอเวอร์ครบตามเงื่อนไข ระบบจะดำเนินการโอนเงินให้ทันที ขอขอบคุณสำหรับความเข้าใจ!"
                )
            if is_billing_deposit and latest_cz:
                return (
                    f"{greeting}\n\n"
                    f"เราได้ตรวจสอบคำสั่งฝากเงินล่าสุดของคุณ (รหัส: {latest_cz['order_id']}, จำนวน: {latest_cz['amount']:.2f} USDT)\n\n"
                    f"⏳ สถานะ: [{latest_cz['status_desc']}]. "
                    f"การยืนยันบล็อกเชนใช้เวลาประมาณ 1-3 นาที ยอดเงินจะเข้าสู่บัญชีของคุณโดยอัตโนมัติ"
                )
            if is_rebate:
                return (
                    f"{greeting}\n\n"
                    f"ยอดคืนเงินรายวันจะคำนวณเวลา 03:00 น. และจ่ายอัตโนมัติก่อน 12:00 น. ของวันถัดไป "
                    f"ไม่มีเงื่อนไขยอดเทิร์น สามารถถอนหรือเล่นเกมได้ทันที"
                )
            return (
                f"{greeting}\n\n"
                f"ตามนโยบายความปลอดภัยทางการเงิน ทุกคำสั่งจะได้รับการประมวลผลอย่างโปร่งใส "
                f"โปรดแจ้งรหัสคำสั่งซื้อหากต้องการให้ตรวจสอบเพิ่มเติม"
            )

        # ==================== 4. 默认简体中文 (zh) ====================
        greeting = f"尊敬的 {vip} 会员【{username}】，您好！"
        if is_billing_withdraw and latest_tx and latest_tx["status"] == "PENDING_AUDIT":
            diff = turnover.get("diff", 0)
            return (
                f"{greeting}\n\n"
                f"系统已为您核实到您于 {latest_tx['created_at']} 提交的提现申请（单号：{latest_tx['order_id']}，金额：{latest_tx['amount']:.2f} 元）。\n\n"
                f"📊 【流水状态说明】：\n"
                f"- 当前有效投注流水：{turnover.get('current', 0):.2f}\n"
                f"- 提现要求最低流水：{turnover.get('required', 0):.2f}\n"
                f"- 尚需完成有效流水：{diff:.2f}\n\n"
                f"目前该笔提现处于【{latest_tx['status_desc']}】状态。建议您继续在游戏中完成剩余的有效打码量后，系统将自动推进出款流程。感谢您的理解与支持！"
            )
        if is_billing_deposit and latest_cz:
            return (
                f"{greeting}\n\n"
                f"已为您查询到您最新的充值订单（单号：{latest_cz['order_id']}，金额：{latest_cz['amount']:.2f} USDT）。\n\n"
                f"⏳ 【处理进度】：当前为【{latest_cz['status_desc']}】。\n"
                f"区块链网络在确认后一般会在 1-3 分钟内自动加款至您的主账户。请您稍作留意，资金安全敬请放心！"
            )
        if is_rebate:
            return (
                f"{greeting}\n\n"
                f"平台每日洗码/返水结算时间为次日凌晨 03:00 开始核算，并在中午 12:00 前统一派发至您的主账户余额。\n"
                f"返水彩金享受 0 流水要求，到账后可直接参与游戏或申请提现。"
            )
        return (
            f"{greeting}\n\n"
            f"根据平台资金风控安全与合规流程，所有账户与资金操作均实时遵循透明结算原则。\n"
            f"若需要协助核实特定订单，请随时提供对应凭证单号，专属坐席将为您快速排查。"
        )

llm_engine = LLMGenerationEngine()
