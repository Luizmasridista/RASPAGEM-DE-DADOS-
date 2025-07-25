"""
Configurações da aplicação frontend.
"""

# Configurações da API
import os
from pathlib import Path

# URL da API do backend
API_URL = "http://127.0.0.1:8000"

# Caminhos do sistema
BASE_DIR = Path(__file__).parent.parent
PLANILHA_MESTRE_DIR = os.path.join(BASE_DIR, "backend", "planilha_mestre")
PLANILHA_MESTRE_NOME = "planilha_mestre.xlsx"
PLANILHA_MESTRE_PATH = os.path.join(PLANILHA_MESTRE_DIR, PLANILHA_MESTRE_NOME)

# Configurações do Streamlit
PAGE_CONFIG = {
    "page_title": "Sistema de Consolidação de Planilhas",
    "page_icon": "📊",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

# Estilos CSS personalizados
CUSTOM_CSS = '''
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #0D47A1;
    }
    .success-box {
        padding: 1rem;
        background-color: #E8F5E9;
        border-left: 5px solid #4CAF50;
        margin-bottom: 1rem;
    }
    .warning-box {
        padding: 1rem;
        background-color: #FFF8E1;
        border-left: 5px solid #FFC107;
        margin-bottom: 1rem;
    }
    .error-box {
        padding: 1rem;
        background-color: #FFEBEE;
        border-left: 5px solid #F44336;
        margin-bottom: 1rem;
    }
</style>
'''

# Opções do menu
MENU_OPTIONS = ["Dashboard", "Upload de Planilhas", "Consolidação", "Backups", "Sobre"]
