"""
Módulo para consolidação de planilhas.
"""

import streamlit as st
import requests
import base64
import time
import os
from .config import API_URL


def mostrar_consolidacao():
    """Interface para consolidação de planilhas."""
    st.markdown('<h2 class="sub-header">Consolidação de Planilhas</h2>', unsafe_allow_html=True)
    
    # Inicializar estado da planilha mestre se não existir
    if 'planilha_mestre' not in st.session_state:
        st.session_state.planilha_mestre = {
            'caminho': None,
            'nome_arquivo': None,
            'tamanho': 0,
            'data_modificacao': None
        }
    
    # Verificar se há uma planilha mestre disponível
    mestre_disponivel = False
    if st.session_state.planilha_mestre and st.session_state.planilha_mestre.get('caminho'):
        if os.path.exists(st.session_state.planilha_mestre['caminho']):
            mestre_disponivel = True
    
    # Se não houver planilha mestre, verificar se existe na pasta padrão
    if not mestre_disponivel:
        pasta_mestre = "planilha_mestre"
        if os.path.exists(pasta_mestre):
            arquivos_mestre = [f for f in os.listdir(pasta_mestre) 
                             if f.endswith(('.xlsx', '.xls'))]
            if arquivos_mestre:
                file_path = os.path.join(pasta_mestre, arquivos_mestre[0])
                file_info = os.stat(file_path)
                st.session_state.planilha_mestre = {
                    'caminho': file_path,
                    'nome_arquivo': arquivos_mestre[0],
                    'tamanho': file_info.st_size,
                    'data_modificacao': time.strftime('%d/%m/%Y %H:%M:%S', 
                                                   time.localtime(file_info.st_mtime))
                }
                mestre_disponivel = True
    
    # Exibir informações da planilha mestre
    if mestre_disponivel:
        st.success(f"📋 Planilha Mestre: {st.session_state.planilha_mestre['nome_arquivo']}")
        st.caption(f"Última modificação: {st.session_state.planilha_mestre['data_modificacao']}")
    else:
        st.warning("⚠️ Nenhuma planilha mestre encontrada. Faça o upload de uma planilha mestre na seção de Upload.")
    
    st.info("Execute a consolidação automática das planilhas de treinamento.")
    
    # Verificar pré-requisitos
    _verificar_prerequisitos(mestre_disponivel)
    
    # Área de consolidação
    _area_consolidacao(mestre_disponivel)
    
    # Download da planilha mestre
    _area_download(mestre_disponivel)


def _verificar_prerequisitos(mestre_disponivel):
    """Verifica se os pré-requisitos estão atendidos."""
    st.markdown("### ✅ Verificação de Pré-requisitos")
    
    import os
    planilhas_dir = "planilhas_originais"
    
    # Verificar pasta e arquivos
    if os.path.exists(planilhas_dir):
        arquivos = [f for f in os.listdir(planilhas_dir) if f.endswith(('.xlsx', '.xls'))]
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Verificar planilhas subordinadas
            if len(arquivos) >= 4:
                st.success(f"✅ {len(arquivos)} planilhas encontradas")
            else:
                st.warning(f"⚠️ Apenas {len(arquivos)} de 4 planilhas encontradas")
            
            # Verificar planilha mestre
            if mestre_disponivel:
                st.success("✅ Planilha mestre disponível")
            else:
                st.warning("⚠️ Nenhuma planilha mestre encontrada")
        
        with col2:
            # Verificar conexão com API
            try:
                response = requests.get(f"{API_URL}/status", timeout=5)
                if response.status_code == 200:
                    st.success("✅ API conectada")
                    
                    # Verificar versão da API
                    try:
                        versao = response.json().get('versao', 'desconhecida')
                        st.caption(f"Versão da API: {versao}")
                    except:
                        pass
                else:
                    st.error("❌ API não conectada")
            except Exception as e:
                st.error(f"❌ Erro ao conectar à API: {str(e)}")
        
        # Mostrar lista de arquivos
        if arquivos:
            with st.expander("📋 Planilhas Disponíveis", expanded=False):
                st.write("**Planilhas Subordinadas:**")
                for i, arquivo in enumerate(arquivos, 1):
                    st.write(f"{i}. {arquivo}")
                
                if mestre_disponivel:
                    st.write("\n**Planilha Mestre:**")
                    st.write(f"• {st.session_state.planilha_mestre['nome_arquivo']}")
    else:
        st.error("❌ Pasta 'planilhas_originais' não encontrada")
        st.info("👉 Vá para 'Upload de Planilhas' para fazer upload dos arquivos primeiro.")
    
    # Verificar permissões de escrita
    try:
        pasta_teste = "teste_perm"
        os.makedirs(pasta_teste, exist_ok=True)
        arquivo_teste = os.path.join(pasta_teste, "teste.txt")
        with open(arquivo_teste, 'w') as f:
            f.write("teste")
        os.remove(arquivo_teste)
        os.rmdir(pasta_teste)
    except Exception as e:
        st.error(f"❌ Erro de permissão: {str(e)}")
        st.warning("O aplicativo não tem permissão para escrever no diretório atual.")


