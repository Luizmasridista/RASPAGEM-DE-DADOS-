"""
Funções utilitárias para a aplicação frontend.
"""

import streamlit as st
import requests
from .config import API_URL


def verificar_status_api():
    """
    Verifica o status da API e retorna informações de conexão.
    
    Returns:
        tuple: (conectado: bool, status_data: dict, erro: str)
    """
    try:
        status_response = requests.get(f"{API_URL}/status", timeout=5)
        if status_response.status_code == 200:
            return True, status_response.json(), None
        else:
            return False, None, f"Status code: {status_response.status_code}"
    except Exception as e:
        return False, None, str(e)


def mostrar_status_sidebar():
    """
    Mostra o status da API na sidebar.
    """
    conectado, status_data, erro = verificar_status_api()
    
    if conectado:
        st.success("✅ API conectada")
        
        # Mostrar informações do status
        st.info(f"Planilha mestre: {'Disponível' if status_data['planilha_mestre']['existe'] else 'Não disponível'}")
        st.info(f"Total de backups: {status_data['backups']['total']}")
        if status_data['backups']['ultimo']:
            st.info(f"Último backup: {status_data['backups']['ultimo']}")
    else:
        st.error("❌ API não conectada")
        if erro:
            st.info(f"Erro de conexão: {erro}")
        st.info("Verifique se o backend está em execução na porta 8000")
        st.info("Execute 'uvicorn backend.main:app --host 0.0.0.0 --port 8000' no terminal para iniciar o backend.")


def inicializar_menu():
    """
    Inicializa e gerencia o estado do menu.
    
    Returns:
        str: Opção selecionada no menu
    """
    from .config import MENU_OPTIONS
    
    # Inicializar a variável de estado para o menu se não existir
    if "menu" not in st.session_state:
        st.session_state["menu"] = "Dashboard"
        
    # Opções do menu
    menu = st.radio(
        "Selecione uma opção:",
        MENU_OPTIONS,
        index=MENU_OPTIONS.index(st.session_state["menu"])
    )
    
    # Atualizar a variável de estado
    st.session_state["menu"] = menu
    
    return menu


def criar_sidebar():
    """
    Cria a sidebar completa da aplicação.
    
    Returns:
        str: Opção selecionada no menu
    """
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/microsoft-excel-2019--v1.png", width=100)
        st.markdown("## Menu")
        
        # Verificar status da API
        mostrar_status_sidebar()
        
        st.divider()
        
        # Menu de navegação
        return inicializar_menu()
