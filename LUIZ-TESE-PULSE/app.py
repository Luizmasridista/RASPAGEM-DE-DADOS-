"""
Sistema de Consolidação de Planilhas de Treinamento
Aplicação principal refatorada em módulos.
"""

import streamlit as st
from frontend.config import PAGE_CONFIG, CUSTOM_CSS
from frontend.utils import criar_sidebar
from frontend.dashboard import mostrar_dashboard
from frontend.upload import mostrar_upload_planilhas
from frontend.consolidacao import mostrar_consolidacao
from frontend.backups import mostrar_backups
from frontend.sobre import mostrar_sobre

# Configurar página
st.set_page_config(**PAGE_CONFIG)

# Aplicar estilos personalizados
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def main():
    """Função principal da aplicação Streamlit."""
    
    # Cabeçalho
    st.markdown('<h1 class="main-header">Sistema de Consolidação de Planilhas de Treinamento</h1>', unsafe_allow_html=True)
    
    # Criar sidebar e obter menu selecionado
    menu = criar_sidebar()
    
    # Conteúdo principal baseado na seleção do menu
    if menu == "Dashboard":
        mostrar_dashboard()
    elif menu == "Upload de Planilhas":
        mostrar_upload_planilhas()
    elif menu == "Consolidação":
        mostrar_consolidacao()
    elif menu == "Backups":
        mostrar_backups()
    elif menu == "Sobre":
        mostrar_sobre()


if __name__ == "__main__":
    main()