def _area_consolidacao(mestre_disponivel):
    """Área principal de consolidação."""
    st.markdown("### 🔄 Executar Consolidação")
    
    # Verificar se a planilha mestre está disponível
    if not mestre_disponivel:
        st.warning("⚠️ Nenhuma planilha mestre disponível. Faça o upload de uma planilha mestre primeiro.")
        if st.button("Ir para Upload de Planilha Mestre", key="ir_para_upload"):
            st.session_state.menu_ativo = "Upload de Planilhas"
            st.rerun()
        return
    
    # Opções de consolidação
    with st.container():
        st.markdown("#### Opções de Consolidação")
        
        col1, col2 = st.columns(2)
        
        with col1:
            criar_backup = st.checkbox(
                "Criar backup automático", 
                value=True, 
                help="Cria um backup da planilha mestre atual antes de sobrescrevê-la"
            )
            
            # Mostrar data e hora do último backup se existir
            pasta_backups = "backups"
            if os.path.exists(pasta_backups):
                backups = [f for f in os.listdir(pasta_backups) if f.endswith('.xlsx')]
                if backups:
                    ultimo_backup = max(backups)
                    st.caption(f"Último backup: {ultimo_backup.split('_backup_')[1].replace('.xlsx', '')}")
        
        with col2:
            sobrescrever = st.checkbox(
                "Sobrescrever planilha mestre existente", 
                value=True,
                help="Se desmarcado, será criada uma nova planilha com timestamp"
            )
            
            # Mostrar informações da planilha mestre atual
            if mestre_disponivel:
                st.caption(f"Arquivo atual: {st.session_state.planilha_mestre['nome_arquivo']}")
    
    # Botão de consolidação
    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("🚀 Iniciar Consolidação", 
                    type="primary", 
                    use_container_width=True,
                    disabled=not mestre_disponivel):
            _executar_consolidacao(criar_backup, sobrescrever)
    
    # Mensagem informativa
    st.info("""
    ℹ️ A consolidação irá processar todas as planilhas subordinadas e atualizar a planilha mestre 
    com os dados mais recentes, de acordo com as opções selecionadas.
    """)


def _executar_consolidacao(criar_backup, sobrescrever):
    """Executa o processo de consolidação."""
    # Criar container para o progresso
    progress_container = st.container()
    
    with progress_container:
        # Barra de progresso
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Etapa 1: Iniciando
            status_text.text("🔄 Iniciando consolidação...")
            progress_bar.progress(10)
            time.sleep(1)
            
            # Etapa 2: Enviando requisição
            status_text.text("📤 Enviando requisição para API...")
            progress_bar.progress(30)
            
            # Preparar dados da requisição
            payload = {
                "criar_backup": criar_backup,
                "sobrescrever": sobrescrever
            }
            
            # Fazer requisição
            response = requests.post(f"{API_URL}/consolidar", json=payload, timeout=30)
            progress_bar.progress(70)
            
            # Etapa 3: Processando resposta
            status_text.text("⚙️ Processando resposta...")
            progress_bar.progress(90)
            time.sleep(1)
            
            # Verificar resultado
            if response.status_code == 200:
                resultado = response.json()
                progress_bar.progress(100)
                status_text.text("✅ Consolidação concluída com sucesso!")
                
                # Verificar se a consolidação foi bem-sucedida
                if resultado.get('sucesso', False):
                    # Mostrar resultados
                    _mostrar_resultado_consolidacao(resultado)
                else:
                    # Erro retornado pela API
                    mensagem_erro = resultado.get('mensagem', 'Erro desconhecido')
                    st.error(f"❌ Erro na consolidação: {mensagem_erro}")
                    
                    # Mostrar detalhes do erro se disponíveis
                    if 'dados' in resultado and 'erro' in resultado['dados']:
                        st.error(f"Detalhes: {resultado['dados']['erro']}")
                
            else:
                st.error(f"❌ Erro na comunicação com a API: {response.status_code}")
                try:
                    erro_json = response.json()
                    if 'detail' in erro_json:
                        st.error(f"Detalhes: {erro_json['detail']}")
                    elif 'mensagem' in erro_json:
                        st.error(f"Detalhes: {erro_json['mensagem']}")
                except:
                    if response.text:
                        st.error(f"Detalhes: {response.text}")
                    
        except requests.exceptions.Timeout:
            st.error("❌ Timeout: A consolidação demorou mais que o esperado.")
        except Exception as e:
            st.error(f"❌ Erro durante a consolidação: {str(e)}")
        finally:
            # Limpar barra de progresso após alguns segundos
            time.sleep(3)
            progress_container.empty()


