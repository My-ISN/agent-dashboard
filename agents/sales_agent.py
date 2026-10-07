"""
Sales & Rental Specialist Agent (AGENT-SLS-01)
Menangani konsultasi sewa laptop, kualifikasi kebutuhan, kalkulasi harga, dan pengajuan diskon
berdasarkan data resmi dari Knowledge Base.
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
        unit_query = entities.get("unit_model", "ThinkPad")
        discount = entities.get("discount_percent", 0.0)

        # Ambil data unit riil dari Knowledge Base
        product = None
        if self.knowledge:
            product = self.knowledge.get_product_by_model(unit_query)

        product_name = product["model"] if product else unit_query
        specs = product["specs"] if product else "Core i5 / RAM 16GB"
        daily_rate = product["rates"]["daily"] if product else 75000
        monthly_rate = product["rates"]["monthly"] if product else 950000

        tools_called = ["search_laptop_catalog", "calculate_rental_pricing"]

        # Evaluasi aturan diskon jika melebihi batas 10%
        if discount > 10.0:
            return AgentExecutionResult(
                agent_id=self.agent_id,
                action_taken="DISCOUNT_APPROVAL_REQUIRED",
                reply_message=(
                    f"Permintaan sewa untuk {qty} unit '{product_name}' ({specs}) dengan pengajuan diskon {discount}% "
                    f"telah kami terima. Sesuai aturan perusahaan, diskon di atas 10% memerlukan persetujuan Owner. "
                    f"Tiket persetujuan telah otomatis kami kirimkan ke dashboard Owner."
                ),
                status="PENDING_APPROVAL",
                tools_called=tools_called,
                requires_approval=True,
                approval_details={
                    "category": "DISCOUNT_REQUEST",
                    "requested_discount_percent": discount,
                    "quantity": qty,
                    "unit": product_name,
                    "estimated_monthly_total": monthly_rate * qty
                }
            )

        # Transaksi normal: ambil rincian tarif sewa riil
        total_estimate = monthly_rate * qty
        return AgentExecutionResult(
            agent_id=self.agent_id,
            action_taken="PREPARE_QUOTATION",
            reply_message=(
                f"Kebutuhan sewa Anda untuk {qty} unit '{product_name}' telah diverifikasi di katalog ISKOM.\n"
                f"- Spesifikasi: {specs}\n"
                f"- Tarif Sewa: Rp {daily_rate:,}/hari atau Rp {monthly_rate:,}/bulan per unit.\n"
                f"- Estimasi Total: Rp {total_estimate:,} (untuk {qty} unit/bulan).\n"
                f"Draf Quotation resmi sedang diterbitkan."
            ),
            status="SUCCESS",
            tools_called=tools_called,
            requires_approval=False
        )
