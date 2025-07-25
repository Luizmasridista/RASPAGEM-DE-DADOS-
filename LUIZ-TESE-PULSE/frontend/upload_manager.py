"""
Gerenciador principal do sistema de upload modularizado.
"""

import streamlit as st
from frontend.upload_utils import mostrar_css_upload, listar_arquivos_planilhas
from frontend.upload_subordinadas import mostrar_componente_subordinadas
from frontend.upload_mestre import mostrar_componente_mestre


def mostrar_upload_planilhas():
    """Interface principal do sistema de upload modularizado."""
    
    # Aplicar CSS moderno
    mostrar_css_upload()
    
    # Título principal
    st.markdown("# 📊 Sistema de Upload de Planilhas")
    st.markdown("*Gerencie suas planilhas subordinadas e mestre de forma intuitiva*")
    
    # Layout em duas colunas
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        mostrar_componente_subordinadas()
    
    with col2:
        mostrar_componente_mestre()
    
    # Status geral do sistema
    mostrar_status_geral()


def mostrar_status_geral():
    """Mostra o status geral do sistema."""
    st.markdown("---")
    st.markdown("### 📈 Status Geral do Sistema")
    
    col1, col2, col3 = st.columns(3)
    
    # Status planilhas subordinadas
    subordinadas_count = len(listar_arquivos_planilhas("planilhas_originais"))
    
    with col1:
        st.metric(
            "📁 Planilhas Subordinadas",
            f"{subordinadas_count}/4",
            delta="Completo" if subordinadas_count >= 4 else "Pendente"
        )
    
    # Status planilha mestre
    mestre_count = len(listar_arquivos_planilhas("planilha_mestre"))
    mestre_existe = mestre_count > 0
    
    with col2:
        st.metric(
            "🎯 Planilha Mestre",
            "Disponível" if mestre_existe else "Não gerada",
            delta="OK" if mestre_existe else "Aguardando"
        )
    
    # Status consolidação
    with col3:
        pronto_consolidar = subordinadas_count >= 4
        st.metric(
            "⚡ Pronto p/ Consolidar",
            "Sim" if pronto_consolidar else "Não",
            delta="Pronto" if pronto_consolidar else "Aguardando"
        )
    
    # Próximos passos
    if subordinadas_count >= 4 and not mestre_existe:
        st.info("🚀 **Próximo passo:** Vá para a seção 'Consolidação' para gerar a planilha mestre!")
    elif subordinadas_count < 4:
        st.warning(f"📋 **Pendente:** Faça upload de {4 - subordinadas_count} planilha(s) subordinada(s) restante(s).")
    else:
        st.success("✅ **Sistema completo:** Todas as planilhas estão disponíveis!")
