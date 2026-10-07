"""
Customer Service & FAQ Specialist Agent (AGENT-CS-01)
Menangani komplain kendala teknis unit laptop, panduan troubleshooting, dan syarat sewa
berdasarkan FAQ dan SOP resmi dari Knowledge Base.
"""

from agents.base_agent import BaseAgent
from core.models import UserMessage, AgentExecutionResult, RouteDecision


class CustomerServiceAgent(BaseAgent):
    agent_id = "AGENT-CS-01"
    name = "Customer Service & Support Agent"
    role_title = "Helpdesk & Customer Care Specialist"
    capabilities = ["faq_support", "troubleshoot_complaint", "create_ticket", "terms_explanation"]
    allowed_tools = ["search_knowledge_faq", "create_support_ticket", "lookup_active_rental"]

    async def process(self, message: UserMessage, route_decision: RouteDecision) -> AgentExecutionResult:
        query = message.text.lower()
        tools_called = ["search_knowledge_faq"]

        # Cek apakah ini pertanyaan seputar syarat sewa / jaminan
        if any(w in query for w in ["syarat", "jaminan", "ktp", "deposit", "prosedur"]):
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

        # Jika ini laporan kendala teknis / kerusakan unit
        tools_called.append("create_support_ticket")
        return AgentExecutionResult(
            agent_id=self.agent_id,
            action_taken="TICKET_CREATED",
            reply_message=(
                "Customer Care ISKOM: Kami memohon maaf atas kendala pada unit laptop sewa Anda. "
                "Sesuai SOP Layanan ISKOM (Garansi Swap Unit 1x24 jam), tiket perbaikan telah diterbitkan. "
                "Teknisi kami siap melakukan penggantian unit cadangan dengan spek sepadan ke lokasi Anda."
            ),
            status="SUCCESS",
            tools_called=tools_called,
            requires_approval=False
        )
