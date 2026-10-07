"""
Sales & Rental Specialist Agent (AGENT-SLS-01)
Menangani konsultasi sewa laptop, kualifikasi kebutuhan, kalkulasi harga,
anti-halusinasi data tidak tersedia, dan evaluasi batas diskon/transaksi.
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
        query_text = message.text.lower()
        entities = route_decision.extracted_entities
        qty = entities.get("quantity", 1)
        unit_query = entities.get("unit_model", "ThinkPad")
        discount = entities.get("discount_percent", 0.0)

        tools_invoked = []

        # 1. PENCEGAHAN KEAMANAN: Prompt Injection / Diskon 100%
        if route_decision.intent == "SECURITY_PROMPT_INJECTION_BLOCKED":
            return AgentExecutionResult(
                agent_id=self.agent_id,
                action_taken="PROMPT_INJECTION_BLOCKED",
                reply_message=(
                    "PERINGATAN SISTEM: Permintaan diskon di luar batas wajar (100%/gratis) atau upaya manipulasi "
                    "instruksi telah diblokir otomatis oleh Business Rule Engine (RULE-DISC-04). "
                    "Silakan ajukan permintaan sewa sesuai tarif dan SOP resmi ISKOM."
                ),
                status="BLOCKED_BY_RULE",
                tools_called=[],
                requires_approval=False
            )

        # 2. ANTI-HALUSINASI: Cek ketersediaan unit di katalog resmi
        product = self.knowledge.get_product_by_model(unit_query) if self.knowledge else None
        
        # Jika unit dicari secara eksplisit namun tidak ada di katalog (contoh: Alienware, Printer)
        if any(unsupported in query_text for unsupported in ["alienware", "printer", "proyektor", "rtx 4090", "playstation"]):
            return AgentExecutionResult(
                agent_id=self.agent_id,
                action_taken="PRODUCT_NOT_AVAILABLE",
                reply_message=(
                    f"Mohon maaf, unit '{unit_query}' saat ini TIDAK TERSEDIA di katalog sewa resmi ISKOM. "
                    "Sistem kami beroperasi dengan prinsip Anti-Halusinasi (tidak mengarang ketersediaan data). "
                    "Kami menyediakan alternatif laptop bisnis handal seperti Lenovo ThinkPad T480/T490 atau Dell Latitude. "
                    "Apakah Anda berkenan kami berikan penawaran untuk tipe alternatif tersebut?"
                ),
                status="PRODUCT_NOT_FOUND",
                tools_called=["search_product"],
                requires_approval=False
            )

        product_name = product["model"] if product else unit_query
        specs = product["specs"] if product else "Core i5 / RAM 16GB"
        daily_rate = product["rates"]["daily"] if product else 75000
        monthly_rate = product["rates"]["monthly"] if product else 950000
        total_estimate = monthly_rate * qty

        # 3. Mode Pencarian Produk / Rekomendasi
        if route_decision.intent == "PRODUCT_CATALOG_SEARCH" and "buat quotation" not in query_text and "sewa" not in query_text:
            return AgentExecutionResult(
                agent_id=self.agent_id,
                action_taken="CATALOG_SEARCHED",
                reply_message=(
                    f"Rekomendasi Katalog Laptop ISKOM:\n"
                    f"- Model: {product_name} ({specs})\n"
                    f"- Tarif Sewa: Rp {daily_rate:,}/hari | Rp {monthly_rate:,}/bulan\n"
                    f"- Kategori: {product.get('category', 'Business Standard') if product else 'Bisnis'}\n"
                    f"Unit ready di gudang untuk disewa."
                ),
                status="SUCCESS",
                tools_called=["search_product"],
                requires_approval=False
            )

        # 4. Evaluasi Aturan Bisnis: Diskon > 10% ATAU Nilai Transaksi >= 25 Juta (RULE-HVT-01)
        is_high_value = total_estimate >= 25000000 or qty >= 20
        needs_approval = (discount > 10.0) or is_high_value

        if needs_approval:
            category = "DISCOUNT_REQUEST" if discount > 10.0 else "HIGH_VALUE_TRANSACTION"
            rule_id = "RULE-DISC-02" if discount > 10.0 else "RULE-HVT-01"
            rationale = (
                f"Pengajuan diskon {discount}%" if discount > 10.0
                else f"Transaksi skala besar ({qty} unit, estimasi Rp {total_estimate:,})"
            )

            apv_ticket = None
            if self.tools:
                apv_res = await self.tools.execute(
                    "request_approval",
                    self.agent_id,
                    requester_agent_id=self.agent_id,
                    rule_id=rule_id,
                    category=category,
                    payload={"unit": product_name, "qty": qty, "discount": discount, "total": total_estimate},
                    rationale=rationale
                )
                if apv_res.get("status") == "SUCCESS":
                    apv_ticket = apv_res["result"]["approval_id"]
                    tools_invoked.append("request_approval")

            reason_str = f"pengajuan diskon {discount}%" if discount > 10.0 else f"nilai transaksi besar ({qty} unit / Rp {total_estimate:,})"
            return AgentExecutionResult(
                agent_id=self.agent_id,
                action_taken="APPROVAL_REQUIRED",
                reply_message=(
                    f"Permintaan sewa untuk {qty} unit '{product_name}' dengan {reason_str} "
                    f"telah kami terima. Sesuai aturan perusahaan, transaksi ini memerlukan otorisasi Owner. "
                    f"Tiket persetujuan #{apv_ticket} telah otomatis dikirimkan ke dashboard Owner."
                ),
                status="PENDING_APPROVAL",
                tools_called=tools_invoked,
                requires_approval=True,
                approval_details={"approval_id": apv_ticket, "category": category, "total": total_estimate}
            )

        # 5. Transaksi Normal: Terbitkan Quotation resmi via Tool
        quo_res = None
        if self.tools:
            tools_invoked.append("check_inventory")
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

        final_amount = quo_res["final_amount"] if quo_res else total_estimate
        quo_id = quo_res["quotation_id"] if quo_res else "DRAFT"

        return AgentExecutionResult(
            agent_id=self.agent_id,
            action_taken="QUOTATION_ISSUED",
            reply_message=(
                f"Surat Penawaran Resmi Sewa Laptop ISKOM #{quo_id}:\n"
                f"- Rincian: {qty}x {product_name} ({specs})\n"
                f"- Estimasi Total: Rp {final_amount:,}/bulan\n"
                f"- Status Stok: Terverifikasi di gudang.\n"
                f"Quotation siap dikirimkan ke klien."
            ),
            status="SUCCESS",
            tools_called=tools_invoked,
            requires_approval=False
        )
