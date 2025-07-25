"""
Componente para gerenciamento da planilha mestre.
"""

import streamlit as st
import os
import time
from frontend.upload_utils import (
    salvar_arquivo_upload, 
    listar_arquivos_planilhas, 
    limpar_pasta_planilhas,
    obter_info_arquivo
)


def mostrar_componente_mestre():
    """Componente principal para gerenciamento da planilha mestre."""
    from frontend.config import PLANILHA_MESTRE_PATH, PLANILHA_MESTRE_DIR
    
    # Inicializar estado se não existir
    if 'mestre_upload_state' not in st.session_state:
        st.session_state.mestre_upload_state = {
            'em_andamento': False,
            'concluido': False,
            'erro': None
        }
    
    # Garantir que o estado de limpeza seja inicializado
    if 'limpando_mestre' not in st.session_state:
        st.session_state.limpando_mestre = False
    
    st.markdown("""
    <div class="upload-card master-card">
        <div class="section-header">
            🎯 Planilha Mestre
        </div>
        <div class="section-subtitle">
            Consolidação de todos os dados
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Verificar se a planilha mestre existe no caminho configurado
    if os.path.exists(PLANILHA_MESTRE_PATH):
        _mostrar_planilha_existente(PLANILHA_MESTRE_DIR, os.path.basename(PLANILHA_MESTRE_PATH))
    else:
        _mostrar_estado_vazio()
    
    # Mostrar opção de upload manual
    _mostrar_upload_manual()


def _mostrar_planilha_existente(pasta, arquivo):
    """Mostra informações da planilha mestre existente."""
    from frontend.config import PLANILHA_MESTRE_PATH
    
    # Usar o caminho configurado para a planilha mestre
    caminho = PLANILHA_MESTRE_PATH
    info = obter_info_arquivo(caminho)
    
    # Se não existir, mostrar mensagem de erro
    if not info.get('existe', False):
        st.error("❌ A planilha mestre não foi encontrada no local esperado.")
        return
    
    st.markdown("""
    <div style="background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; padding: 1rem; margin: 0.5rem 0;">
        <h4>📊 Planilha Mestre Atual</h4>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Arquivo", os.path.basename(caminho))
        st.metric("Tamanho", f"{info['tamanho_kb']:.1f} KB")
    with col2:
        st.metric("Última Atualização", info['data_modificacao'])
    
    # Botões de ação
    col_download, col_limpar = st.columns(2)
    with col_download:
        _botao_download(caminho, os.path.basename(caminho))
    
    with col_limpar:
        if st.button("🗑️ Limpar", use_container_width=True, key="limpar_mestre_btn"):
            _limpar_planilha_mestre()


def _mostrar_estado_vazio():
    """Mostra estado quando não há planilha mestre."""
    from frontend.config import PLANILHA_MESTRE_PATH
    
    # Container principal
    with st.container():
        st.markdown("""
        <div style="text-align: center; padding: 2rem; background: #f8f9fa; border-radius: 8px; border: 2px dashed #dee2e6; margin-bottom: 1.5rem;">
            <h3>📋 Nenhuma Planilha Mestre</h3>
            <p style="color: #6c757d; margin-bottom: 1.5rem;">Faça upload de uma planilha mestre para começar a consolidação.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Seção de upload
        st.markdown("### 📤 Enviar Planilha Mestre")
        st.markdown("Faça upload de um arquivo Excel (.xlsx) para ser usado como planilha meste.")
        
        # Upload de arquivo
        uploaded_file = st.file_uploader(
            "Selecione o arquivo",
            type=["xlsx", "xls"],
            accept_multiple_files=False,
            key="upload_mestre_file"
        )
        
        # Botão para confirmar o upload
        if uploaded_file is not None:
            if st.button("✅ Confirmar Upload", type="primary", use_container_width=True):
                _salvar_planilha_mestre(uploaded_file)
                # Forçar atualização da interface
                st.rerun()

def _mostrar_upload_manual():
    """Mostra opção de upload manual da planilha mestre."""
    st.markdown("---")
    st.markdown("**🔄 Upload Manual (Opcional)**")
    
    # Inicializar estado se não existir
    if 'mestre_upload_state' not in st.session_state:
        st.session_state.mestre_upload_state = {
            'em_andamento': False,
            'concluido': False,
            'erro': None
        }
    
    # Mostrar mensagem se upload em andamento
    if st.session_state.mestre_upload_state['em_andamento']:
        st.info("⏳ Processando upload da planilha mestre, aguarde...")
    
    # Uploader desabilitado durante processamento
    uploaded_mestre = st.file_uploader(
        "Substituir planilha mestre atual",
        type=['xlsx', 'xls'],
        help="Use apenas se necessário substituir a planilha mestre",
        key="mestre_uploader",
        disabled=st.session_state.mestre_upload_state['em_andamento']
    )
    
    # Botão desabilitado durante processamento
    if uploaded_mestre and not st.session_state.mestre_upload_state['em_andamento']:
        if st.button("📤 Substituir Planilha Mestre", 
                    type="secondary", 
                    use_container_width=True,
                    disabled=st.session_state.mestre_upload_state['em_andamento']):
            _salvar_planilha_mestre(uploaded_mestre)


def _botao_download(caminho_arquivo, nome_arquivo):
    """Cria botão de download para a planilha mestre."""
    from frontend.config import PLANILHA_MESTRE_PATH
    
    # Usar o caminho configurado para a planilha mestre
    if not os.path.exists(caminho_arquivo):
        st.error("❌ Arquivo não encontrado para download.")
        return
    
    try:
        with open(caminho_arquivo, "rb") as file:
            file_data = file.read()
            
        st.download_button(
            label="⬇️ Baixar Planilha Mestre",
            data=file_data,
            file_name=os.path.basename(caminho_arquivo),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key=f"download_mestre_{os.path.basename(caminho_arquivo)}"
        )
    except Exception as e:
        st.error(f"❌ Erro ao preparar o download: {str(e)}")
        st.error(f"Caminho do arquivo: {caminho_arquivo}")


def _salvar_planilha_mestre(uploaded_file):
    """Salva a planilha mestre e atualiza o estado da sessão."""
    from frontend.config import PLANILHA_MESTRE_DIR, PLANILHA_MESTRE_NOME, PLANILHA_MESTRE_PATH
    
    # Usar o caminho configurado para a planilha mestre
    pasta_destino = PLANILHA_MESTRE_DIR
    
    # Inicializar estados da sessão se não existirem
    if 'mestre_upload_state' not in st.session_state:
        st.session_state.mestre_upload_state = {
            'em_andamento': False,
            'concluido': False,
            'erro': None
        }
    
    # Estado centralizado da planilha mestre
    if 'planilha_mestre' not in st.session_state:
        st.session_state.planilha_mestre = {
            'caminho': None,
            'nome_arquivo': None,
            'tamanho': 0,
            'data_modificacao': None
        }
    
    # Evitar múltiplos uploads simultâneos
    if st.session_state.mestre_upload_state['em_andamento']:
        return
    
    # Iniciar processo de upload
    st.session_state.mestre_upload_state.update({
        'em_andamento': True,
        'concluido': False,
        'erro': None
    })
    
    try:
        # Criar pasta se não existir
        if not os.path.exists(pasta_destino):
            os.makedirs(pasta_destino)
        
        # Reset do file pointer para garantir leitura correta
        uploaded_file.seek(0)
        
        # Garantir que o diretório existe
        os.makedirs(pasta_destino, exist_ok=True)
        
        # Salvar o arquivo com o nome padrão (planilha_mestre.xlsx)
        file_path = os.path.join(pasta_destino, PLANILHA_MESTRE_NOME)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Verificar se o arquivo foi salvo
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            # Atualizar estado da planilha mestre
            file_info = os.stat(file_path)
            st.session_state.planilha_mestre = {
                'caminho': file_path,
                'nome_arquivo': uploaded_file.name,
                'tamanho': file_info.st_size,
                'data_modificacao': time.strftime('%d/%m/%Y %H:%M:%S', 
                                               time.localtime(file_info.st_mtime))
            }
            
            st.success(f"✅ Planilha mestre salva como {uploaded_file.name}")
            st.balloons()
            
            # Atualizar estado para sucesso
            st.session_state.mestre_upload_state.update({
                'em_andamento': False,
                'concluido': True,
                'erro': None
            })
            
        else:
            error_msg = "Arquivo não foi salvo corretamente ou está vazio"
            st.error(f"❌ Erro: {error_msg}")
            
            # Limpar estado em caso de erro
            st.session_state.planilha_mestre = {
                'caminho': None,
                'nome_arquivo': None,
                'tamanho': 0,
                'data_modificacao': None
            }
            
            st.session_state.mestre_upload_state.update({
                'em_andamento': False,
                'concluido': True,
                'erro': error_msg
            })
            
    except Exception as e:
        error_msg = str(e)
        st.error(f"❌ Erro durante o salvamento: {error_msg}")
        
        # Limpar estado em caso de erro
        st.session_state.planilha_mestre = {
            'caminho': None,
            'nome_arquivo': None,
            'tamanho': 0,
            'data_modificacao': None
        }
        
        # Atualizar estado com erro
        st.session_state.mestre_upload_state.update({
            'em_andamento': False,
            'concluido': True,
            'erro': error_msg
        })


def _limpar_planilha_mestre():
    """Remove a planilha mestre e reseta o estado."""
    from frontend.config import PLANILHA_MESTRE_PATH, PLANILHA_MESTRE_DIR
    
    # Inicializar estado se não existir
    if 'limpando_mestre' not in st.session_state:
        st.session_state.limpando_mestre = False
    
    # Evitar múltiplas execuções simultâneas
    if st.session_state.limpando_mestre:
        return
    
    # Iniciar processo de limpeza
    st.session_state.limpando_mestre = True
    
    try:
        # Resetar o estado de upload para garantir que a interface seja atualizada
        if 'mestre_upload_state' in st.session_state:
            st.session_state.mestre_upload_state.update({
                'em_andamento': False,
                'concluido': False,
                'erro': None
            })
        
        # Verificar se o arquivo existe antes de tentar remover
        if os.path.exists(PLANILHA_MESTRE_PATH):
            try:
                os.remove(PLANILHA_MESTRE_PATH)
                st.success("✅ Planilha mestre removida com sucesso!")
                st.balloons()
                
                # Atualizar o estado da planilha mestre
                if 'planilha_mestre' in st.session_state:
                    st.session_state.planilha_mestre = {
                        'caminho': None,
                        'nome_arquivo': None,
                        'tamanho': 0,
                        'data_modificacao': None
                    }
                
                # Forçar atualização da interface
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Erro ao remover a planilha mestre: {str(e)}")
        else:
            st.warning("ℹ️ Nenhuma planilha mestre encontrada para remover.")
    
    except Exception as e:
        st.error(f"❌ Erro ao limpar planilha mestre: {str(e)}")
    
    finally:
        # Resetar o estado de limpeza
        st.session_state.limpando_mestre = False
