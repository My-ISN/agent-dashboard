"""
Sales & Rental Specialist Agent (AGENT-SLS-01)
Menangani konsultasi sewa laptop, kualifikasi kebutuhan, kalkulasi harga, dan pengajuan diskon
melalui eksekusi Tools resmi dengan RBAC Guard.
"""

from typing import Dict, Any
from agents.base_agent import BaseAgent
from core.models import UserMessage, AgentExecutionResult, RouteDecision


class SalesRentalAgent(BaseAgent):
    agent_id = "AGENT-SLS-01"
    name = "Sales & Rental Agent"
    role_title = "Rental Sales Consultant"
    capabilities = ["rental_inquiry", "quotation_request", "discount_proposal", "unit_recommendation"]
    allowed_tools = ["search_customer", "search_product", "check_inventory", "create_lead", "create_quotation", "request_approval"]

    async def process(self, message: UserMessage, route_decision: RouteDecision) -> AgentExecutionResult:
        entities = route_decision.extracted_entities
        qty = entities.get("quantity", 1)
        unit_query = entities.get("unit_model", "ThinkPad")
        discount = entities.get("discount_percent", 0.0)

        tools_invoked = []

        # 1. Panggil Tool Cek Inventaris melalui Tool Registry
        inv_check = None
        if self.tools:
            inv_res = await self.tools.execute("check_inventory", self.agent_id, model_or_sku=unit_query, requested_qty=qty)
            if inv_res.get("status") == "SUCCESS":
                inv_check = inv_res.get("result")
                tools_invoked.append("check_inventory")

        # 2. Ambil data produk dari Knowledge Base
        product = self.knowledge.get_product_by_model(unit_query) if self.knowledge else None
        product_name = product["model"] if product else unit_query
        specs = product["specs"] if product else "Core i5 / RAM 16GB"
        monthly_rate = product["rates"]["monthly"] if product else 950000

        # 3. Evaluasi aturan diskon jika melebihi batas 10%
        if discount > 10.0:
            apv_ticket = None
            if self.tools:
                apv_res = await self.tools.execute(
                    "request_approval",
                    self.agent_id,
                    requester_agent_id=self.agent_id,
                    rule_id="RULE-DISC-02",
                    category="DISCOUNT_REQUEST",
                    payload={
                        "unit": product_name,
                        "qty": qty,
                        "requested_discount": discount,
                        "estimated_monthly": monthly_rate * qty
                    },
                    rationale=f"Klien memesan {qty} unit laptop dengan permintaan diskon {discount}%."
                )
                if apv_res.get("status") == "SUCCESS":
                    apv_ticket = apv_res["result"]["approval_id"]
                    tools_invoked.append("request_approval")

            return AgentExecutionResult(
                agent_id=self.agent_id,
                action_taken="DISCOUNT_APPROVAL_REQUIRED",
                reply_message=(
                    f"Permintaan sewa untuk {qty} unit '{product_name}' ({specs}) dengan pengajuan diskon {discount}% "
                    f"telah kami terima. Tiket persetujuan #{apv_ticket} telah otomatis dikirimkan ke dashboard Owner."
                ),
                status="PENDING_APPROVAL",
                tools_called=tools_invoked,
                requires_approval=True,
                approval_details={
                    "approval_id": apv_ticket,
                    "category": "DISCOUNT_REQUEST",
                    "discount_percent": discount
                }
            )

        # 4. Transaksi normal: terbitkan quotation melalui Tool
        quo_res = None
        if self.tools:
            q_exec = await self.tools.execute(
                "create_quotation",
                self.agent_id,
                customer_name=message.user_id,
                unit_model=product_name,
                qty=qty,
                duration_months=1,
                discount_percent=discount
            )
            if q_exec.get("status") == "SUCCESS":
                quo_res = q_exec["result"]
                tools_invoked.append("create_quotation")

        final_amount = quo_res["final_amount"] if quo_res else (monthly_rate * qty)
        quo_id = quo_res["quotation_id"] if quo_res else "DRAFT"

        return AgentExecutionResult(
            agent_id=self.agent_id,
            action_taken="QUOTATION_ISSUED",
            reply_message=(
                f"Penawaran Resmi Sewa Laptop ISKOM #{quo_id}:\n"
                f"- Unit: {qty}x {product_name} ({specs})\n"
                f"- Estimasi Total: Rp {final_amount:,}/bulan\n"
                f"- Ketersediaan: Unit ready di gudang.\n"
                f"Surat penawaran siap dikirim ke customer."
            ),
            status="SUCCESS",
            tools_called=tools_invoked,
            requires_approval=False
        )
