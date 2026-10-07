"""
ISKOM AI-OS Tool Registry & RBAC Guard
Pusat registrasi fungsi/alat yang dapat digunakan oleh Agen AI.
Agen DILARANG mengakses database secara mentah tanpa melalui Tool berizin.
"""

from typing import Dict, Any, Callable, List, Optional
import inspect
import datetime


class ToolPermissionDenied(Exception):
    """Exception jika agen mencoba memanggil tool di luar wewenangnya"""
    pass


class ToolDefinition:
    """Metadatata dan fungsi eksekusi dari satu Tool"""
    def __init__(
        self,
        name: str,
        description: str,
        func: Callable,
        allowed_agents: List[str],
        requires_approval: bool = False
    ):
        self.name = name
        self.description = description
        self.func = func
        self.allowed_agents = allowed_agents
        self.requires_approval = requires_approval

    def is_allowed_for(self, agent_id: str) -> bool:
        """Cek apakah agen memiliki wewenang memanggil tool ini"""
        return ("*" in self.allowed_agents) or (agent_id in self.allowed_agents)


class ToolRegistry:
    """Registry pusat untuk mendaftarkan dan mengeksekusi tools dengan RBAC Guard"""

    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {}
        self.execution_logs: List[Dict[str, Any]] = []

    def register(
        self,
        name: str,
        description: str,
        allowed_agents: List[str],
        requires_approval: bool = False
    ):
        """Decorator untuk mendaftarkan fungsi Python sebagai AI Tool"""
        def decorator(func: Callable):
            tool_def = ToolDefinition(
                name=name,
                description=description,
                func=func,
                allowed_agents=allowed_agents,
                requires_approval=requires_approval
            )
            self.tools[name] = tool_def
            return func
        return decorator

    def list_tools_for_agent(self, agent_id: str) -> List[Dict[str, Any]]:
        """Melihat daftar seluruh tool yang boleh dipanggil oleh agen tertentu"""
        return [
            {
                "name": t.name,
                "description": t.description,
                "requires_approval": t.requires_approval
            }
            for t in self.tools.values()
            if t.is_allowed_for(agent_id)
        ]

    async def execute(self, tool_name: str, caller_agent_id: str, **kwargs) -> Dict[str, Any]:
        """
        Mengeksekusi tool dengan pengecekan RBAC Guard:
        1. Validasi keberadaan tool di registry
        2. Validasi apakah caller_agent_id diizinkan
        3. Eksekusi fungsi dan catat log audit
        """
        timestamp = datetime.datetime.utcnow().isoformat()

        # 1. Cek keberadaan tool
        if tool_name not in self.tools:
            log_entry = {
                "timestamp": timestamp,
                "tool": tool_name,
                "agent_id": caller_agent_id,
                "status": "NOT_FOUND",
                "error": f"Tool '{tool_name}' tidak terdaftar di registry"
            }
            self.execution_logs.append(log_entry)
            return {"status": "ERROR", "message": log_entry["error"]}

        tool = self.tools[tool_name]

        # 2. RBAC Guard: Cek wewenang agen
        if not tool.is_allowed_for(caller_agent_id):
            log_entry = {
                "timestamp": timestamp,
                "tool": tool_name,
                "agent_id": caller_agent_id,
                "status": "PERMISSION_DENIED",
                "error": f"Agen '{caller_agent_id}' DILARANG memanggil tool '{tool_name}' (Di luar batas wewenang)"
            }
            self.execution_logs.append(log_entry)
            return {
                "status": "PERMISSION_DENIED",
                "message": log_entry["error"],
                "allowed_agents": tool.allowed_agents
            }

        # 3. Eksekusi fungsi (sinkron atau asinkron)
        try:
            if inspect.iscoroutinefunction(tool.func):
                result = await tool.func(**kwargs)
            else:
                result = tool.func(**kwargs)

            log_entry = {
                "timestamp": timestamp,
                "tool": tool_name,
                "agent_id": caller_agent_id,
                "status": "SUCCESS",
                "params": kwargs,
                "result": result
            }
            self.execution_logs.append(log_entry)

            return {
                "status": "SUCCESS",
                "tool": tool_name,
                "result": result
            }

        except Exception as e:
            log_entry = {
                "timestamp": timestamp,
                "tool": tool_name,
                "agent_id": caller_agent_id,
                "status": "EXECUTION_ERROR",
                "error": str(e)
            }
            self.execution_logs.append(log_entry)
            return {"status": "ERROR", "message": f"Gagal mengeksekusi tool: {str(e)}"}
