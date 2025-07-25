"""
Utilitários compartilhados para o sistema de upload.
"""

import streamlit as st
import os
from datetime import datetime


def criar_pasta_se_nao_existir(pasta):
    """Cria uma pasta se ela não existir."""
    try:
        os.makedirs(pasta, exist_ok=True)
        return True
    except Exception as e:
        st.error(f"❌ Erro ao criar pasta {pasta}: {str(e)}")
        return False


def listar_arquivos_planilhas(pasta):
    """Lista arquivos de planilhas (.xlsx, .xls) em uma pasta."""
    try:
        # Se for a pasta da planilha mestre, verificar o caminho específico
        if 'planilha_mestre' in pasta.lower():
            from frontend.config import PLANILHA_MESTRE_PATH
            if os.path.exists(PLANILHA_MESTRE_PATH):
                return [os.path.basename(PLANILHA_MESTRE_PATH)]
            return []
        
        # Para outras pastas, listar normalmente
        if not os.path.exists(pasta):
            return []
        
        return [f for f in os.listdir(pasta) if f.endswith(('.xlsx', '.xls'))]
    except Exception as e:
        print(f"Erro ao listar arquivos em {pasta}: {str(e)}")
        return []


def obter_info_arquivo(caminho_arquivo):
    """Obtém informações de um arquivo."""
    try:
        # Se for a planilha mestre, usar o caminho configurado
        if 'planilha_mestre' in caminho_arquivo.lower():
            from frontend.config import PLANILHA_MESTRE_PATH
            if os.path.exists(PLANILHA_MESTRE_PATH):
                caminho_arquivo = PLANILHA_MESTRE_PATH
            else:
                return {"existe": False}
        
        # Verificar se o arquivo existe
        if not os.path.exists(caminho_arquivo):
            return {"existe": False}
            
        # Obter informações do arquivo
        tamanho = os.path.getsize(caminho_arquivo) / 1024  # KB
        modificacao = os.path.getmtime(caminho_arquivo)
        data_mod = datetime.fromtimestamp(modificacao).strftime('%d/%m/%Y %H:%M')
        
        return {
            "tamanho_kb": round(tamanho, 2),  # Arredondar para 2 casas decimais
            "data_modificacao": data_mod,
            "existe": True,
            "caminho_completo": caminho_arquivo
        }
    except Exception as e:
        print(f"Erro ao obter informações do arquivo {caminho_arquivo}: {str(e)}")
        return {"existe": False, "erro": str(e)}


def salvar_arquivo_upload(uploaded_file, pasta_destino):
    """Salva um arquivo de upload na pasta especificada."""
    try:
        if not criar_pasta_se_nao_existir(pasta_destino):
            return False
        
        file_path = os.path.join(pasta_destino, uploaded_file.name)
        
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getvalue())
        
        # Verificar se foi salvo
        return os.path.exists(file_path)
        
    except Exception as e:
        st.error(f"❌ Erro ao salvar {uploaded_file.name}: {str(e)}")
        return False


def limpar_pasta_planilhas(pasta):
    """Remove todas as planilhas de uma pasta."""
    try:
        if not os.path.exists(pasta):
            return 0
        
        arquivos = listar_arquivos_planilhas(pasta)
        
        for arquivo in arquivos:
            os.remove(os.path.join(pasta, arquivo))
        
        return len(arquivos)
        
    except Exception as e:
        st.error(f"❌ Erro ao limpar pasta {pasta}: {str(e)}")
        return 0


def mostrar_css_upload():
    """Aplica CSS moderno para os componentes de upload."""
    st.markdown("""
    <style>
    .upload-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        margin: 1rem 0;
        border-left: 4px solid #4CAF50;
        transition: transform 0.2s ease;
    }
    
    .upload-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.12);
    }
    
    .master-card {
        border-left: 4px solid #FF9800;
    }
    
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 0.5rem;
    }
    
    .section-subtitle {
        color: #7f8c8d;
        font-size: 0.9rem;
        margin-bottom: 1rem;
    }
    
    .status-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
        margin: 0.2rem;
    }
    
    .status-success {
        background: #d4edda;
        color: #155724;
    }
    
    .status-warning {
        background: #fff3cd;
        color: #856404;
    }
    
    .status-info {
        background: #d1ecf1;
        color: #0c5460;
    }
    </style>
    """, unsafe_allow_html=True)


def mostrar_estruturas_esperadas():
    """Mostra as estruturas esperadas para as planilhas subordinadas."""
    estruturas = [
        {"nome": "Estrutura 1", "desc": "Dados do setor administrativo", "icon": "🏢"},
        {"nome": "Estrutura 2", "desc": "Dados do setor operacional", "icon": "⚙️"},
        {"nome": "Estrutura 3", "desc": "Dados do setor comercial", "icon": "💼"},
        {"nome": "Estrutura 4", "desc": "Dados do setor financeiro", "icon": "💰"}
    ]
    
    for est in estruturas:
        st.markdown(f"""
        <div style="padding: 0.5rem; margin: 0.3rem 0; background: #f8f9fa; border-radius: 6px; border-left: 3px solid #4CAF50;">
            {est['icon']} <strong>{est['nome']}</strong><br>
            <small style="color: #6c757d;">{est['desc']}</small>
        </div>
        """, unsafe_allow_html=True)
