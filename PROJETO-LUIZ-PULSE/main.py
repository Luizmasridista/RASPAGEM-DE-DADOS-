import flet as ft
import threading
import os
import sys

# Configuração robusta do sys.path para resolver importações
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Adiciona também o diretório pai caso esteja sendo executado em modo debug
parent_dir = os.path.dirname(project_root)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
from services.session_manager import SessionManager
from services.file_service import FileService
from models.consolidation_model import ConsolidationConfig
from ui.sidebar import Sidebar
from ui.steps.step1_master_file import Step1MasterFile
from ui.steps.step2_upload_files import Step2UploadFiles
from ui.steps.step3_configuration import Step3Configuration
from ui.steps.step4_consolidation import Step4Consolidation
from ui.steps.step5_results import Step5Results

class ConsolidationApp:
    """Aplicação principal de consolidação de dados"""
    
    def __init__(self):
        self.session_manager = SessionManager()
        self.file_service = FileService()
        
        # Componentes da UI
        self.sidebar = None
        self.step1 = None
        self.step2 = None
        self.step3 = None
        self.step4 = None
        self.step5 = None
        
        # Container principal do conteúdo
        self.content_container = ft.Container(
            content=ft.Text("Carregando...", size=20),
            padding=ft.padding.all(20),
            expand=True
        )
    
    def main(self, page: ft.Page):
        """Função principal da aplicação"""
        self.page = page
        page.title = "Sistema de Consolidação de Dados"
        page.window_width = 1200
        page.window_height = 800
        page.window_min_width = 800
        page.window_min_height = 600
        page.theme_mode = ft.ThemeMode.LIGHT
        
        # Cria pasta de backups se não existir
        if not os.path.exists("backups"):
            os.makedirs("backups")
        
        # Inicializa componentes
        print("[Main] Inicializando componentes...")
        self._initialize_components(page)
        print("[Main] Componentes inicializados.")
        
        # Verifica se sidebar foi inicializado
        if self.sidebar is None:
            print("[Main] ERRO: Sidebar não foi inicializado!")
            self.sidebar = Sidebar(
                steps=[{"id": 1, "name": "Passo 1", "description": "Descrição 1"}],
                current_step=1
            )
        
        # Layout principal
        print("[Main] Construindo layout principal...")
        main_layout = ft.Row([
            self.sidebar.build() if self.sidebar else ft.Container(content=ft.Text("Sidebar não inicializado")),
            self.content_container if self.content_container else ft.Container(content=ft.Text("Conteúdo não inicializado"))
        ], spacing=0, expand=True)
        
        print("[Main] Adicionando layout à página...")
        page.add(main_layout)
        print("[Main] Layout adicionado.")
        
        # Mostra o primeiro passo
        self._show_step(1)
        page.update()
        print("[Main] Primeiro passo exibido.")
    
    def _initialize_components(self, page: ft.Page):
        """Inicializa todos os componentes da UI"""
        # Define os passos do processo
        steps = [
            {"id": 1, "name": "Arquivo Mestre", "description": "Selecione o arquivo Excel principal"},
            {"id": 2, "name": "Arquivos Subordinados", "description": "Carregue os arquivos para consolidação"},
            {"id": 3, "name": "Configuração", "description": "Configure as opções de consolidação"},
            {"id": 4, "name": "Consolidação", "description": "Execute o processo de consolidação"},
            {"id": 5, "name": "Resultados", "description": "Visualize os resultados da consolidação"}
        ]
        
        print("[Init] Inicializando Sidebar...")
        # Sidebar
        self.sidebar = Sidebar(
            steps=steps,
            current_step=1,
            on_step_click=self._on_step_change,
            on_reset=self._on_new_session
        )
        print("[Init] Sidebar inicializado.")
        
        print("[Init] Inicializando Steps...")
        # Steps
        self.step1 = Step1MasterFile(page, self._on_master_file_selected, self._on_step_back, self.file_service)
        print("[Init] Step1 inicializado.")
        self.step2 = Step2UploadFiles(page, self._on_step2_next, self._on_step_back, self._on_subordinate_files_updated, self.file_service)
        print("[Init] Step2 inicializado.")
        self.step3 = Step3Configuration(page, self._on_configuration_set)
        print("[Init] Step3 inicializado.")
        self.step4 = Step4Consolidation(page, self._on_consolidation_complete, self._on_next_step)
        print("[Init] Step4 inicializado.")
        self.step5 = Step5Results(page, self._on_new_session)
        print("[Init] Step5 inicializado.")
        
        # Configura callback de consolidação
        self.step4.set_start_callback(self._start_consolidation)
        print("[Init] Callback de consolidação configurado.")
    
    def _on_step_change(self, step: int):
        """Manipula mudança de passo"""
        if step == 0:  # Reset
            self._reset_session()
            return
        
        # Verifica se pode navegar para o passo
        if self.session_manager.can_proceed_to_step(step):
            self.session_manager.set_current_step(step)
            self._show_step(step)
            self._update_sidebar()
        else:
            self._show_error("Você precisa completar os passos anteriores primeiro.")
    
    def _show_step(self, step: int):
        """Exibe o passo especificado"""
        print(f"[ShowStep] Solicitação para exibir passo {step}")
        
        try:
            # Atualiza o passo atual na sessão
            self.session_manager.set_current_step(step)
            print(f"[ShowStep] Sessão atualizada para passo {step}")
            
            # Limpa o conteúdo atual antes de carregar o novo passo
            self.content_container.content = None
            self.content_container.update()
            print("[ShowStep] Conteúdo limpo para evitar conflitos")
            
            # Cria o conteúdo do novo passo
            if step == 1:
                print("[ShowStep] Construindo Step1")
                self.content_container.content = self.step1.build()
                print("[ShowStep] Step1 construído com sucesso")
            elif step == 2:
                print("[ShowStep] Construindo Step2")
                self.content_container.content = self.step2.build()
                print("[ShowStep] Step2 construído com sucesso")
            elif step == 3:
                print("[ShowStep] Construindo Step3")
                self.content_container.content = self.step3.build()
                print("[ShowStep] Step3 construído com sucesso")
            elif step == 4:
                print("[ShowStep] Construindo Step4")
                if self.step4 is None:
                    print("[ShowStep] ERRO CRÍTICO: self.step4 é None")
                    return
                    
                try:
                    # Constrói Step4 com logs adicionais
                    print("[ShowStep] Chamando step4.build()...")
                    step4_content = self.step4.build()
                    print(f"[ShowStep] step4.build() retornou: {type(step4_content)}")
                    
                    # Atribui o conteúdo ao container
                    print("[ShowStep] Atribuindo conteúdo da Step4 ao container")
                    self.content_container.content = step4_content
                    print("[ShowStep] Step4 construído com sucesso")
                    
                    # Registramos o início automático da consolidação mas o desativamos por enquanto
                    # para garantir que a UI esteja visível primeiro
                    print("[ShowStep] Início automático da consolidação temporariamente desativado")
                    print("[ShowStep] Usuário precisará clicar no botão 'Iniciar Consolidação'")
                    
                except Exception as step4_error:
                    print(f"[ShowStep] ERRO ao construir Step4: {step4_error}")
                    import traceback
                    traceback.print_exc()
            elif step == 5:
                print("[ShowStep] Construindo Step5")
                self.content_container.content = self.step5.build()
                print("[ShowStep] Step5 construído com sucesso")
            
            # Força atualização da UI com retry
            print(f"[ShowStep] Atualizando container de conteúdo")
            try:
                self.content_container.update()
                print("[ShowStep] Container atualizado com sucesso")
            except Exception as ui_error:
                print(f"[ShowStep] Erro ao atualizar container: {ui_error}")
            
            try:
                self.page.update()
                print("[ShowStep] Página atualizada com sucesso")
            except Exception as page_error:
                print(f"[ShowStep] Erro ao atualizar página: {page_error}")
                
            print(f"[ShowStep] Passo {step} exibido com sucesso.")
        except Exception as e:
            print(f"[ShowStep] ERRO GERAL ao exibir passo {step}: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_sidebar(self):
        """Atualiza o estado do sidebar"""
        current_step = self.session_manager.get_current_step()
        enabled_steps = []
        
        # Determina quais passos estão habilitados
        for i in range(1, 6):
            if self.session_manager.can_proceed_to_step(i):
                enabled_steps.append(i)
        
        self.sidebar.set_current_step(current_step)
    
    def _on_master_file_selected(self, file_path: str):
        """Manipula seleção do arquivo mestre"""
        file_info = self.file_service.get_file_info(file_path)
        
        if file_info:
            self.session_manager.set_master_file(file_info)
            
            # Configura informações no step 3
            sheet_name = self.step1.sheet_dropdown.value
            self.step3.set_master_info(file_path, sheet_name)
            
            # Avança para próximo passo
            self.session_manager.next_step()
            self._show_step(2)
            self._update_sidebar()
        else:
            self._show_error("Erro ao processar arquivo mestre.")
    
    def _on_step2_next(self, files: list):
        """Callback when next is clicked in step 2. Adds files to session and advances to step 3."""
        for file in files:
            self.session_manager.add_subordinate_file(file)
        self._on_step_change(3)
    
    def _on_subordinate_files_updated(self, files):
        """Manipula atualização dos arquivos subordinados"""
        # Limpa lista atual
        self.session_manager.subordinate_files = []
        
        # Adiciona novos arquivos
        for file_info in files:
            self.session_manager.add_subordinate_file(file_info)
        
        # Avança para próximo passo
        self.session_manager.next_step()
        self._show_step(3)
        self._update_sidebar()
    
    def _on_configuration_set(self, config: ConsolidationConfig):
        """Manipula configuração da consolidação"""
        print(f"[Main] _on_configuration_set chamado com config: {config}")
        
        try:
            # Salva configuração na sessão
            self.session_manager.set_consolidation_config(config)
            print("[Main] Configuração salva na sessão com sucesso")
            
            # Avança para próximo passo
            print("[Main] Avançando para o passo 4 (Consolidação)")
            self.session_manager.next_step()
            
            # Garante que a sessão está no passo correto
            current_step = self.session_manager.get_current_step()
            print(f"[Main] Passo atual na sessão: {current_step}")
            
            # Verifica se step4 existe
            if not self.step4:
                print("[Main] ERRO: self.step4 não foi inicializado. Recriando...")
                from ui.steps.step4_consolidation import Step4Consolidation
                self.step4 = Step4Consolidation(
                    page=self.page,
                    next_callback=self._on_consolidation_complete
                )
                self.step4.set_start_callback(self._start_consolidation)
                print("[Main] Step4 recriado")
                
            # Força a exibição do passo 4 com timeout para garantir tempo de processamento
            import time
            print("[Main] Aguardando 0.5s para garantir que a sessão está pronta...")
            time.sleep(0.5)
            self._show_step(4)
            
            # Atualiza a barra lateral
            self._update_sidebar()
            
            # Garante que a UI seja atualizada
            print("[Main] Forçando atualização da UI")
            self.page.update()
            print("[Main] Navegação para o passo 4 concluída")
        
        except Exception as e:
            print(f"[Main] ERRO ao navegar para o passo 4: {e}")
            import traceback
            traceback.print_exc()
    
    def _start_consolidation(self):
        """Inicia o processo de consolidação em thread separada"""
        def run_consolidation():
            try:
                result = self.session_manager.start_consolidation(
                    progress_callback=self._on_consolidation_progress
                )
                
                # Atualiza UI no thread principal
                self.step4.on_consolidation_finished(result)
                self.content_container.update()
                
            except Exception as e:
                print(f"Erro na consolidação: {e}")
        
        # Executa em thread separada
        thread = threading.Thread(target=run_consolidation)
        thread.daemon = True
        thread.start()
    
    def _on_consolidation_progress(self, step_id: int, status: str, progress: float):
        """Manipula progresso da consolidação"""
        self.step4.update_progress(step_id, status, progress)
        self.content_container.update()
    
    def _on_consolidation_complete(self, result):
        """Manipula conclusão da consolidação"""
        # Avança para próximo passo
        self.session_manager.next_step()
        self._show_step(5)
        self.step5.show_results(result)
        self._update_sidebar()
        
        # Backup já é criado no ConsolidationService após consolidação bem-sucedida
        print(f"[Main] Consolidação concluída: {result.success}, Backup: {result.backup_path}")
    
    def _on_new_session(self):
        """Inicia nova sessão"""
        self._reset_session()
    
    def _reset_session(self):
        """Reseta a sessão"""
        self.session_manager.reset_session()
        
        # Reseta componentes
        self.step1.reset()
        self.step2.reset()
        self.step3.reset()
        self.step4.reset()
        self.step5.reset()
        
        # Volta para o primeiro passo
        self._show_step(1)
        self._update_sidebar()
    
    def _show_error(self, message: str):
        """Exibe mensagem de erro"""
        # Implementação básica - pode ser melhorada
        print(f"Erro: {message}")
    
    def _on_step_back(self):
        """Manipula navegação para o passo anterior"""
        current_step = self.session_manager.get_current_step()
        if current_step > 1:
            self.session_manager.set_current_step(current_step - 1)
            self._show_step(current_step - 1)
            self._update_sidebar()
    
    def _on_next_step(self):
        """Manipula avanço para o próximo passo"""
        print("[Main] Avançando para a próxima etapa")
        self._show_step(5)  # Avança para a etapa 5 (Resultados)

def main(page: ft.Page):
    """Função principal para Flet"""
    app = ConsolidationApp()
    app.main(page)

if __name__ == "__main__":
    ft.app(target=main)
