"""
ISKOM AI-OS Workflow Engine & State Machine
Mengatur siklus hidup proses bisnis sewa (Lead -> Quotation -> Approval -> Won/Lost)
dengan validasi transisi status yang ketat dan audit trail.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
import datetime
import uuid


class LeadState(str, Enum):
    NEW_LEAD = "NEW_LEAD"
    QUALIFIED = "QUALIFIED"
    FOLLOW_UP = "FOLLOW_UP"
    QUOTATION_SENT = "QUOTATION_SENT"
    NEGOTIATION = "NEGOTIATION"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    CLOSING = "CLOSING"
    WON = "WON"
    LOST = "LOST"


class InvalidStateTransition(Exception):
    """Exception jika terjadi lompatan status yang melanggar SOP bisnis"""
    pass


class WorkflowInstance:
    """Representasi satu alur kerja transaksi sewa aktif"""

    # Definisi Transisi yang Diperbolehkan (State Machine Transition Graph)
    ALLOWED_TRANSITIONS = {
        LeadState.NEW_LEAD: [LeadState.QUALIFIED, LeadState.LOST],
        LeadState.QUALIFIED: [LeadState.FOLLOW_UP, LeadState.QUOTATION_SENT, LeadState.NEGOTIATION, LeadState.LOST],
        LeadState.FOLLOW_UP: [LeadState.QUOTATION_SENT, LeadState.LOST],
        LeadState.QUOTATION_SENT: [LeadState.NEGOTIATION, LeadState.CLOSING, LeadState.LOST],
        LeadState.NEGOTIATION: [LeadState.PENDING_APPROVAL, LeadState.CLOSING, LeadState.LOST],
        LeadState.PENDING_APPROVAL: [LeadState.CLOSING, LeadState.NEGOTIATION, LeadState.LOST],
        LeadState.CLOSING: [LeadState.WON, LeadState.LOST],
        LeadState.WON: [],   # Terminal State
        LeadState.LOST: []   # Terminal State
    }

    def __init__(self, workflow_id: str, customer_name: str, initial_state: LeadState = LeadState.NEW_LEAD):
        self.workflow_id = workflow_id
        self.customer_name = customer_name
        self.current_state = initial_state
        self.history: List[Dict[str, Any]] = [
            {
                "from_state": None,
                "to_state": initial_state.value,
                "actor": "SYSTEM",
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "notes": "Inisialisasi workflow lead baru"
            }
        ]

    def can_transition_to(self, target_state: LeadState) -> bool:
        """Mengecek apakah transisi ke target_state sah menurut aturan mesin status"""
        allowed = self.ALLOWED_TRANSITIONS.get(self.current_state, [])
        return target_state in allowed

    def transition_to(self, target_state: LeadState, actor: str, notes: str = "", metadata: Optional[Dict[str, Any]] = None):
        """Mengeksekusi perpindahan status dengan validasi guardrail"""
        if not self.can_transition_to(target_state):
            raise InvalidStateTransition(
                f"Lompatan status TIDAK SAH: Dari '{self.current_state.value}' ke '{target_state.value}' "
                f"tidak diizinkan oleh SOP alur kerja ISKOM."
            )

        prev_state = self.current_state
        self.current_state = target_state

        history_entry = {
            "from_state": prev_state.value,
            "to_state": target_state.value,
            "actor": actor,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "notes": notes,
            "metadata": metadata or {}
        }
        self.history.append(history_entry)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "customer_name": self.customer_name,
            "current_state": self.current_state.value,
            "steps_count": len(self.history),
            "history": self.history
        }


class WorkflowEngine:
    """Manajer pengelola seluruh workflow aktif di ISKOM AI-OS"""

    def __init__(self):
        self.instances: Dict[str, WorkflowInstance] = {}

    def start_lead_workflow(self, customer_name: str, workflow_id: Optional[str] = None) -> WorkflowInstance:
        """Membuat instance alur kerja baru untuk prospek yang masuk"""
        wf_id = workflow_id or f"WF-LEAD-{uuid.uuid4().hex[:6].upper()}"
        instance = WorkflowInstance(workflow_id=wf_id, customer_name=customer_name)
        self.instances[wf_id] = instance
        return instance

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowInstance]:
        """Mengambil instance workflow berdasarkan ID"""
        return self.instances.get(workflow_id)

    def list_active_workflows(self) -> List[Dict[str, Any]]:
        """Melihat ringkasan seluruh workflow yang sedang berjalan"""
        return [
            {
                "workflow_id": wf.workflow_id,
                "customer": wf.customer_name,
                "state": wf.current_state.value,
                "steps": len(wf.history)
            }
            for wf in self.instances.values()
        ]
