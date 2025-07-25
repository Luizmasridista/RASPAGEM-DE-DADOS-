"""
Módulo da página Sobre o sistema.
"""

import streamlit as st
from datetime import datetime


def mostrar_sobre():
    """Página sobre o sistema."""
    st.markdown('<h2 class="sub-header">Sobre o Sistema</h2>', unsafe_allow_html=True)
    
    # Informações principais
    _informacoes_principais()
    
    # Funcionalidades
    _mostrar_funcionalidades()
    
    # Como utilizar
    _como_utilizar()
    
    # Informações técnicas
    _informacoes_tecnicas()
    
    # Rodapé
    _rodape()


def _informacoes_principais():
    """Informações principais do sistema."""
    st.markdown("""
    ### 📊 Sistema de Consolidação de Planilhas de Treinamento
    
    Este sistema foi desenvolvido para automatizar o processo de consolidação de planilhas de treinamento 
    das 4 estruturas de gestão da empresa, proporcionando maior eficiência e controle sobre os dados.
    """)
    
    # Card com destaque
    st.markdown('''
    <div style="background-color: #E3F2FD; padding: 20px; border-radius: 10px; border-left: 5px solid #1E88E5; margin: 20px 0;">
        <h4 style="color: #1565C0; margin-top: 0;">🎯 Objetivo Principal</h4>
        <p>Unificar e consolidar dados de treinamento de múltiplas estruturas organizacionais em uma única planilha mestre, 
        mantendo a integridade dos dados e criando backups automáticos para segurança.</p>
    </div>
    ''', unsafe_allow_html=True)


def _mostrar_funcionalidades():
    """Mostra as funcionalidades do sistema."""
    st.markdown("### ⚙️ Funcionalidades")
    
    # Funcionalidades em colunas
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **📤 Upload de Planilhas**
        - Upload múltiplo de arquivos
        - Suporte a formatos .xlsx e .xls
        - Validação automática de arquivos
        - Preview dos dados antes do processamento
        
        **🔄 Consolidação Automática**
        - Processamento inteligente dos dados
        - Unificação de estruturas diferentes
        - Validação de integridade
        - Relatórios de processamento
        """)
    
    with col2:
        st.markdown("""
        **💾 Sistema de Backups**
        - Backups automáticos com timestamp
        - Histórico completo de consolidações
        - Download de backups anteriores
        - Gestão inteligente de armazenamento
        
        **📊 Dashboard Interativo**
        - Estatísticas em tempo real
        - Status do sistema
        - Monitoramento de processos
        - Interface intuitiva
        """)


def _como_utilizar():
    """Instruções de como utilizar o sistema."""
    st.markdown("### 📋 Como Utilizar")
    
    # Passos em tabs
    tab1, tab2, tab3, tab4 = st.tabs(["1️⃣ Preparação", "2️⃣ Upload", "3️⃣ Consolidação", "4️⃣ Download"])
    
    with tab1:
        st.markdown("""
        ### Preparação das Planilhas
        
        **Antes de começar:**
        - Certifique-se de que possui as 4 planilhas de treinamento
        - Verifique se os arquivos estão nos formatos .xlsx ou .xls
        - Confirme que as planilhas contêm as colunas esperadas
        - Faça backup dos arquivos originais (recomendado)
        
        **Estruturas esperadas:**
        - Planilha da Estrutura de Gestão 1
        - Planilha da Estrutura de Gestão 2
        - Planilha da Estrutura de Gestão 3
        - Planilha da Estrutura de Gestão 4
        """)
    
    with tab2:
        st.markdown("""
        ### Upload das Planilhas
        
        **Passos:**
        1. Acesse a seção **"Upload de Planilhas"**
        2. Clique em **"Selecione as planilhas"**
        3. Escolha os 4 arquivos simultaneamente
        4. Visualize o preview dos dados
        5. Clique em **"Salvar Planilhas"**
        
        **Dicas:**
        - Você pode selecionar múltiplos arquivos de uma vez
        - O sistema mostra um preview dos dados antes de salvar
        - Arquivos são validados automaticamente
        """)
    
    with tab3:
        st.markdown("""
        ### Processo de Consolidação
        
        **Passos:**
        1. Acesse a seção **"Consolidação"**
        2. Verifique os pré-requisitos
        3. Configure as opções (backup recomendado)
        4. Clique em **"Iniciar Consolidação"**
        5. Aguarde o processamento
        
        **Opções disponíveis:**
        - ✅ Criar backup automático (recomendado)
        - ✅ Sobrescrever planilha mestre existente
        """)
    
    with tab4:
        st.markdown("""
        ### Download e Backups
        
        **Planilha Mestre:**
        - Baixe a planilha consolidada na seção "Consolidação"
        - Arquivo gerado com timestamp único
        - Formato .xlsx compatível com Excel
        
        **Backups:**
        - Acesse a seção "Backups" para ver histórico
        - Baixe qualquer consolidação anterior
        - Visualize estatísticas dos backups
        """)


def _informacoes_tecnicas():
    """Informações técnicas do sistema."""
    st.markdown("### 🔧 Informações Técnicas")
    
    # Informações em expander
    with st.expander("📋 Especificações Técnicas", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **Backend:**
            - Python 3.7+
            - FastAPI (API REST)
            - Pandas (Processamento de dados)
            - Uvicorn (Servidor ASGI)
            
            **Frontend:**
            - Streamlit (Interface web)
            - Requests (Comunicação HTTP)
            - Base64 (Codificação de arquivos)
            """)
        
        with col2:
            st.markdown("""
            **Arquitetura:**
            - API REST para backend
            - Interface web responsiva
            - Processamento assíncrono
            - Sistema de arquivos local
            
            **Formatos Suportados:**
            - .xlsx (Excel 2007+)
            - .xls (Excel 97-2003)
            """)
    
    with st.expander("🛠️ Configurações do Sistema", expanded=False):
        st.markdown("""
        **Configurações Atuais:**
        - API URL: http://127.0.0.1:8000
        - Timeout de requisições: 30 segundos
        - Pasta de planilhas: planilhas_originais/
        - Pasta de backups: backups/
        - Pasta da planilha mestre: planilha_mestre/
        
        **Limites:**
        - Tamanho máximo por arquivo: Não limitado
        - Número máximo de planilhas: 4 (recomendado)
        - Formatos aceitos: .xlsx, .xls
        """)


def _rodape():
    """Rodapé com informações adicionais."""
    st.markdown("---")
    
    # Informações do sistema
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**📅 Data e Hora Atual**")
        st.text(datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
    
    with col2:
        st.markdown("**🔢 Versão do Sistema**")
        st.text("v1.0.0")
    
    with col3:
        st.markdown("**🏢 Desenvolvido para**")
        st.text("Gestão de Treinamentos")
    
    # Suporte
    st.markdown("### 📞 Suporte")
    st.info("""
    **Em caso de dúvidas ou problemas:**
    - Verifique se o backend está em execução
    - Consulte os logs do sistema
    - Entre em contato com o administrador do sistema
    """)
    
    # Links úteis
    st.markdown("### 🔗 Links Úteis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Ir para Dashboard"):
            st.session_state["menu"] = "Dashboard"
    
    with col2:
        if st.button("📤 Fazer Upload"):
            st.session_state["menu"] = "Upload de Planilhas"
    
    with col3:
        if st.button("🔄 Consolidar"):
            st.session_state["menu"] = "Consolidação"
