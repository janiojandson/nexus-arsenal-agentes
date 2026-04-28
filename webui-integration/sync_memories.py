#!/usr/bin/env python3
"""
webui-integration/sync_memories.py
🔄 NEXUS V4 — SINCRONIZADOR DE MEMÓRIAS PARA WEBUI

Sincroniza arquivos Markdown do repositório nexus-arsenal-agentes
para o formato de documentos do Open WebUI.

Uso:
    python sync_memories.py --output webui_docs/
"""

import os
import re
import sys
import json
import argparse
import requests
from datetime import datetime
from pathlib import Path


# ======================================================
# 🔗 CONFIGURAÇÃO
# ======================================================
GITHUB_API_URL = "https://api.github.com"
GITHUB_OWNER = "janiojandson"
GITHUB_REPO = "nexus-arsenal-agentes"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# Diretórios a serem sincronizados
DIRS_TO_SYNC = [
    "",  # Raiz do repositório
    "memorias",
    "docs",
    "webui-integration"
]

# Extensões de arquivo a serem sincronizadas
FILE_EXTENSIONS = [".md", ".MD", ".markdown"]


# ======================================================
# 🔄 FUNÇÕES DE SINCRONIZAÇÃO
# ======================================================
def fetch_repo_contents(path=""):
    """Busca conteúdo do repositório via API do GitHub"""
    url = f"{GITHUB_API_URL}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{path}"
    headers = {}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"❌ Erro ao buscar conteúdo do repositório: {response.status_code}")
        print(response.text)
        return []
    
    return response.json()


def fetch_file_content(file_url):
    """Busca conteúdo de um arquivo via API do GitHub"""
    headers = {}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    
    response = requests.get(file_url, headers=headers)
    if response.status_code != 200:
        print(f"❌ Erro ao buscar conteúdo do arquivo: {response.status_code}")
        return None
    
    return response.json().get("content")


def format_for_webui(content, filename, path=""):
    """Formata o conteúdo Markdown para o formato do WebUI"""
    # Extrai título do arquivo
    title = os.path.splitext(filename)[0].replace("_", " ").title()
    
    # Adiciona metadados
    formatted = f"# {title}\n\n"
    
    # Adiciona caminho como referência
    if path:
        formatted += f"*Fonte: `{path}/{filename}`*\n\n"
    else:
        formatted += f"*Fonte: `{filename}`*\n\n"
    
    # Adiciona conteúdo original
    formatted += content
    
    # Adiciona timestamp
    formatted += f"\n\n---\n*Sincronizado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
    
    return formatted


def create_webui_document(content, filename, output_dir):
    """Cria um documento no formato do WebUI"""
    # Sanitiza o nome do arquivo
    safe_filename = re.sub(r'[^\w\-\.]', '_', filename)
    output_path = os.path.join(output_dir, safe_filename)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"✅ Documento criado: {output_path}")
    return output_path


def process_directory(path, output_dir):
    """Processa um diretório do repositório"""
    print(f"🔍 Processando diretório: {path or 'raiz'}")
    
    # Cria diretório de saída se não existir
    os.makedirs(output_dir, exist_ok=True)
    
    # Busca conteúdo do diretório
    contents = fetch_repo_contents(path)
    if not contents:
        return []
    
    processed_files = []
    
    for item in contents:
        if item["type"] == "file":
            # Verifica se é um arquivo Markdown
            _, ext = os.path.splitext(item["name"])
            if ext.lower() in FILE_EXTENSIONS:
                print(f"📄 Processando arquivo: {item['name']}")
                
                # Busca conteúdo do arquivo
                content = fetch_file_content(item["download_url"])
                if content:
                    # Decodifica conteúdo (base64)
                    import base64
                    decoded_content = base64.b64decode(content).decode("utf-8")
                    
                    # Formata para WebUI
                    formatted = format_for_webui(decoded_content, item["name"], path)
                    
                    # Cria documento
                    doc_path = create_webui_document(formatted, item["name"], output_dir)
                    processed_files.append(doc_path)
    
    return processed_files


def create_index(processed_files, output_dir):
    """Cria um índice de todos os documentos processados"""
    index_path = os.path.join(output_dir, "_index.md")
    
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("# Índice de Memórias do Nexus\n\n")
        f.write("Este arquivo contém links para todas as memórias sincronizadas do GitHub.\n\n")
        
        for file_path in processed_files:
            filename = os.path.basename(file_path)
            name = os.path.splitext(filename)[0].replace("_", " ").title()
            f.write(f"- [{name}]({filename})\n")
        
        f.write(f"\n\n---\n*Atualizado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    
    print(f"📚 Índice criado: {index_path}")


# ======================================================
# 🚀 FUNÇÃO PRINCIPAL
# ======================================================
def main():
    parser = argparse.ArgumentParser(description="Sincroniza memórias do GitHub para o Open WebUI")
    parser.add_argument("--output", default="webui_docs", help="Diretório de saída para os documentos")
    args = parser.parse_args()
    
    output_dir = args.output
    print(f"🚀 Iniciando sincronização para: {output_dir}")
    
    all_processed = []
    
    for dir_path in DIRS_TO_SYNC:
        processed = process_directory(dir_path, output_dir)
        all_processed.extend(processed)
    
    if all_processed:
        create_index(all_processed, output_dir)
        print(f"✅ Sincronização concluída! {len(all_processed)} documentos processados.")
    else:
        print("⚠️ Nenhum documento foi processado.")


if __name__ == "__main__":
    main()