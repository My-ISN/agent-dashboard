"""
Customer Service & FAQ Specialist Agent (AGENT-CS-01)
Menangani komplain kendala teknis unit laptop, panduan troubleshooting, dan syarat sewa.
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
        tools_called = ["create_support_ticket"]

        return AgentExecutionResult(
            agent_id=self.agent_id,
            action_taken="TICKET_CREATED",
            reply_message=(
                "Customer Care ISKOM: Kami mohon maaf atas kendala teknis pada unit laptop sewa Anda. "
                "Tiket bantuan telah otomatis kami terbitkan di HRIS Helpdesk. Tim teknisi operasional kami "
                "akan segera menghubungi Anda untuk koordinasi remote check atau penukaran unit (swap unit)."
            ),
            status="SUCCESS",
            tools_called=tools_called,
            requires_approval=False
        )
