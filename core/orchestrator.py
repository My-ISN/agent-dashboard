"""
ISKOM AI-OS Master Core Orchestrator
Kernel utama eksekusi instruksi:
USER -> AI CORE -> ROUTER -> AGENT -> KNOWLEDGE & TOOLS -> WORKFLOW -> LOGGER -> RESULT
"""

import time
from typing import Dict, Any, Optional
from core.models import UserMessage, CoreResponse, RouteDecision
from core.router import IntentRouter
from core.knowledge_loader import KnowledgeBase
from core.workflow_engine import WorkflowEngine, LeadState
from core.logger import ActivityLogger
from tools.business_tools import registry as tool_registry
from agents.base_agent import BaseAgent
from agents.sales_agent import SalesRentalAgent
from agents.inventory_agent import InventoryAgent
from agents.finance_agent import FinanceAgent
from agents.cs_agent import CustomerServiceAgent
from agents.kpi_agent import KPIExecutiveAgent


class CoreOrchestrator:
    """Master Orchestrator untuk mengoordinasi Router, Knowledge, Tools, Workflow, Logger, dan Agen"""

    def __init__(self, knowledge_dir: Optional[str] = None, log_dir: Optional[str] = None):
        self.knowledge = KnowledgeBase(knowledge_dir=knowledge_dir)
        self.tools = tool_registry
        self.workflows = WorkflowEngine()
        self.logger = ActivityLogger(log_dir=log_dir)
        self.router = IntentRouter()
        self.agents: Dict[str, BaseAgent] = {}
        self._register_default_agents()

    def _register_default_agents(self):
        """Pendaftaran seluruh agen spesialis ke dalam kernel"""
        agents_list = [
            SalesRentalAgent(knowledge_base=self.knowledge, tool_registry=self.tools),
            InventoryAgent(knowledge_base=self.knowledge, tool_registry=self.tools),
            FinanceAgent(knowledge_base=self.knowledge, tool_registry=self.tools),
            CustomerServiceAgent(knowledge_base=self.knowledge, tool_registry=self.tools),
            KPIExecutiveAgent(knowledge_base=self.knowledge, tool_registry=self.tools)
        ]
        for ag in agents_list:
            self.agents[ag.agent_id] = ag

    async def handle_request(self, user_text: str, user_id: str = "guest_user", channel: str = "web_dashboard") -> CoreResponse:
        """Memproses instruksi dari pengguna dari hulu ke hilir (End-to-End)"""
        start_time = time.time()

        # 1. Buat object pesan pengguna
        msg = UserMessage(user_id=user_id, text=user_text, channel=channel)

        # 2. Routing semantik (Tentukan agen penanggung jawab)
        route_decision = self.router.route(msg)

        # 3. Ambil agen spesialis yang terpilih
        agent = self.agents.get(route_decision.agent_id)
        if not agent:
            agent = self.agents["AGENT-SLS-01"]

        # 4. Delegasikan eksekusi ke agen
        execution_result = await agent.process(msg, route_decision)

        # 5. Sinkronkan ke Workflow Engine jika berkaitan dengan sewa
        if route_decision.intent == "RENTAL_SALES_INQUIRY":
            wf = self.workflows.start_lead_workflow(customer_name=user_id)
            wf.transition_to(LeadState.QUALIFIED, actor=agent.agent_id, notes="Kualifikasi kebutuhan sewa selesai")
            if execution_result.status == "PENDING_APPROVAL":
                wf.transition_to(LeadState.NEGOTIATION, actor=agent.agent_id, notes="Negosiasi diskon khusus")
                wf.transition_to(LeadState.PENDING_APPROVAL, actor=agent.agent_id, notes="Menunggu verifikasi Owner")
            elif execution_result.status == "SUCCESS":
                wf.transition_to(LeadState.QUOTATION_SENT, actor=agent.agent_id, notes="Quotation resmi diterbitkan")

        # 6. Hitung latency total pemrosesan
        latency_ms = int((time.time() - start_time) * 1000)

        # 7. AUDIT TRAIL LOGGING (10 Parameter Wajib)
        self.logger.log_action(
            user=user_id,
            agent_id=agent.agent_id,
            agent_name=agent.name,
            user_input=user_text,
            keputusan=f"{route_decision.intent} ({route_decision.confidence*100:.0f}%)",
            tools_called=execution_result.tools_called,
            action=execution_result.action_taken,
            result=execution_result.reply_message[:150],
            error=None,
            approval_required=execution_result.requires_approval,
            approval_details=execution_result.approval_details,
            latency_ms=latency_ms
        )

        # 8. Bentuk CoreResponse final
        return CoreResponse(
            user_input=user_text,
            routing=route_decision,
            execution=execution_result,
            latency_ms=latency_ms
        )
