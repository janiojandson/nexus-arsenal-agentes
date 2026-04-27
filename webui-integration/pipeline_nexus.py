"""
webui-integration/pipeline_nexus.py
🌉 NEXUS V3 — PIPELINE OPEN WEBUI
Transforma intenções do chat em ações de infraestrutura no GitHub e Railway.
Compatível com Open WebUI Pipelines.
"""

import os
import json
import requests
from typing import List, Optional, Generator, AsyncGenerator
from pydantic import BaseModel


# ======================================================
# 🔗 CONFIGURAÇÃO DA CONEXÃO COM O NEXUS (Railway)
# ======================================================
NEXUS_BASE_URL = os.environ.get("NEXUS_BASE_URL", "https://nexus-v3.up.railway.app")
NEXUS_API_KEY = os.environ.get("NEXUS_API_KEY", "")
NEXUS_CLIENT_ID = os.environ.get("NEXUS_CLIENT_ID", "webui-pipeline")

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {NEXUS_API_KEY}"
}


# ======================================================
# 📋 SCHEMAS
# ======================================================
class PipelineConfig(BaseModel):
    nexus_url: str = NEXUS_BASE_URL
    nexus_api_key: str = NEXUS_API_KEY


class CommandMapping:
    """Mapeia comandos do WebUI para ações do Nexus."""
    
    COMMANDS = {
        "!git_sync": {
            "description": "Sincroniza memórias e código do Arsenal",
            "action": "git_sync",
            "task_type": "agent_task"
        },
        "!check_deploy": {
            "description": "Verifica status do deploy no Railway",
            "action": "check_deploy",
            "task_type": "fast_task"
        },
        "!status": {
            "description": "Status completo do sistema Nexus",
            "action": "status",
            "task_type": "fast_task"
        },
        "!diagnostico": {
            "description": "Diagnóstico detalhado do sistema",
            "action": "diagnostico",
            "task_type": "fast_task"
        },
        "!master": {
            "description": "Força uso do modelo Mestre (pago)",
            "action": "master",
            "task_type": "coding_heavy"
        },
        "!memoria": {
            "description": "Busca na memória persistente do Nexus",
            "action": "memoria",
            "task_type": "fast_task"
        },
        "!deploy": {
            "description": "Executa deploy no Railway",
            "action": "deploy",
            "task_type": "agent_task"
        },
        "!tools": {
            "description": "Lista todas as tools disponíveis",
            "action": "tools",
            "task_type": "fast_task"
        }
    }

    @classmethod
    def is_command(cls, text: str) -> bool:
        return text.strip().startswith("!")

    @classmethod
    def get_command(cls, text: str) -> Optional[dict]:
        cmd = text.strip().split(" ")[0].lower()
        return cls.COMMANDS.get(cmd)

    @classmethod
    def list_commands(cls) -> str:
        lines = ["📋 **Comandos Disponíveis:**\n"]
        for cmd, info in cls.COMMANDS.items():
            lines.append(f"  • `{cmd}` — {info['description']}")
        return "\n".join(lines)


