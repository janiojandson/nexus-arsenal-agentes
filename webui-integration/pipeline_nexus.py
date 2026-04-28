"""
webui-integration/pipeline_nexus.py
🌉 NEXUS V4 — PIPELINE OPEN WEBUI (SSE Edition)

Compatível com Open WebUI Pipelines.
Intercepta mensagens do WebUI, envia para o endpoint SSE /api/v1/stream-command
do Nexus (Railway) e emite os eventos do cérebro em tempo real como tokens
incrementais no chat.

Fallback para /api/v1/command (REST síncrono) se o stream falhar.

title: Nexus CTO
author: Nexus (auto)
version: 4.0.0
license: MIT
"""

from __future__ import annotations

import os
import json
import time
import requests
import sseclient
import asyncio
from typing import List, Union, Generator, Iterator, Optional
from pydantic import BaseModel, Field


# ======================================================
# 🔗 CONFIGURAÇÃO
# ======================================================
DEFAULT_NEXUS_URL = os.environ.get(
    "NEXUS_BASE_URL", "https://nexus-v4.up.railway.app"
)
DEFAULT_NEXUS_KEY = os.environ.get("NEXUS_API_KEY", "")


# ======================================================
# 🧾 COMMAND MAP
# ======================================================
class CommandMapping:
    COMMANDS = {
        "!status": {"desc": "Status completo do sistema Nexus"},
        "!diagnostico": {"desc": "Diagnóstico do keyRotator e circuit breakers"},
        "!master": {"desc": "Força uso do modelo MESTRE (pago) na próxima tarefa"},
        "!memoria": {"desc": "Busca na memória persistente (GitHub + pgvector)"},
        "!deploy": {"desc": "Gatilha deploy no Railway"},
        "!tools": {"desc": "Lista todas as tools disponíveis"},
        "!git_sync": {"desc": "Sincroniza repositórios e memórias"},
        "!check_deploy": {"desc": "Verifica status do deploy no Railway"},
        "!help": {"desc": "Mostra este menu"},
    }

    @classmethod
    def is_command(cls, text: str) -> bool:
        return text.strip().startswith("!")

    @classmethod
    def list_commands(cls) -> str:
        lines = ["📋 **Comandos Disponíveis:**\n"]
        for cmd, info in cls.COMMANDS.items():
            lines.append(f"  • `{cmd}` — {info['desc']}")
        return "\n".join(lines)


