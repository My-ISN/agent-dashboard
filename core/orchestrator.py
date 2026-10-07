"""
ISKOM AI-OS Master Core Orchestrator
Kernel utama eksekusi instruksi:
USER -> AI CORE -> ROUTER -> AGENT -> KNOWLEDGE -> RESULT
"""

import time
from typing import Dict, Any, Optional
from core.models import UserMessage, CoreResponse, RouteDecision
from core.router import IntentRouter
from core.knowledge_loader import KnowledgeBase
from agents.base_agent import BaseAgent
from agents.sales_agent import SalesRentalAgent
from agents.inventory_agent import InventoryAgent
from agents.finance_agent import FinanceAgent
from agents.cs_agent import CustomerServiceAgent
from agents.kpi_agent import KPIExecutiveAgent


class CoreOrchestrator:
    """Master Orchestrator untuk mengoordinasi Router, Knowledge Base, dan Agen Spesialis"""

    def __init__(self, knowledge_dir: Optional[str] = None):
        self.knowledge = KnowledgeBase(knowledge_dir=knowledge_dir)
        self.router = IntentRouter()
        self.agents: Dict[str, BaseAgent] = {}
        self._register_default_agents()

    def _register_default_agents(self):
        """Pendaftaran seluruh agen spesialis ke dalam kernel dengan akses Knowledge Base"""
        agents_list = [
            SalesRentalAgent(knowledge_base=self.knowledge),
            InventoryAgent(knowledge_base=self.knowledge),
            FinanceAgent(knowledge_base=self.knowledge),
            CustomerServiceAgent(knowledge_base=self.knowledge),
            KPIExecutiveAgent(knowledge_base=self.knowledge)
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

        # 4. Delegasikan eksekusi ke agen dengan dukungan Knowledge Base
        execution_result = await agent.process(msg, route_decision)

        # 5. Hitung latency total pemrosesan
        latency_ms = int((time.time() - start_time) * 1000)

        # 6. Bentuk CoreResponse final
        return CoreResponse(
            user_input=user_text,
            routing=route_decision,
            execution=execution_result,
            latency_ms=latency_ms
        )
