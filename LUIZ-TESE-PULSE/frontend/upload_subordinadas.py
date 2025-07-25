"""
Componente para upload de planilhas subordinadas.
"""

import streamlit as st
import pandas as pd
from frontend.upload_utils import (
    salvar_arquivo_upload, 
    listar_arquivos_planilhas, 
    limpar_pasta_planilhas,
    mostrar_estruturas_esperadas
)


def mostrar_componente_subordinadas():
    """Componente principal para upload de planilhas subordinadas."""
    
    # Inicializar estado se não existir
    if 'upload_state' not in st.session_state:
        st.session_state.upload_state = {
            'em_andamento': False,
            'concluido': False,
            'erros': [],
            'sucesso': 0,
            'total': 0,
            'arquivos_processados': 0
        }
    
    # Garantir que o estado de limpeza seja inicializado
    if 'limpando_subordinadas' not in st.session_state:
        st.session_state.limpando_subordinadas = False
    
    st.markdown("""
    <div class="upload-card">
        <div class="section-header">
            📁 Planilhas Subordinadas
        </div>
        <div class="section-subtitle">
            Dados setoriais para consolidação
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Informações das estruturas esperadas
    with st.expander("ℹ️ Estruturas Esperadas", expanded=False):
        mostrar_estruturas_esperadas()
    
    # Upload de arquivos (desabilitado durante upload)
    uploaded_files = st.file_uploader(
        "📤 Selecione as planilhas subordinadas",
        type=['xlsx', 'xls'],
        accept_multiple_files=True,
        help="Formatos aceitos: .xlsx, .xls",
        key="subordinadas_uploader",
        disabled=st.session_state.upload_state.get('em_andamento', False)
    )
    
    # Verificar se há upload em andamento
    if st.session_state.upload_state.get('em_andamento', False):
        _atualizar_interface_upload(uploaded_files if uploaded_files else [])
    
    # Mostrar preview e botões se houver arquivos e não estiver em andamento
    if uploaded_files and not st.session_state.upload_state.get('em_andamento', False):
        _mostrar_preview_arquivos(uploaded_files)
        _mostrar_botoes_acao(uploaded_files)
    
    # Status atual
    _mostrar_status_subordinadas()


def _mostrar_preview_arquivos(uploaded_files):
    """Mostra preview dos arquivos selecionados."""
    st.success(f"✅ {len(uploaded_files)} arquivo(s) selecionado(s)")
    
    for i, file in enumerate(uploaded_files, 1):
        with st.expander(f"📄 {file.name} ({file.size/1024:.1f} KB)", expanded=False):
            try:
                df = pd.read_excel(file)
                col_info, col_preview = st.columns([1, 2])
                
                with col_info:
                    st.metric("Linhas", df.shape[0])
                    st.metric("Colunas", df.shape[1])
                
                with col_preview:
                    st.dataframe(df.head(3), use_container_width=True)
                    
            except Exception as e:
                st.error(f"❌ Erro ao ler arquivo: {str(e)}")


def _mostrar_botoes_acao(uploaded_files):
    """Mostra botões de ação para os arquivos."""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if st.button("💾 Salvar Planilhas", type="primary", use_container_width=True):
            _salvar_planilhas(uploaded_files)
    
    with col2:
        if st.button("🔄 Info", help="Informações dos arquivos"):
            for i, f in enumerate(uploaded_files, 1):
                st.write(f"{i}. {f.name} ({f.size} bytes)")


def _salvar_planilhas(uploaded_files):
    """Salva as planilhas subordinadas de forma simples e sem travar a interface."""
    pasta_destino = "planilhas_originais"
    
    # Inicializar estado se não existir
    if 'upload_state' not in st.session_state:
        st.session_state.upload_state = {
            'em_andamento': False,
            'concluido': False,
            'erros': [],
            'sucesso': 0,
            'total': 0,
            'arquivos_processados': 0
        }
    
    # Evitar múltiplos uploads simultâneos
    if st.session_state.upload_state['em_andamento']:
        return
    
    # Iniciar processo de upload
    st.session_state.upload_state.update({
        'em_andamento': True,
        'concluido': False,
        'erros': [],
        'sucesso': 0,
        'total': len(uploaded_files),
        'arquivos_processados': 0
    })
    
    # Processar o upload diretamente sem rerun para evitar loop infinito
    _processar_upload_planilhas(uploaded_files, pasta_destino)
    
    # Atualizar estado após o processamento
    st.session_state.upload_state['em_andamento'] = False
    st.session_state.upload_state['concluido'] = True


def _processar_upload_planilhas(uploaded_files, pasta_destino):
    """Processa o upload das planilhas em um único ciclo de execução."""
    # Container para feedback
    feedback_container = st.empty()
    
    with feedback_container.container():
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Processar cada arquivo
        for i, file in enumerate(uploaded_files):
            # Atualizar status
            status_text.text(f"Processando {i+1} de {len(uploaded_files)}: {file.name}")
            progress_bar.progress((i + 1) / len(uploaded_files))
            
            try:
                # Reset do ponteiro do arquivo
                file.seek(0)
                
                # Salvar arquivo
                if salvar_arquivo_upload(file, pasta_destino):
                    st.session_state.upload_state['sucesso'] += 1
                else:
                    st.session_state.upload_state['erros'].append(file.name)
                    
            except Exception as e:
                st.session_state.upload_state['erros'].append(f"{file.name} - {str(e)}")
            
            # Atualizar contador de arquivos processados
            st.session_state.upload_state['arquivos_processados'] = i + 1
        
        # Processo concluído
        st.session_state.upload_state.update({
            'em_andamento': False,
            'concluido': True
        })
        
        # Limpar elementos de progresso
        progress_bar.empty()
        status_text.empty()
        
        # Mostrar resultados
        if st.session_state.upload_state['sucesso'] > 0:
            st.success(f"✅ {st.session_state.upload_state['sucesso']} planilha(s) salva(s) com sucesso!")
            if st.session_state.upload_state['sucesso'] == len(uploaded_files):
                st.balloons()
        
        if st.session_state.upload_state['erros']:
            st.error(f"❌ Erro ao salvar: {', '.join(st.session_state.upload_state['erros'])}")

def _atualizar_interface_upload(uploaded_files):
    """Atualiza a interface durante o upload."""
    if not st.session_state.upload_state['concluido']:
        # Executar o processamento dos arquivos
        pasta_destino = "planilhas_originais"
        _processar_upload_planilhas(uploaded_files, pasta_destino)


def _mostrar_status_subordinadas():
    """Mostra o status das planilhas subordinadas."""
    pasta = "planilhas_originais"
    arquivos = listar_arquivos_planilhas(pasta)
    total = len(arquivos)
    
    # Status visual
    if total >= 4:
        st.markdown('<span class="status-badge status-success">✅ Completo (4/4)</span>', unsafe_allow_html=True)
    elif total > 0:
        st.markdown(f'<span class="status-badge status-warning">⚠️ Parcial ({total}/4)</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge status-info">📝 Aguardando upload</span>', unsafe_allow_html=True)
    
    # Lista de arquivos
    if arquivos:
        with st.expander(f"📁 Arquivos ({total})", expanded=False):
            for arquivo in arquivos:
                st.markdown(f"• {arquivo}")
            
            if st.button("🗑️ Limpar Todos", key="limpar_subordinadas"):
                _limpar_arquivos()


def _limpar_arquivos():
    """Limpa todas as planilhas subordinadas e reseta o estado."""
    pasta = "planilhas_originais"
    
    # Inicializar estado se não existir
    if 'limpando_subordinadas' not in st.session_state:
        st.session_state.limpando_subordinadas = False
    
    # Evitar múltiplas execuções simultâneas
    if st.session_state.limpando_subordinadas:
        return
    
    # Iniciar processo de limpeza
    st.session_state.limpando_subordinadas = True
    
    # Container para feedback
    feedback_container = st.empty()
    
    try:
        with feedback_container.container():
            st.info("⏳ Limpando arquivos, aguarde...")
            
            # Limpar a pasta
            removidos = limpar_pasta_planilhas(pasta)
            
            # Mostrar feedback
            if removidos > 0:
                st.success(f"✅ {removidos} arquivo(s) removido(s)!")
                st.balloons()
            else:
                st.warning("ℹ️ Nenhum arquivo encontrado para remover.")
    
    except Exception as e:
        st.error(f"❌ Erro ao limpar arquivos: {str(e)}")
    
    finally:
        # Resetar o estado de limpeza
        st.session_state.limpando_subordinadas = False
        
        # Resetar o estado de upload para garantir que os botões reapareçam
        st.session_state.upload_state = {
            'em_andamento': False,
            'concluido': False,
            'erros': [],
            'sucesso': 0,
            'total': 0,
            'arquivos_processados': 0
        }
        
       
