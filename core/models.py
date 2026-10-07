"""
ISKOM AI-OS Core Data Models (Pydantic V2)
Standard Schema definitions for Messages, Routing, Decisions, and Execution Lifecycle.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import uuid


class UserMessage(BaseModel):
    """Representasi pesan input dari pengguna / staf / customer"""
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    user_id: Optional[str] = "user_guest"
    text: str = Field(..., description="Kalimat teks instruksi / pertanyaan")
    channel: str = Field(default="web_dashboard", description="web_dashboard, whatsapp, form_rental")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RouteDecision(BaseModel):
    """Hasil analisis Intent Router mengenai agen yang harus menangani"""
    agent_id: str = Field(..., description="ID agen pemenang, misal AGENT-SLS-01")
    agent_name: str = Field(..., description="Nama resmi agen")
    intent: str = Field(..., description="Kategori intent bisnis")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Skor kepastian 0.0 - 1.0")
    extracted_entities: Dict[str, Any] = Field(default_factory=dict, description="Entitas yang diekstrak (qty, unit, durasi, dll)")
    reasoning: str = Field(..., description="Alasan mengapa instruksi diarahkan ke agen ini")


class AgentExecutionResult(BaseModel):
    """Hasil pemrosesan oleh Agen Spesialis"""
    agent_id: str
    action_taken: str
    reply_message: str
    status: str = "SUCCESS"  # SUCCESS, PENDING_APPROVAL, BLOCKED_BY_RULE, ERROR
    tools_called: List[str] = Field(default_factory=list)
    requires_approval: bool = False
    approval_details: Optional[Dict[str, Any]] = None


class CoreResponse(BaseModel):
    """Respon lengkap yang dikembalikan oleh AI Core ke pemanggil"""
    transaction_id: str = Field(default_factory=lambda: f"TX-{uuid.uuid4().hex[:12].upper()}")
    user_input: str
    routing: RouteDecision
    execution: AgentExecutionResult
    latency_ms: int = Field(default=0, description="Waktu pemrosesan dalam milidetik")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
