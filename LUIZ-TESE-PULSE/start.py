"""
Script para iniciar o sistema de consolidação de planilhas.
Inicia tanto o backend (FastAPI) quanto o frontend (Streamlit).
"""

import os
import subprocess
import time
import webbrowser
import threading
import signal
import sys
from pathlib import Path

# Configurações
BACKEND_PORT = 8000
FRONTEND_PORT = 8501

def criar_diretorios():
    """Cria os diretórios necessários para o sistema."""
    os.makedirs("planilhas_originais", exist_ok=True)
    os.makedirs("planilha_mestre", exist_ok=True)
    os.makedirs("backups", exist_ok=True)
    print("✅ Diretórios criados com sucesso")

def iniciar_backend():
    """Inicia o servidor backend com FastAPI."""
    print("🚀 Iniciando servidor backend (FastAPI)...")
    backend_process = subprocess.Popen(
        ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", str(BACKEND_PORT), "--reload"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return backend_process

def iniciar_frontend():
    """Inicia o servidor frontend com Streamlit."""
    print("🚀 Iniciando servidor frontend (Streamlit)...")
    frontend_process = subprocess.Popen(
        ["streamlit", "run", "app.py", "--server.port", str(FRONTEND_PORT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return frontend_process

def abrir_navegador():
    """Abre o navegador com a interface do sistema."""
    # Aguarda um pouco para garantir que os servidores estejam prontos
    time.sleep(8)
    
    # Abre o frontend no navegador
    frontend_url = f"http://localhost:{FRONTEND_PORT}"
    print(f"🌐 Abrindo navegador em: {frontend_url}")
    webbrowser.open(frontend_url)
    
    # Também mostra a URL da API
    backend_url = f"http://localhost:{BACKEND_PORT}/docs"
    print(f"📚 Documentação da API disponível em: {backend_url}")

def monitorar_processo(processo, nome):
    """Monitora a saída de um processo em tempo real."""
    for linha in iter(processo.stdout.readline, ''):
        if linha:
            print(f"[{nome}] {linha.strip()}")
    
    for linha in iter(processo.stderr.readline, ''):
        if linha:
            print(f"[{nome} - ERRO] {linha.strip()}")

def manipular_sinal(sig, frame):
    """Manipula sinais para encerrar os processos corretamente."""
    print("\n⚠️ Encerrando o sistema...")
    if 'backend_process' in globals() and backend_process:
        backend_process.terminate()
    if 'frontend_process' in globals() and frontend_process:
        frontend_process.terminate()
    sys.exit(0)

if __name__ == "__main__":
    # Registrar manipuladores de sinais
    signal.signal(signal.SIGINT, manipular_sinal)
    signal.signal(signal.SIGTERM, manipular_sinal)
    
    # Verificar se estamos na raiz do projeto
    if not os.path.exists("backend") or not os.path.exists("frontend"):
        print("❌ Erro: Execute este script na raiz do projeto")
        sys.exit(1)
    
    # Criar diretórios necessários
    criar_diretorios()
    
    try:
        # Iniciar backend e frontend
        backend_process = iniciar_backend()
        frontend_process = iniciar_frontend()
        
        # Iniciar threads para monitorar a saída dos processos
        threading.Thread(target=monitorar_processo, args=(backend_process, "Backend"), daemon=True).start()
        threading.Thread(target=monitorar_processo, args=(frontend_process, "Frontend"), daemon=True).start()
        
        # Abrir navegador
        abrir_navegador()
        
        # Manter o script em execução
        print("✅ Sistema iniciado com sucesso!")
        print("🛑 Pressione Ctrl+C para encerrar o sistema")
        
        # Aguardar até que os processos terminem
        backend_process.wait()
        frontend_process.wait()
        
    except Exception as e:
        print(f"❌ Erro ao iniciar o sistema: {str(e)}")
        sys.exit(1)
