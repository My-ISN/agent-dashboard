"""
ISKOM AI-OS Base Agent Class
Standard interface for all specialist agents with Knowledge Base access.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from core.models import UserMessage, AgentExecutionResult, RouteDecision


class BaseAgent(ABC):
    """Kelas dasar abstrak untuk seluruh agen spesialis"""
    
    agent_id: str
    name: str
    role_title: str
    capabilities: List[str]
    allowed_tools: List[str]
    knowledge: Any = None  # Reference to KnowledgeBase

    def __init__(self, knowledge_base: Any = None):
        if not hasattr(self, 'agent_id'):
            raise NotImplementedError("Setiap agent wajib memiliki agent_id")
        self.knowledge = knowledge_base

    @abstractmethod
    async def process(self, message: UserMessage, route_decision: RouteDecision) -> AgentExecutionResult:
        """Eksekusi tugas oleh agen spesialis berdasarkan intent dan entitas"""
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} [{self.agent_id}] - {self.name}>"