# ======================================================
# 🌉 CLIENTE DA API NEXUS
# ======================================================
class NexusClient:
    """Cliente para comunicação com o Nexus no Railway."""

    def __init__(self, base_url: str = NEXUS_BASE_URL, api_key: str = NEXUS_API_KEY):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

    def _request(self, method: str, endpoint: str, data: dict = None) -> dict:
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.request(
                method=method,
                url=url,
                json=data,
                headers=self.headers,
                timeout=120
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            return {"type": "error", "error": "Timeout ao conectar com o Nexus. O modelo pode estar processando (Modal tem alta latência)."}
        except requests.exceptions.ConnectionError:
            return {"type": "error", "error": "Nexus offline. Verifique o deploy no Railway."}
        except requests.exceptions.HTTPError as e:
            return {"type": "error", "error": f"Erro HTTP {e.response.status_code}: {e.response.text[:200]}"}
        except Exception as e:
            return {"type": "error", "error": str(e)}

    def send_command(self, command: str, task_type: str = None, metadata: dict = None) -> dict:
        payload = {
            "command": command,
            "clientId": NEXUS_CLIENT_ID,
            "taskType": task_type,
            "metadata": metadata or {}
        }
        return self._request("POST", "/api/v1/command", payload)

    def send_command_stream(self, command: str, task_type: str = None, metadata: dict = None):
        """Envia comando e recebe resposta via SSE stream."""
        payload = {
            "command": command,
            "taskType": task_type,
            "metadata": metadata or {}
        }
        url = f"{self.base_url}/api/v1/command/stream"
        try:
            response = requests.post(
                url,
                json=payload,
                headers=self.headers,
                stream=True,
                timeout=120
            )
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    line = line.decode("utf-8")
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            yield data
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            yield {"type": "error", "error": str(e)}

    def get_status(self) -> dict:
        return self._request("GET", "/api/v1/status")

    def get_diagnostico(self) -> dict:
        return self._request("GET", "/api/v1/diagnostico")

    def get_tools(self) -> dict:
        return self._request("GET", "/api/v1/tools")

    def search_memory(self, query: str, limit: int = 5) -> dict:
        return self._request("GET", f"/api/v1/memorias?query={query}&limite={limit}")


# ======================================================
# 🔧 PIPELINE PRINCIPAL (Open WebUI Compatible)
# ======================================================
class Pipeline:
    """Pipeline Nexus para Open WebUI — Transforma chat em infraestrutura."""

    def __init__(self):
        self.name = "Nexus V3 Pipeline"
        self.client = NexusClient()
        self.command_mapping = CommandMapping()

    async def on_startup(self):
        print(f"🚀 [Nexus Pipeline] Inicializado. Conectando a {self.client.base_url}")
        status = self.client.get_status()
        if status.get("status") == "OPERACIONAL":
            print("✅ [Nexus Pipeline] Conexão com Nexus estabelecida.")
        else:
            print(f"⚠️ [Nexus Pipeline] Nexus pode estar offline: {status}")

    async def on_shutdown(self):
        print("👋 [Nexus Pipeline] Desligando...")

    async def pipe(
        self,
        user_message: str,
        model_id: str,
        messages: List[dict],
        body: dict
    ) -> AsyncGenerator[str, None]:
        """
        Processa mensagem do usuário. Se for comando, executa ação.
        Se for pergunta normal, roteia pelo Nexus.
        """
        text = user_message.strip()

        # Verificar se é um comando especial
        if self.command_mapping.is_command(text):
            cmd_info = self.command_mapping.get_command(text)
            if cmd_info:
                yield from self._execute_command(cmd_info, text)
                return
            else:
                yield f"❌ Comando não reconhecido.\n\n{self.command_mapping.list_commands()}"
                return

        # Verificar se é pergunta sobre memória
        if any(kw in text.lower() for kw in ["memória", "memoria", "lembra", "já fizemos", "histórico"]):
            memory_result = self.client.search_memory(text)
            if memory_result.get("data"):
                context = memory_result["data"]
                # Envia com contexto de memória
                result = self.client.send_command(
                    f"[CONTEXTO DE MEMÓRIA]: {context}\n\n[PERGUNTA]: {text}",
                    task_type="fast_task"
                )
            else:
                result = self.client.send_command(text)
        else:
            # Roteamento normal pelo Nexus
            result = self.client.send_command(text)

        if result.get("type") == "error":
            yield f"🚨 Erro: {result['error']}"
        elif result.get("data"):
            data = result["data"]
            if isinstance(data, dict) and data.get("content"):
                yield data["content"]
            else:
                yield json.dumps(data, indent=2, ensure_ascii=False)
        else:
            yield str(result)

    def _execute_command(self, cmd_info: dict, full_text: str) -> Generator[str, None, None]:
        """Executa um comando mapeado."""
        action = cmd_info["action"]
        args = full_text.split(" ", 1)[1] if " " in full_text else ""

        if action == "status":
            result = self.client.get_status()
            yield f"📊 **Status do Nexus:**\n```json\n{json.dumps(result, indent=2, ensure_ascii=False)}\n```"

        elif action == "diagnostico":
            result = self.client.get_diagnostico()
            yield f"🔍 **Diagnóstico Completo:**\n```json\n{json.dumps(result, indent=2, ensure_ascii=False)}\n```"

        elif action == "tools":
            result = self.client.get_tools()
            tools = result.get("data", [])
            lines = ["🔧 **Tools Disponíveis:**\n"]
            for tool in tools:
                fn = tool.get("function", {})
                lines.append(f"  • `{fn.get('name')}` — {fn.get('description')}")
            yield "\n".join(lines)

        elif action == "memoria":
            if not args:
                yield "🔍 Use: `!memoria [termo de busca]`"
                return
            result = self.client.search_memory(args)
            if result.get("data"):
                yield f"🧠 **Memórias encontradas:**\n\n{result['data']}"
            else:
                yield "📭 Nenhuma memória encontrada para este termo."

        elif action == "master":
            result = self.client.send_command(
                args or "Mestre invocado. Às ordens.",
                task_type="coding_heavy",
                metadata={"useMaster": True}
            )
            if result.get("data", {}).get("content"):
                yield result["data"]["content"]
            else:
                yield json.dumps(result, indent=2, ensure_ascii=False)

        elif action == "git_sync":
            yield "🔄 Sincronizando memórias do Arsenal..."
            result = self.client.send_command("!git_sync", task_type="agent_task")
            yield f"✅ Sincronização concluída:\n{json.dumps(result, indent=2, ensure_ascii=False)}"

        elif action == "check_deploy":
            result = self.client.get_status()
            yield f"🚀 **Status do Deploy:**\n```json\n{json.dumps(result, indent=2, ensure_ascii=False)}\n```"

        elif action == "deploy":
            yield "🚀 Iniciando deploy no Railway..."
            result = self.client.send_command("!deploy", task_type="agent_task")
            yield f"✅ Deploy iniciado:\n{json.dumps(result, indent=2, ensure_ascii=False)}"

        else:
            yield f"❌ Ação não implementada: {action}"


# ======================================================
# 📚 SINCRONIZAÇÃO DE MEMÓRIA VISUAL
# ======================================================
def formatar_diario_para_webui(diario_markdown: str) -> dict:
    """
    Formata o Diário de Bordo (Markdown do GitHub) para ser exibido
    como 'Documento de Conhecimento' no Open WebUI.
    """
    return {
        "title": "📓 Diário de Bordo — Nexus V3",
        "content": diario_markdown,
        "type": "knowledge_document",
        "source": "github://nexus-arsenal-agentes/memorias/diario_de_bordo.md",
        "timestamp": __import__("datetime").datetime.now().isoformat()
    }


def formatar_alertas_para_webui(alertas: list) -> dict:
    """Formata alertas de instabilidade para exibição no WebUI."""
    return {
        "title": "🚨 Alertas de Instabilidade — Modelos",
        "content": json.dumps(alertas, indent=2, ensure_ascii=False),
        "type": "alert_document",
        "source": "github://nexus-arsenal-agentes/memorias/alertas/"
    }


# ======================================================
# 🏁 EXPORTS
# ======================================================
__all__ = [
    "Pipeline",
    "NexusClient",
    "CommandMapping",
    "formatar_diario_para_webui",
    "formatar_alertas_para_webui"
]
