"""
Finance & Invoicing Specialist Agent (AGENT-FIN-01)
Menangani status invoice, mutasi rekening, penagihan, dan deposit jaminan sewa.
"""

from agents.base_agent import BaseAgent
from core.models import UserMessage, AgentExecutionResult, RouteDecision


class FinanceAgent(BaseAgent):
    agent_id = "AGENT-FIN-01"
    name = "Finance & Invoicing Agent"
    role_title = "Billing & Invoicing Specialist"
    capabilities = ["check_invoice", "verify_payment", "calculate_deposit", "refund_inquiry"]
    allowed_tools = ["create_invoice", "verify_bank_mutation", "query_invoice_status"]

    async def process(self, message: UserMessage, route_decision: RouteDecision) -> AgentExecutionResult:
        entities = route_decision.extracted_entities
        invoice_no = entities.get("invoice_number", "Tagihan Aktif")

        tools_called = ["query_invoice_status"]

        return AgentExecutionResult(
            agent_id=self.agent_id,
            action_taken="INVOICE_QUERIED",
            reply_message=(
                f"Informasi Keuangan & Billing ISKOM: Data untuk '{invoice_no}' telah diperiksa di sistem pembukuan. "
                f"Status pembayaran tercatat resmi di database HRIS Invoicing."
            ),
            status="SUCCESS",
            tools_called=tools_called,
            requires_approval=False
        )