def _mostrar_resultado_consolidacao(resultado):
    """Mostra os resultados da consolidação."""
    st.markdown("### 📊 Resultado da Consolidação")
    
    # Sucesso
    st.success("✅ Consolidação realizada com sucesso!")
    
    # Extrair dados do resultado
    dados = resultado.get('dados', resultado) if 'dados' in resultado else resultado
    
    # Detalhes em colunas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        planilhas_proc = dados.get('planilhas_processadas', [])
        if isinstance(planilhas_proc, list):
            st.metric("Planilhas Processadas", len(planilhas_proc))
            if planilhas_proc:
                st.caption(f"Arquivos: {', '.join(planilhas_proc)}")
        else:
            st.metric("Planilhas Processadas", planilhas_proc or 'N/A')
    
    with col2:
        total_registros = dados.get('total_registros', 'N/A')
        st.metric("Total de Registros", total_registros)
        
        # Mostrar tamanho do arquivo se disponível
        tamanho = dados.get('tamanho_arquivo_bytes', 0)
        if tamanho > 0:
            st.caption(f"Tamanho: {tamanho / 1024:.1f} KB")
    
    with col3:
        backup_criado = dados.get('backup_criado', False)
        if backup_criado:
            st.metric("Backup", "✅ Criado")
        else:
            st.metric("Backup", "❌ Não criado")
        
        # Mostrar timestamp
        timestamp = dados.get('timestamp', '')
        if timestamp:
            st.caption(f"Criado em: {timestamp}")
    
    # Mostrar colunas da planilha consolidada
    colunas = dados.get('colunas', [])
    if colunas:
        with st.expander("📋 Estrutura da Planilha Consolidada", expanded=False):
            st.write(f"**Total de colunas:** {len(colunas)}")
            
            # Mostrar colunas principais
            colunas_principais = [col for col in colunas if col not in ['Planilha_Origem', 'Data_Consolidacao', 'ID_Consolidacao']]
            if colunas_principais:
                st.write("**Colunas de dados:**")
                cols_display = st.columns(min(3, len(colunas_principais)))
                for i, col in enumerate(colunas_principais[:9]):  # Mostrar até 9 colunas
                    with cols_display[i % 3]:
                        st.write(f"• {col}")
                
                if len(colunas_principais) > 9:
                    st.caption(f"... e mais {len(colunas_principais) - 9} colunas")
            
            # Mostrar colunas de metadados
            colunas_meta = [col for col in colunas if col in ['Planilha_Origem', 'Data_Consolidacao', 'ID_Consolidacao']]
            if colunas_meta:
                st.write("**Colunas de metadados:**")
                st.write(", ".join(colunas_meta))
    
    # Preview da planilha consolidada
    st.markdown("### 👁️ Preview da Planilha Consolidada")
    
    try:
        # Tentar carregar e exibir preview da planilha mestre
        caminho_arquivo = dados.get('caminho_arquivo', '')
        if not caminho_arquivo:
            # Tentar caminho padrão
            caminho_arquivo = "planilha_mestre/planilha_mestre.xlsx"
        
        if os.path.exists(caminho_arquivo):
            import pandas as pd
            df = pd.read_excel(caminho_arquivo)
            
            if not df.empty:
                st.write(f"**Mostrando as primeiras 10 linhas de {len(df)} registros totais:**")
                
                # Configurar exibição do dataframe
                st.dataframe(
                    df.head(10), 
                    use_container_width=True,
                    height=400
                )
                
                # Estatísticas rápidas
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total de Linhas", len(df))
                with col2:
                    st.metric("Total de Colunas", len(df.columns))
                with col3:
                    # Contar valores não nulos
                    valores_preenchidos = df.count().sum()
                    st.metric("Valores Preenchidos", valores_preenchidos)
                with col4:
                    # Contar planilhas de origem únicas
                    if 'Planilha_Origem' in df.columns:
                        origens_unicas = df['Planilha_Origem'].nunique()
                        st.metric("Planilhas de Origem", origens_unicas)
                
                # Botão para ver dados completos
                if st.button("📊 Ver Todos os Dados", use_container_width=True):
                    st.dataframe(df, use_container_width=True, height=600)
                    
            else:
                st.warning("⚠️ Planilha consolidada está vazia.")
        else:
            st.warning("⚠️ Arquivo da planilha consolidada não encontrado.")
            st.info("📝 Tente executar a consolidação novamente.")
            
    except Exception as e:
        st.error(f"❌ Erro ao carregar preview: {str(e)}")
        st.info("📝 Verifique se a planilha foi criada corretamente.")
    
    # Informações adicionais
    if 'detalhes' in dados:
        with st.expander("🔍 Detalhes Técnicos", expanded=False):
            st.json(dados['detalhes'])
    
    # Mensagem de próximos passos
    st.info("👉 A planilha mestre foi criada! Você pode baixá-la na seção abaixo.")
    
    # Atualizar estado da planilha mestre
    if os.path.exists(caminho_arquivo):
        file_info = os.stat(caminho_arquivo)
        st.session_state.planilha_mestre = {
            'caminho': caminho_arquivo,
            'nome_arquivo': os.path.basename(caminho_arquivo),
            'tamanho': file_info.st_size,
            'data_modificacao': time.strftime('%d/%m/%Y %H:%M:%S', 
                                           time.localtime(file_info.st_mtime))
        }


