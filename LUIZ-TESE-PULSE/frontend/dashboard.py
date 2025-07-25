"""
Módulo do Dashboard principal da aplicação.
"""

import streamlit as st
import requests
import pandas as pd
from .config import API_URL


def mostrar_dashboard():
    """Exibe o dashboard principal."""
    st.markdown('<h2 class="sub-header">Dashboard</h2>', unsafe_allow_html=True)
    
    # Adicionar explicação sobre o sistema
    st.markdown('''
    <div style="background-color: #E8F5E9; padding: 15px; border-radius: 5px; border-left: 5px solid #4CAF50;">
        <h3 style="color: #2E7D32;">📊 Bem-vindo ao Sistema de Consolidação</h3>
        <p><strong>Como funciona:</strong></p>
        <ol>
            <li>Faça upload das 4 planilhas de treinamento</li>
            <li>Execute a consolidação automática</li>
            <li>Baixe a planilha mestre consolidada</li>
            <li>Acesse backups de consolidações anteriores</li>
        </ol>
    </div>
    ''', unsafe_allow_html=True)
    
    # Estatísticas do sistema
    _mostrar_estatisticas()
    
    # Status das planilhas
    _mostrar_status_planilhas()


def _mostrar_estatisticas():
    """Mostra estatísticas do sistema."""
    st.markdown("### 📈 Estatísticas do Sistema")
    
    try:
        response = requests.get(f"{API_URL}/status")
        if response.status_code == 200:
            status_data = response.json()
            
            # Criar colunas para as métricas
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    label="Planilha Mestre",
                    value="Disponível" if status_data['planilha_mestre']['existe'] else "Não disponível",
                    delta="✅" if status_data['planilha_mestre']['existe'] else "❌"
                )
            
            with col2:
                st.metric(
                    label="Total de Backups",
                    value=status_data['backups']['total'],
                    delta=f"+{status_data['backups']['total']}" if status_data['backups']['total'] > 0 else None
                )
            
            with col3:
                if status_data['planilha_mestre']['existe']:
                    st.metric(
                        label="Última Modificação",
                        value=status_data['planilha_mestre']['ultima_modificacao'][:10] if status_data['planilha_mestre']['ultima_modificacao'] else "N/A"
                    )
                else:
                    st.metric(
                        label="Última Modificação",
                        value="N/A"
                    )
            
            with col4:
                if status_data['backups']['ultimo']:
                    st.metric(
                        label="Último Backup",
                        value=status_data['backups']['ultimo'][:10]
                    )
                else:
                    st.metric(
                        label="Último Backup",
                        value="N/A"
                    )
        else:
            st.error("Erro ao obter estatísticas do sistema.")
    except Exception as e:
        st.error(f"Erro de conexão: {str(e)}")


def _mostrar_status_planilhas():
    """Mostra o status das planilhas originais."""
    st.markdown("### 📋 Status das Planilhas Originais")
    
    # Verificar se existem planilhas na pasta
    import os
    planilhas_dir = "planilhas_originais"
    
    if os.path.exists(planilhas_dir):
        arquivos = [f for f in os.listdir(planilhas_dir) if f.endswith(('.xlsx', '.xls'))]
        
        if arquivos:
            # Criar tabela com informações dos arquivos
            dados_planilhas = []
            for arquivo in arquivos:
                caminho = os.path.join(planilhas_dir, arquivo)
                tamanho = os.path.getsize(caminho) / 1024  # KB
                modificacao = os.path.getmtime(caminho)
                from datetime import datetime
                data_mod = datetime.fromtimestamp(modificacao).strftime('%d/%m/%Y %H:%M')
                
                dados_planilhas.append({
                    "Arquivo": arquivo,
                    "Tamanho (KB)": f"{tamanho:.1f}",
                    "Última Modificação": data_mod,
                    "Status": "✅ Pronto"
                })
            
            df = pd.DataFrame(dados_planilhas)
            st.dataframe(df, use_container_width=True)
            
            if len(arquivos) >= 4:
                st.success("✅ Todas as 4 planilhas estão disponíveis para consolidação!")
            else:
                st.warning(f"⚠️ Apenas {len(arquivos)} de 4 planilhas disponíveis.")
        else:
            st.warning("⚠️ Nenhuma planilha encontrada na pasta 'planilhas_originais'.")
    else:
        st.warning("⚠️ Pasta 'planilhas_originais' não encontrada.")
    
    # Instruções rápidas
    st.markdown("### 🚀 Próximos Passos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Para começar:**
        1. Vá para "Upload de Planilhas"
        2. Faça upload das 4 planilhas
        3. Execute a consolidação
        """)
    
    with col2:
        st.markdown("""
        **Recursos disponíveis:**
        - Dashboard com estatísticas
        - Upload de múltiplas planilhas
        - Consolidação automática
        - Sistema de backups
        """)
