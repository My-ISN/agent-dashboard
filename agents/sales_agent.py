"""
Sales & Rental Specialist Agent (AGENT-SLS-01)
Menangani konsultasi sewa laptop, kualifikasi kebutuhan, kalkulasi harga, dan pengajuan diskon.
"""

from typing import Dict, Any
from agents.base_agent import BaseAgent
from core.models import UserMessage, AgentExecutionResult, RouteDecision


class SalesRentalAgent(BaseAgent):
    agent_id = "AGENT-SLS-01"
    name = "Sales & Rental Agent"
    role_title = "Rental Sales Consultant"
    capabilities = ["rental_inquiry", "quotation_request", "discount_proposal", "unit_recommendation"]
    allowed_tools = ["search_laptop_catalog", "calculate_rental_pricing", "create_rental_quotation"]

    async def process(self, message: UserMessage, route_decision: RouteDecision) -> AgentExecutionResult:
        entities = route_decision.extracted_entities
        qty = entities.get("quantity", 1)
        unit = entities.get("unit_model", "Laptop Standar")
        discount = entities.get("discount_percent", 0.0)

        tools_called = ["search_laptop_catalog", "calculate_rental_pricing"]

        # Evaluasi aturan diskon jika ada permintaan diskon
        if discount > 10.0:
            return AgentExecutionResult(
                agent_id=self.agent_id,
                action_taken="DISCOUNT_APPROVAL_REQUIRED",
                reply_message=(
                    f"Permintaan sewa untuk {qty} unit '{unit}' dengan permohonan diskon {discount}% "
                    f"telah kami catat. Karena diskon melebihi wewenang mandiri agen (> 10%), "
                    f"pengajuan penawaran ini telah diteruskan ke Owner untuk mendapatkan persetujuan (estimasi < 10 menit)."
                ),
                status="PENDING_APPROVAL",
                tools_called=tools_called,
                requires_approval=True,
                approval_details={
                    "category": "DISCOUNT_REQUEST",
                    "requested_discount_percent": discount,
                    "quantity": qty,
                    "unit": unit
                }
            )

        # Transaksi normal
        return AgentExecutionResult(
            agent_id=self.agent_id,
            action_taken="PREPARE_QUOTATION",
            reply_message=(
                f"Halo! Kebutuhan sewa Anda untuk {qty} unit '{unit}' telah kami verifikasi. "
                f"Spesifikasi unit dan estimasi penawaran resmi (Quotation) sedang disiapkan sesuai tarif standar ISKOM."
            ),
            status="SUCCESS",
            tools_called=tools_called,
            requires_approval=False
        )
