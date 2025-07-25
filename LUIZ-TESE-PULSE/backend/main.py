"""
API REST para o sistema de consolidação de planilhas de treinamento.
"""

import os
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import logging

from backend.consolidador import (
    consolidar_planilhas,
    criar_backup_mestre,
    listar_backups,
    obter_planilha_mestre
)
from backend.config import HOST, PORT, PLANILHA_MESTRE_PATH

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("api")

# Inicialização da API
app = FastAPI(
    title="API de Consolidação de Planilhas",
    description="Sistema para consolidação automática de planilhas de treinamento",
    version="1.0.0"
)

# Configuração de CORS para permitir requisições do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar origens permitidas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConsolidacaoParams(BaseModel):
    usar_planilha_existente: bool = False  # Sempre criar nova por padrão
    criar_backup: bool = True
    sobrescrever: bool = True  # Compatibilidade com frontend

class ConsolidacaoResponse(BaseModel):
    sucesso: bool
    mensagem: str
    dados: Optional[Dict[str, Any]] = None

class BackupModel(BaseModel):
    nome: str
    caminho: str
    data: str
    tamanho_kb: float

@app.get("/")
async def root():
    """Endpoint raiz da API."""
    return {"mensagem": "API de Consolidação de Planilhas de Treinamento"}

@app.get("/status", response_model=Dict[str, Any])
async def status():
    """Verifica o status do sistema."""
    if not PLANILHA_MESTRE_PATH:
        raise HTTPException(status_code=500, detail="Caminho da planilha mestre não está definido.")

    planilha_mestre_existe = os.path.exists(PLANILHA_MESTRE_PATH)
    backups = listar_backups()

    # Obter informações adicionais da planilha mestre
    ultima_modificacao = None
    if planilha_mestre_existe:
        try:
            from datetime import datetime
            timestamp = os.path.getmtime(PLANILHA_MESTRE_PATH)
            ultima_modificacao = datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y %H:%M:%S")
        except Exception as e:
            logger.error(f"Erro ao obter informações da planilha mestre: {str(e)}")

    return {
        "status": "online",
        "planilha_mestre": {
            "existe": planilha_mestre_existe,
            "caminho": PLANILHA_MESTRE_PATH if planilha_mestre_existe else None,
            "ultima_modificacao": ultima_modificacao
        },
        "backups": {
            "total": len(backups),
            "ultimo": backups[0]["data"] if backups else None
        }
    }

@app.post("/consolidar", response_model=ConsolidacaoResponse)
async def consolidar(params: ConsolidacaoParams, background_tasks: BackgroundTasks):
    """Inicia o processo de consolidação das planilhas."""
    try:
        # Log dos parâmetros recebidos
        logger.info(f"Iniciando consolidação com parâmetros: criar_backup={params.criar_backup}, sobrescrever={getattr(params, 'sobrescrever', True)}")
        logger.info("Forçando criação de nova planilha mestre para consolidação adequada")
        
        # O backup é criado automaticamente dentro da função consolidar_planilhas
        # se já existir uma planilha mestre
        logger.info("Backup automático será criado se necessário durante a consolidação")
        
        # Sempre criar nova planilha mestre para garantir consolidação correta
        # O backup automático é criado internamente se necessário
        sucesso, resultado = consolidar_planilhas()
        
        if sucesso:
            return ConsolidacaoResponse(
                sucesso=True,
                mensagem="Consolidação realizada com sucesso! Nova planilha mestre criada com dados consolidados.",
                dados={
                    **resultado,
                    "planilhas_processadas": len(resultado.get('estruturas_processadas', [])),
                    "backup_criado": params.criar_backup,
                    "detalhes": {
                        "metodo": "Nova planilha mestre criada",
                        "estruturas": resultado.get('estruturas_processadas', []),
                        "colunas_consolidadas": resultado.get('colunas', [])
                    }
                }
            )
        else:
            return ConsolidacaoResponse(
                sucesso=False,
                mensagem=f"Falha na consolidação: {resultado}",
                dados={"erro": resultado}
            )
    
    except Exception as e:
        logger.error(f"Erro durante consolidação: {str(e)}")
        return ConsolidacaoResponse(
            sucesso=False,
            mensagem=f"Erro interno durante a consolidação: {str(e)}",
            dados={"erro": str(e)}
        )

@app.get("/download-mestre")
async def download_mestre():
    """Endpoint para download da planilha mestre."""
    caminho = obter_planilha_mestre()
    
    if not caminho or not os.path.exists(caminho):
        raise HTTPException(
            status_code=404,
            detail="Planilha mestre não encontrada"
        )
    
    return FileResponse(
        path=caminho,
        filename="planilha_mestre.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.get("/listar-backups", response_model=List[BackupModel])
async def get_backups():
    """Lista todos os backups disponíveis."""
    return listar_backups()

@app.get("/download-backup/{nome_backup}")
async def download_backup(nome_backup: str):
    """Endpoint para download de um backup específico."""
    backups = listar_backups()
    backup = next((b for b in backups if b["nome"] == nome_backup), None)
    
    if not backup:
        raise HTTPException(
            status_code=404,
            detail=f"Backup {nome_backup} não encontrado"
        )
    
    return FileResponse(
        path=backup["caminho"],
        filename=backup["nome"],
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def start_api():
    """Inicia o servidor da API."""
    uvicorn.run(
        "backend.main:app",
        host=HOST,
        port=PORT,
        reload=True
    )

if __name__ == "__main__":
    start_api()
