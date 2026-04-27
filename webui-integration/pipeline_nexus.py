"""
webui-integration/pipeline_nexus.py
🌉 NEXUS V3 — PIPELINE OPEN WEBUI (SSE Edition)

Compatível com Open WebUI Pipelines.
Intercepta mensagens do WebUI, envia para o endpoint SSE /api/v1/stream-command
do Nexus (Railway) e emite os eventos do cérebro em tempo real como tokens
incrementais no chat.

Fallback para /api/v1/command (REST síncrono) se o stream falhar.

title: Nexus CTO
author: Nexus (auto)
version: 3.0.0
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
    "NEXUS_BASE_URL", "https://nexus-v3.up.railway.app"
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

    def __init__(self) -> None:
        self.name = "Nexus CTO"
        self.valves = self.Valves()
        self.sse_client_id = None

    # -------- ciclo de vida --------
    async def on_startup(self) -> None:
        print(f"🌉 [Nexus Pipeline] Conectando ao Nexus em {self.valves.NEXUS_BASE_URL}")
        if not self.valves.USE_STREAM:
            print("⚠️ [Nexus Pipeline] Modo stream desativado, usando REST síncrono")

    async def on_shutdown(self) -> None:
        print("🔌 [Nexus Pipeline] Desconectando do Nexus")

    # -------- processamento --------
    async def process(
        self, prompt: str, system_prompt: str = ""
    ) -> Union[str, Generator[str, None, None]]:
        """
        Processa um prompt através do Nexus Engine
        """
        # Verificar se é um comando especial
        if prompt.strip().lower() == "!help":
            return CommandMapping.list_commands()

        # Usar SSE para streaming em tempo real
        if self.valves.USE_STREAM:
            try:
                return self._process_stream(prompt, system_prompt)
            except Exception as e:
                print(f"❌ [Nexus Pipeline] Erro no stream: {e}")
                print("⚠️ [Nexus Pipeline] Fallback para REST síncrono")
                # Fallback para REST síncrono
                return await self._process_sync(prompt, system_prompt)
        else:
            # Usar REST síncrono
            return await self._process_sync(prompt, system_prompt)

    async def _process_sync(self, prompt: str, system_prompt: str) -> str:
        """
        Processa um prompt de forma síncrona via REST
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.valves.NEXUS_API_KEY}",
        }

        payload = {
            "prompt": prompt,
            "system": system_prompt,
            "client_id": self.valves.NEXUS_CLIENT_ID,
        }

        url = f"{self.valves.NEXUS_BASE_URL}/api/v1/command"
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result.get("resposta", "Erro: Resposta vazia do Nexus")
        except requests.exceptions.RequestException as e:
            return f"❌ Erro ao conectar com o Nexus: {str(e)}"

    def _process_stream(self, prompt: str, system_prompt: str) -> Generator[str, None, None]:
        """
        Processa um prompt via streaming SSE
        Retorna um gerador que emite tokens incrementalmente
        """
        # Estabelecer conexão SSE primeiro
        if not self.sse_client_id:
            self._establish_sse_connection()
        
        # Enviar comando para processamento via SSE
        self._send_sse_command(prompt, system_prompt)
        
        # Retornar gerador que consome eventos SSE
        return self._consume_sse_events()

    def _establish_sse_connection(self) -> None:
        """
        Estabelece uma conexão SSE com o Nexus
        """
        headers = {
            "Accept": "text/event-stream",
            "Cache-Control": "no-cache",
            "Authorization": f"Bearer {self.valves.NEXUS_API_KEY}",
        }
        
        url = f"{self.valves.NEXUS_BASE_URL}/api/v1/stream-command"
        
        # Iniciar conexão SSE em uma thread separada
        def connect_sse():
            try:
                response = requests.get(url, headers=headers, stream=True)
                response.raise_for_status()
                
                client = sseclient.SSEClient(response)
                
                # Esperar pelo evento de conexão para obter o clientId
                for event in client.events():
                    if event.event == "conectado":
                        data = json.loads(event.data)
                        self.sse_client_id = data.get("clientId")
                        print(f"🔌 [Nexus Pipeline] Conexão SSE estabelecida, ID: {self.sse_client_id}")
                        break
                
                # Manter a conexão aberta para eventos futuros
                self.sse_client = client
                
            except Exception as e:
                print(f"❌ [Nexus Pipeline] Erro ao estabelecer conexão SSE: {e}")
                self.sse_client_id = None
                raise
        
        # Iniciar em uma thread separada
        import threading
        thread = threading.Thread(target=connect_sse)
        thread.daemon = True
        thread.start()
        
        # Esperar até que a conexão seja estabelecida ou timeout
        timeout = 10
        start_time = time.time()
        while not self.sse_client_id and time.time() - start_time < timeout:
            time.sleep(0.1)
        
        if not self.sse_client_id:
            raise Exception("Timeout ao estabelecer conexão SSE")

    def _send_sse_command(self, prompt: str, system_prompt: str) -> None:
        """
        Envia um comando para processamento via SSE
        """
        if not self.sse_client_id:
            raise Exception("Conexão SSE não estabelecida")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.valves.NEXUS_API_KEY}",
        }
        
        payload = {
            "prompt": prompt,
            "system": system_prompt,
            "clientId": self.sse_client_id,
        }
        
        url = f"{self.valves.NEXUS_BASE_URL}/api/v1/stream-command"
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"❌ [Nexus Pipeline] Erro ao enviar comando SSE: {e}")
            raise

    def _consume_sse_events(self) -> Generator[str, None, None]:
        """
        Consome eventos SSE e os emite como tokens incrementais
        """
        if not hasattr(self, 'sse_client') or not self.sse_client:
            raise Exception("Cliente SSE não inicializado")
        
        # Processar eventos SSE
        start_time = time.time()
        timeout = self.valves.STREAM_TIMEOUT
        
        try:
            for event in self.sse_client.events():
                # Verificar timeout
                if time.time() - start_time > timeout:
                    yield "\n\n⏱️ Timeout: Processamento excedeu o limite de tempo"
                    break
                
                # Processar evento
                if event.event == "resposta":
                    data = json.loads(event.data)
                    chunk = data.get("chunk", "")
                    yield chunk
                
                elif event.event == "status":
                    data = json.loads(event.data)
                    mensagem = data.get("mensagem", "")
                    yield f"\n{mensagem}\n"
                
                elif event.event == "erro":
                    data = json.loads(event.data)
                    mensagem = data.get("mensagem", "")
                    yield f"\n❌ {mensagem}\n"
                
                elif event.event == "concluido":
                    # Evento de conclusão, encerrar o gerador
                    break
                
                # Ignorar outros eventos (heartbeat, etc)
        
        except Exception as e:
            yield f"\n\n❌ Erro ao processar stream: {str(e)}"
        
        finally:
            # Não fechamos a conexão SSE aqui para permitir reutilização
            pass