def _area_download(mestre_disponivel):
    """Área para download da planilha mestre."""
    st.markdown("---")
    st.markdown("### 📥 Download da Planilha Mestre")
    
    # Se não houver planilha mestre disponível
    if not mestre_disponivel:
        st.warning("Nenhuma planilha mestre disponível para download.")
        return
    
    # Mostrar informações da planilha mestre
    planilha = st.session_state.planilha_mestre
    
    st.success("Planilha mestre disponível para download.")
    
    # Mostrar informações detalhadas
    with st.container():
        st.markdown("#### Informações do Arquivo")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("📄 Nome do Arquivo", planilha['nome_arquivo'])
            st.metric("📊 Tamanho", f"{planilha['tamanho'] / 1024:.1f} KB")
        
        with col2:
            st.metric("📅 Última Modificação", planilha['data_modificacao'])
            
            # Verificar integridade do arquivo
            try:
                import pandas as pd
                df = pd.read_excel(planilha['caminho'])
                st.metric("📈 Número de Registros", len(df))
            except Exception as e:
                st.error(f"Erro ao verificar o arquivo: {str(e)}")
    
    # Seção de ações
    with st.expander("🔧 Ações", expanded=True):
        # Botão de download
        _baixar_planilha_mestre()
        
        # Botão para visualizar prévia
        if st.button("👁️ Visualizar Prévia", use_container_width=True):
            try:
                import pandas as pd
                df = pd.read_excel(planilha['caminho'])
                st.dataframe(df.head(), use_container_width=True)
                st.caption(f"Mostrando 5 de {len(df)} registros")
            except Exception as e:
                st.error(f"Erro ao exibir prévia: {str(e)}")
        
        # Botão para verificar erros
        if st.button("🔍 Verificar Erros", use_container_width=True):
            try:
                import pandas as pd
                df = pd.read_excel(planilha['caminho'])
                
                # Verificar valores ausentes
                valores_ausentes = df.isnull().sum()
                colunas_com_erros = valores_ausentes[valores_ausentes > 0]
                
                if len(colunas_com_erros) == 0:
                    st.success("✅ Nenhum valor ausente encontrado.")
                else:
                    st.warning(f"⚠️ Valores ausentes encontrados em {len(colunas_com_erros)} coluna(s):")
                    st.dataframe(colunas_com_erros.rename("Valores Ausentes"), 
                               use_container_width=True)
            except Exception as e:
                st.error(f"Erro ao verificar erros: {str(e)}")
                st.info("Execute uma consolidação primeiro para gerar a planilha mestre.")


def _baixar_planilha_mestre():
    """Baixa a planilha mestre."""
    try:
        with st.spinner("📥 Preparando download..."):
            response = requests.get(f"{API_URL}/download-mestre")
            
            if response.status_code == 200:
                # Criar link para download
                b64 = base64.b64encode(response.content).decode()
                filename = f"planilha_mestre_{time.strftime('%Y%m%d_%H%M%S')}.xlsx"
                
                href = f'''
                <a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" 
                   download="{filename}" 
                   style="display: inline-block; padding: 0.5rem 1rem; background-color: #1E88E5; color: white; 
                          text-decoration: none; border-radius: 0.25rem; font-weight: bold;">
                    📥 Clique aqui para baixar {filename}
                </a>
                '''
                
                st.markdown(href, unsafe_allow_html=True)
                st.success("✅ Download preparado! Clique no link acima para baixar.")
                
            else:
                st.error(f"❌ Erro ao baixar planilha: {response.status_code}")
                
    except Exception as e:
        st.error(f"❌ Erro durante o download: {str(e)}")
