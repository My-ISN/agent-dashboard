"""
Customer Service & FAQ Specialist Agent (AGENT-CS-01)
Menangani komplain kendala teknis unit laptop, panduan troubleshooting, syarat sewa,
serta penanganan darurat Intervensi Manusia (OTP & CAPTCHA).
"""

from agents.base_agent import BaseAgent
from core.models import UserMessage, AgentExecutionResult, RouteDecision


class CustomerServiceAgent(BaseAgent):
    agent_id = "AGENT-CS-01"
    name = "Customer Service & Support Agent"
    role_title = "Helpdesk & Customer Care Specialist"
    capabilities = ["faq_support", "troubleshoot_complaint", "create_ticket", "terms_explanation", "human_fallback"]
    allowed_tools = ["search_knowledge_faq", "create_support_ticket", "lookup_active_rental", "send_message"]

    async def process(self, message: UserMessage, route_decision: RouteDecision) -> AgentExecutionResult:
        query = message.text.lower()
        tools_called = []

        # 1. PENCEGAHAN KEAMANAN: CAPTCHA / OTP (RULE-SEC-01 & RULE-SEC-02)
        if route_decision.intent == "SECURITY_HUMAN_INTERVENTION":
            return AgentExecutionResult(
                agent_id=self.agent_id,
                action_taken="HUMAN_INTERVENTION_REQUIRED",
                reply_message=(
                    "PERINGATAN KEAMANAN: Terdeteksi permintaan verifikasi CAPTCHA atau Kode OTP SMS. "
                    "Sesuai protokol keamanan ISKOM, AI dilarang memproses kode keamanan secara otomatis. "
                    "Eksekusi dihentikan sementara dan diteruskan ke staf/operator manusia untuk verifikasi langsung."
                ),
                status="HUMAN_INTERVENTION_REQUIRED",
                tools_called=tools_called,
                requires_approval=True
            )

        # 2. Pertanyaan seputar Denda / Kebijakan
        if "denda" in query:
            return AgentExecutionResult(
                agent_id=self.agent_id,
                action_taken="POLICY_EXPLAINED",
                reply_message=(
                    "Kebijakan Denda Keterlambatan ISKOM:\n"
                    "Batas toleransi pengembalian adalah 2 jam setelah masa sewa berakhir. "
                    "Keterlambatan melebihi batas toleransi dikenakan denda harian sebesar: "
                    "Tarif Sewa Harian + 20% surcharge per hari."
                ),
                status="SUCCESS",
                tools_called=["search_knowledge_faq"],
                requires_approval=False
            )

        # 3. Pertanyaan seputar Syarat Sewa / KTP / Deposit
        if any(w in query for w in ["syarat", "jaminan", "ktp", "deposit", "prosedur"]):
            tools_called.append("search_knowledge_faq")
            faq_item = self.knowledge.search_faq(query) if self.knowledge else None
            answer = faq_item["answer"] if faq_item else "Syarat sewa perorangan: KTP Asli + Deposit Rp 200rb - 500rb."
            return AgentExecutionResult(
                agent_id=self.agent_id,
                action_taken="FAQ_ANSWERED",
                reply_message=f"Informasi Layanan ISKOM:\n{answer}",
                status="SUCCESS",
                tools_called=tools_called,
                requires_approval=False
            )

        # 4. Laporan Kendala Teknis / Unit Rusak
        tools_called.append("create_ticket")
        if self.tools:
            await self.tools.execute(
                "create_ticket",
                self.agent_id,
                customer_name=message.user_id,
                issue_category="HARDWARE",
                description=message.text,
                priority="HIGH"
            )

        return AgentExecutionResult(
            agent_id=self.agent_id,
            action_taken="TICKET_CREATED",
            reply_message=(
                "Customer Care ISKOM: Kami memohon maaf atas kendala pada unit laptop sewa Anda. "
                "Sesuai SOP Layanan ISKOM (Garansi Swap Unit 1x24 jam), tiket perbaikan telah diterbitkan di sistem Helpdesk. "
                "Teknisi kami siap melakukan penukaran unit cadangan dengan spesifikasi sepadan ke lokasi Anda."
            ),
            status="SUCCESS",
            tools_called=tools_called,
            requires_approval=False
        )
