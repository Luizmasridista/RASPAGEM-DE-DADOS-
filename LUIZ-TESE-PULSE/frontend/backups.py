"""
Módulo para gerenciamento de backups.
"""

import streamlit as st
import requests
import pandas as pd
import base64
from .config import API_URL


def mostrar_backups():
    """Interface para gerenciamento de backups."""
    st.markdown('<h2 class="sub-header">Gerenciamento de Backups</h2>', unsafe_allow_html=True)
    
    st.info("Aqui você pode visualizar e baixar os backups das consolidações anteriores.")
    
    # Controles superiores
    _controles_superiores()
    
    # Lista de backups
    _listar_backups()


def _controles_superiores():
    """Controles superiores da página."""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("### 📦 Backups Disponíveis")
    
    with col2:
        # Botão para atualizar a lista
        if st.button("🔄 Atualizar", use_container_width=True):
            pass  # O Streamlit atualizará automaticamente


def _listar_backups():
    """Lista todos os backups disponíveis."""
    try:
        response = requests.get(f"{API_URL}/listar-backups")
        
        if response.status_code == 200:
            backups = response.json()
            
            if backups:
                # Estatísticas dos backups
                _mostrar_estatisticas_backups(backups)
                
                # Tabela de backups
                _mostrar_tabela_backups(backups)
                
                # Área de download
                _area_download_backup(backups)
                
            else:
                _mostrar_sem_backups()
        else:
            st.error(f"❌ Erro ao obter lista de backups: {response.status_code}")
            
    except Exception as e:
        st.error(f"❌ Erro de conexão: {str(e)}")


def _mostrar_estatisticas_backups(backups):
    """Mostra estatísticas dos backups."""
    st.markdown("### 📊 Estatísticas")
    
    # Calcular estatísticas
    total_backups = len(backups)
    tamanho_total = sum(backup['tamanho_kb'] for backup in backups)
    
    # Backup mais recente
    backup_recente = max(backups, key=lambda x: x['data']) if backups else None
    
    # Mostrar métricas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de Backups", total_backups)
    
    with col2:
        st.metric("Tamanho Total", f"{tamanho_total:.1f} KB")
    
    with col3:
        if backup_recente:
            st.metric("Backup Mais Recente", backup_recente['data'][:10])
        else:
            st.metric("Backup Mais Recente", "N/A")
    
    with col4:
        if backup_recente:
            st.metric("Tamanho do Último", f"{backup_recente['tamanho_kb']:.1f} KB")
        else:
            st.metric("Tamanho do Último", "N/A")


def _mostrar_tabela_backups(backups):
    """Mostra tabela com todos os backups."""
    st.markdown("### 📋 Lista Completa")
    
    # Preparar dados para a tabela
    dados_backups = []
    for i, backup in enumerate(sorted(backups, key=lambda x: x['data'], reverse=True), 1):
        dados_backups.append({
            "ID": i,
            "Nome do Arquivo": backup["nome"],
            "Data e Hora": backup["data"],
            "Tamanho (KB)": f"{backup['tamanho_kb']:.1f}",
            "Status": "✅ Disponível"
        })
    
    # Mostrar tabela
    df_backups = pd.DataFrame(dados_backups)
    
    # Configurar exibição da tabela
    st.dataframe(
        df_backups,
        use_container_width=True,
        hide_index=True,
        column_config={
            "ID": st.column_config.NumberColumn("ID", width="small"),
            "Nome do Arquivo": st.column_config.TextColumn("Nome do Arquivo", width="large"),
            "Data e Hora": st.column_config.TextColumn("Data e Hora", width="medium"),
            "Tamanho (KB)": st.column_config.TextColumn("Tamanho (KB)", width="small"),
            "Status": st.column_config.TextColumn("Status", width="small")
        }
    )


def _area_download_backup(backups):
    """Área para download de backups específicos."""
    st.markdown("### 📥 Download de Backup")
    
    # Seleção de backup
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Criar opções para o selectbox
        opcoes_backup = []
        for backup in sorted(backups, key=lambda x: x['data'], reverse=True):
            label = f"{backup['nome']} ({backup['data']})"
            opcoes_backup.append((label, backup['nome']))
        
        if opcoes_backup:
            backup_selecionado = st.selectbox(
                "Selecione um backup para download:",
                options=[opcao[0] for opcao in opcoes_backup],
                format_func=lambda x: x,
                help="Backups ordenados do mais recente para o mais antigo"
            )
            
            # Obter nome do arquivo selecionado
            nome_arquivo = next(opcao[1] for opcao in opcoes_backup if opcao[0] == backup_selecionado)
    
    with col2:
        # Botão de download
        if opcoes_backup and st.button("📥 Baixar Backup", type="primary", use_container_width=True):
            _baixar_backup_selecionado(nome_arquivo)
    
    # Informações do backup selecionado
    if opcoes_backup:
        backup_info = next(b for b in backups if b['nome'] == nome_arquivo)
        
        with st.expander("ℹ️ Informações do Backup Selecionado", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Nome:** {backup_info['nome']}")
                st.write(f"**Data:** {backup_info['data']}")
            
            with col2:
                st.write(f"**Tamanho:** {backup_info['tamanho_kb']:.1f} KB")
                st.write(f"**Status:** ✅ Disponível")


def _baixar_backup_selecionado(nome_arquivo):
    """Baixa o backup selecionado."""
    try:
        with st.spinner("📥 Preparando download do backup..."):
            download_response = requests.get(f"{API_URL}/download-backup/{nome_arquivo}")
            
            if download_response.status_code == 200:
                # Criar link para download
                b64 = base64.b64encode(download_response.content).decode()
                
                href = f'''
                <a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" 
                   download="{nome_arquivo}"
                   style="display: inline-block; padding: 0.5rem 1rem; background-color: #4CAF50; color: white; 
                          text-decoration: none; border-radius: 0.25rem; font-weight: bold;">
                    📥 Clique aqui para baixar {nome_arquivo}
                </a>
                '''
                
                st.markdown(href, unsafe_allow_html=True)
                st.success("✅ Download preparado! Clique no link acima para baixar o backup.")
                
            else:
                st.error(f"❌ Erro ao baixar backup: {download_response.status_code}")
                
    except Exception as e:
        st.error(f"❌ Erro durante o download: {str(e)}")


def _mostrar_sem_backups():
    """Mostra mensagem quando não há backups."""
    st.warning("📦 Nenhum backup encontrado.")
    
    st.markdown("""
    ### Como criar backups:
    
    1. Vá para a seção **"Consolidação"**
    2. Marque a opção **"Criar backup automático"**
    3. Execute a consolidação
    4. O backup será criado automaticamente
    
    ### Sobre os backups:
    
    - Os backups são criados automaticamente durante a consolidação
    - Cada backup contém um timestamp único
    - Os backups preservam o histórico de todas as consolidações
    - Você pode baixar qualquer backup anterior a qualquer momento
    """)
    
    # Botão para ir para consolidação
    if st.button("🚀 Ir para Consolidação", type="primary"):
        st.session_state["menu"] = "Consolidação"
