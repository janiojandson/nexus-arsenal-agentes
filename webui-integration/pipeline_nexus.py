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

    # -------- ciclo de vida --------
    async def on_startup(self) -> None:
        print(f"🌉 [Nexus Pipeline] on_startup — alvo: {self.valves.NEXUS_BASE_URL}")

    async def on_shutdown(self) -> None:
        print("🌉 [Nexus Pipeline] on_shutdown")

    # -------- helpers --------
    def _headers(self) -> dict:
        h = {"Content-Type": "application/json", "Accept": "text/event-stream"}
        if self.valves.NEXUS_API_KEY:
            h["Authorization"] = f"Bearer {self.valves.NEXUS_API_KEY}"
        h["X-Client-Id"] = self.valves.NEXUS_CLIENT_ID
        return h

    def _format_event(self, evt: dict) -> str:
        t = evt.get("type", "status")
        data = evt.get("data", {})
        if t == "status":
            return f"📥 {data.get('msg', '...')}\n"
        if t == "progress":
            prov = data.get("provider", "?")
            model = data.get("model", "?")
            key = data.get("keyIndex", "?")
            return f"🧠 Processando via **{model}** @ {prov} (key #{key})\n"
        if t == "juiz":
            return f"⚖️ {data.get('msg', 'Juízes avaliando...')}\n"
        if t == "token":
            return data.get("text", "")
        if t == "final":
            return f"\n\n---\n✅ **Resposta final:**\n\n{data.get('response', '')}\n"
        if t == "error":
            return f"\n\n🚨 Erro: `{data.get('error', 'desconhecido')}`\n"
        return f"ℹ️ {json.dumps(data, ensure_ascii=False)}\n"

    # -------- STREAM SSE --------
    def _stream_sse(self, prompt: str, system_prompt: str) -> Generator[str, None, None]:
        url = f"{self.valves.NEXUS_BASE_URL.rstrip('/')}/api/v1/stream-command"
        payload = {
            "prompt": prompt,
            "systemPrompt": system_prompt,
            "clientId": self.valves.NEXUS_CLIENT_ID,
        }
        try:
            with requests.post(
                url,
                headers=self._headers(),
                json=payload,
                stream=True,
                timeout=self.valves.STREAM_TIMEOUT,
            ) as r:
                if r.status_code != 200:
                    yield f"🚨 SSE falhou (HTTP {r.status_code}). Fazendo fallback REST...\n"
                    yield from self._rest_fallback(prompt, system_prompt)
                    return

                buffer = ""
                for raw in r.iter_lines(decode_unicode=True):
                    if raw is None:
                        continue
                    if raw == "":
                        # fim de evento SSE
                        if buffer.startswith("data:"):
                            payload_txt = buffer[5:].strip()
                            if payload_txt and payload_txt != "[DONE]":
                                try:
                                    evt = json.loads(payload_txt)
                                    yield self._format_event(evt)
                                except json.JSONDecodeError:
                                    yield payload_txt + "\n"
                        buffer = ""
                    else:
                        buffer += raw + "\n"
        except requests.exceptions.RequestException as e:
            yield f"🚨 Falha de rede no SSE: `{e}`\n"
            yield from self._rest_fallback(prompt, system_prompt)

    # -------- REST FALLBACK --------
    def _rest_fallback(self, prompt: str, system_prompt: str) -> Generator[str, None, None]:
        url = f"{self.valves.NEXUS_BASE_URL.rstrip('/')}/api/v1/command"
        try:
            r = requests.post(
                url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.valves.NEXUS_API_KEY}"
                    if self.valves.NEXUS_API_KEY
                    else "",
                },
                json={"prompt": prompt, "systemPrompt": system_prompt},
                timeout=self.valves.STREAM_TIMEOUT,
            )
            if r.ok:
                data = r.json()
                yield data.get("response", "(resposta vazia)")
            else:
                yield f"🚨 REST falhou: HTTP {r.status_code} — {r.text[:300]}"
        except Exception as e:
            yield f"🚨 Falha REST: `{e}`"

    # -------- PIPE (entrypoint do Open WebUI) --------
    def pipe(
        self,
        user_message: str,
        model_id: str,
        messages: List[dict],
        body: dict,
    ) -> Union[str, Generator, Iterator]:
        text = (user_message or "").strip()

        # comando local !help
        if text.lower() in ("!help", "!ajuda", "!comandos"):
            return CommandMapping.list_commands()

        # monta system prompt a partir da conversa
        system_prompt = ""
        for m in messages:
            if m.get("role") == "system":
                system_prompt = m.get("content", "")
                break

        # escolhe stream ou rest
        if self.valves.USE_STREAM:
            return self._stream_sse(text, system_prompt)
        else:
            return self._rest_fallback(text, system_prompt)