# ======================================================
# 🚀 PIPELINE
# ======================================================
class Pipeline:
    class Valves(BaseModel):
        NEXUS_BASE_URL: str = Field(
            default=DEFAULT_NEXUS_URL,
            description="URL base do Nexus (Railway)",
        )
        NEXUS_API_KEY: str = Field(
            default=DEFAULT_NEXUS_KEY,
            description="API Key do Nexus (Bearer)",
        )
        NEXUS_CLIENT_ID: str = Field(
            default="webui-pipeline",
            description="Identificador do cliente WebUI",
        )
        STREAM_TIMEOUT: int = Field(
            default=180,
            description="Timeout total do stream em segundos",
        )
        USE_STREAM: bool = Field(
            default=True,
            description="Se False, usa REST síncrono /api/v1/command",
        )
        SHOW_PROGRESS: bool = Field(
            default=True,
            description="Mostra mensagens de progresso durante processamento",
        )

    def __init__(self) -> None:
        self.name = "Nexus CTO"
        self.valves = self.Valves()
        self.sse_client_id = None
        self._generate_client_id()

    # -------- ciclo de vida --------
    def _generate_client_id(self) -> None:
        """Gera um ID de cliente único para esta sessão"""
        import uuid
        self.sse_client_id = f"webui-{str(uuid.uuid4())[:8]}"

    def startup(self) -> None:
        """Inicializa o pipeline"""
        print(f"🚀 Nexus CTO Pipeline inicializado. Client ID: {self.sse_client_id}")
        self._check_connection()

    def shutdown(self) -> None:
        """Finaliza o pipeline"""
        print("👋 Nexus CTO Pipeline finalizado")

    def _check_connection(self) -> None:
        """Verifica se o Nexus está online"""
        try:
            url = f"{self.valves.NEXUS_BASE_URL}/api/v1/status"
            headers = {"Authorization": f"Bearer {self.valves.NEXUS_API_KEY}"}
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Nexus conectado: {data.get('status')} - v{data.get('version')}")
            else:
                print(f"⚠️ Nexus respondeu com status {response.status_code}")
        except Exception as e:
            print(f"❌ Não foi possível conectar ao Nexus: {str(e)}")

    # -------- processamento --------
    def process_user_message(self, user_message: str) -> Generator[str, None, None]:
        """Processa a mensagem do usuário e retorna a resposta do Nexus"""
        
        # Verifica se é um comando especial
        if CommandMapping.is_command(user_message):
            command = user_message.strip().split()[0]
            if command == "!help":
                yield CommandMapping.list_commands()
                return
        
        # Mostra mensagem de progresso
        if self.valves.SHOW_PROGRESS:
            yield "📥 Recebido. Iniciando análise MoE...\n\n"
        
        # Decide qual endpoint usar (stream ou síncrono)
        if self.valves.USE_STREAM:
            try:
                # Tenta usar o endpoint de streaming
                async_generator = self._process_stream(user_message)
                
                # Converte o async generator para um generator síncrono
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    for chunk in loop.run_until_complete(self._collect_async_gen(async_generator)):
                        yield chunk
                finally:
                    loop.close()
                    
            except Exception as e:
                # Fallback para o endpoint síncrono em caso de erro
                print(f"⚠️ Erro no stream, usando fallback síncrono: {str(e)}")
                yield f"⚠️ Stream falhou, usando endpoint síncrono...\n\n"
                yield from self._process_sync(user_message)
        else:
            # Usa diretamente o endpoint síncrono
            yield from self._process_sync(user_message)

    async def _collect_async_gen(self, gen):
        """Coleta resultados de um async generator"""
        result = []
        async for item in gen:
            result.append(item)
            yield item
        return result

    async def _process_stream(self, user_message: str) -> Generator[str, None, None]:
        """Processa a mensagem usando o endpoint de streaming (SSE)"""
        url = f"{self.valves.NEXUS_BASE_URL}/api/v1/stream-command"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.valves.NEXUS_API_KEY}",
            "Accept": "text/event-stream",
            "X-Client-ID": self.sse_client_id,
        }
        
        payload = {
            "prompt": user_message,
            "clientId": self.sse_client_id,
        }
        
        try:
            response = requests.post(
                url, 
                headers=headers, 
                json=payload,
                stream=True,
                timeout=self.valves.STREAM_TIMEOUT
            )
            
            if response.status_code != 200:
                error_msg = f"Erro no stream: {response.status_code} - {response.text}"
                print(f"❌ {error_msg}")
                yield f"❌ {error_msg}"
                return
            
            # Processa eventos SSE
            client = sseclient.SSEClient(response)
            accumulated_text = ""
            
            for event in client.events():
                if event.event == "progress":
                    # Eventos de progresso
                    try:
                        data = json.loads(event.data)
                        progress_msg = data.get("message", "")
                        if progress_msg and self.valves.SHOW_PROGRESS:
                            yield f"{progress_msg}\n\n"
                    except:
                        pass
                        
                elif event.event == "token":
                    # Tokens incrementais
                    token = event.data
                    accumulated_text += token
                    yield token
                    
                elif event.event == "error":
                    # Eventos de erro
                    try:
                        data = json.loads(event.data)
                        error_msg = data.get("error", "Erro desconhecido")
                        yield f"\n\n❌ Erro: {error_msg}"
                    except:
                        yield f"\n\n❌ Erro no processamento do stream"
                        
                elif event.event == "done":
                    # Evento de conclusão
                    break
                    
        except Exception as e:
            print(f"❌ Erro ao processar stream: {str(e)}")
            yield f"\n\n❌ Erro na conexão SSE: {str(e)}"

    def _process_sync(self, user_message: str) -> Generator[str, None, None]:
        """Processa a mensagem usando o endpoint síncrono"""
        url = f"{self.valves.NEXUS_BASE_URL}/api/v1/command"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.valves.NEXUS_API_KEY}",
            "X-Client-ID": self.sse_client_id,
        }
        
        payload = {
            "prompt": user_message,
            "clientId": self.sse_client_id,
        }
        
        if self.valves.SHOW_PROGRESS:
            yield "🧠 Processando via endpoint síncrono...\n\n"
        
        try:
            response = requests.post(
                url, 
                headers=headers, 
                json=payload,
                timeout=self.valves.STREAM_TIMEOUT
            )
            
            if response.status_code != 200:
                error_msg = f"Erro na API: {response.status_code} - {response.text}"
                print(f"❌ {error_msg}")
                yield f"❌ {error_msg}"
                return
            
            data = response.json()
            if data.get("success"):
                yield data.get("response", "Sem resposta do servidor")
            else:
                yield f"❌ Erro: {data.get('error', 'Erro desconhecido')}"
                
        except Exception as e:
            print(f"❌ Erro ao processar requisição síncrona: {str(e)}")
            yield f"❌ Erro na requisição: {str(e)}"

    # -------- utilitários --------
    def format_memory_for_webui(self, memory_file_path: str) -> str:
        """Formata um arquivo de memória do GitHub para importação no WebUI"""
        try:
            with open(memory_file_path, 'r') as f:
                content = f.read()
                
            # Extrai metadados e formata para WebUI
            title = os.path.basename(memory_file_path).replace('.md', '')
            formatted = f"# {title}\n\n{content}"
            
            return formatted
        except Exception as e:
            return f"Erro ao formatar memória: {str(e)}"

    def sync_memories_to_webui(self) -> str:
        """Sincroniza memórias do GitHub para o WebUI"""
        # Esta função seria implementada para exportar memórias
        # do GitHub para o formato de documentos do WebUI
        return "Função não implementada ainda"


# ======================================================
# 🔌 INTERFACE PARA OPEN WEBUI
# ======================================================
pipeline = Pipeline()

def on_chat_start():
    pipeline.startup()

def on_chat_end():
    pipeline.shutdown()

def on_message(user_message: str) -> Iterator[str]:
    for chunk in pipeline.process_user_message(user_message):
        yield chunk