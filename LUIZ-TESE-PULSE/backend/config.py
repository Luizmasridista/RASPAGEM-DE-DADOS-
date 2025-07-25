"""
Configurações do sistema de consolidação de planilhas de treinamento.
"""

import os
from pathlib import Path

# Diretórios do sistema
BASE_DIR = Path(__file__).parent.parent
PLANILHAS_ORIGINAIS_DIR = os.path.join(BASE_DIR, "planilhas_originais")
PLANILHA_MESTRE_DIR = os.path.join(BASE_DIR, "planilha_mestre")
BACKUPS_DIR = os.path.join(BASE_DIR, "backups")

# Nome do arquivo mestre
PLANILHA_MESTRE_NOME = "planilha_mestre.xlsx"
PLANILHA_MESTRE_PATH = os.path.join(PLANILHA_MESTRE_DIR, PLANILHA_MESTRE_NOME)

# Configurações do servidor
HOST = "0.0.0.0"
PORT = 8000

# Formato do timestamp para backups
TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"

# Estrutura esperada das planilhas
ESTRUTURAS = ["Estrutura_A", "Estrutura_B", "Estrutura_C", "Estrutura_D"]
COLUNAS_OBRIGATORIAS = ["Colaborador", "Departamento", "Treinamento", "Carga_Horaria", "Data_Inicio", "Data_Fim", "Status"]

# Intervalo de backup automático (em segundos)
INTERVALO_BACKUP = 3600  # 1 hora
