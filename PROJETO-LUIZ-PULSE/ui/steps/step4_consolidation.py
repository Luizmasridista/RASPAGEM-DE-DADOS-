import flet as ft
from typing import Callable, Optional
from models.consolidation_model import ConsolidationResult, ConsolidationStep
from ui.design_system import ds

class Step4Consolidation:
    """Passo 4: Execução da consolidação"""
    
    def __init__(self, page: ft.Page, on_consolidation_complete: Callable[[ConsolidationResult], None], on_next_click: Callable[[], None]):
        self.page = page
        self.on_consolidation_complete = on_consolidation_complete
        self.on_next_click = on_next_click
        self.start_callback = None
        
        # Estado da consolidação
        self.is_running = False
        self.is_completed = False
        self.result = None
        
        # Controles da UI
        self.start_button = None
        self.progress_container = None
        self.overall_progress = ft.ProgressBar(
            width=None,
            height=6,
            value=0,
            bgcolor=ds.colors.NEUTRAL_200,
            color=ds.colors.PRIMARY_600,
            border_radius=ds.border_radius.SM
        )
        self.status_text = ds.create_body_text(
            "Aguardando início da consolidação...",
            size="sm",
            color=ds.colors.NEUTRAL_600
        )
        self.main_progress_bar = self.overall_progress  # Alias para compatibilidade
        self.progress_status_text = self.status_text  # Alias para compatibilidade
        self.progress_percentage_text = ds.create_body_text(
            "0%",
            size="sm",
            weight="bold",
            color=ds.colors.NEUTRAL_800
        )
        self.next_button_container = ft.Container(visible=False)  # Container para botão de próximo passo
        self.step_progress_bars = {}
        self.step_status_texts = {}
        self.container = None
        
        # Passos da consolidação
        self.consolidation_steps = [
            {"id": 1, "name": "Validação", "description": "Validando arquivos e configurações"},
            {"id": 2, "name": "Preparação", "description": "Preparando arquivos para consolidação"},
            {"id": 3, "name": "Leitura", "description": "Lendo dados dos arquivos subordinados"},
            {"id": 4, "name": "Consolidação", "description": "Consolidando dados na planilha mestre"},
            {"id": 5, "name": "Formatação", "description": "Aplicando formatação das planilhas subordinadas"},
            {"id": 6, "name": "Backup e Finalização", "description": "Criando backup e finalizando processo"},
        ]
        
    def set_start_callback(self, callback: Callable[[], None]):
        """Define o callback para iniciar a consolidação"""
        self.start_callback = callback
        
    def build(self):
        """Constrói a interface da etapa de consolidação"""
        print("[Step4] Iniciando build() da Step4")
        try:
            # Reseta o estado para iniciar limpo
            print("[Step4] Resetando estado inicial...")
            self.reset()  
            
            # Título e descrição da etapa
            print("[Step4] Criando cabeçalho...")
            header_container = ft.Container(
                content=ft.Column([
                    ds.create_heading("Consolidação", "Executar processo de consolidação"),
                    ds.create_body_text(
                        "Inicie o processo de consolidação dos arquivos subordinados no arquivo mestre.",
                        size="md",
                        color=ds.colors.NEUTRAL_700
                    ),
                ], spacing=ds.spacing.SM),
                padding=ft.padding.all(ds.spacing.LG),
                bgcolor=ds.colors.BACKGROUND,
                border_radius=ds.border_radius.LG,
                border=ft.border.all(1, ds.colors.NEUTRAL_200)
            )
            
            # Botão para iniciar a consolidação - MUITO IMPORTANTE
            print("[Step4] Criando botão de início...")
            self.start_button = ft.ElevatedButton(
                content=ft.Row([
                    ft.Icon(name=ft.icons.PLAY_ARROW, color="#FFFFFF"),
                    ft.Text(value="Iniciar Consolidação", color="#FFFFFF"),
                ], alignment=ft.MainAxisAlignment.CENTER),
                style=ds.get_button_style("primary", "large"),
                on_click=self._handle_start,
                # Forçando visibilidade do botão
                visible=True,
                disabled=False,
                width=300
            )
            
            # Container com botão centralizado
            start_button_container = ft.Container(
                content=ft.Row([
                    self.start_button
                ], alignment=ft.MainAxisAlignment.CENTER),
                padding=ft.padding.all(ds.spacing.LG),
                bgcolor=ds.colors.BACKGROUND,
                border_radius=ds.border_radius.LG,
                border=ft.border.all(1, ds.colors.NEUTRAL_200),
                # Forçando visibilidade do container
                visible=True
            )
            
            # Texto de debug visível para o usuário
            debug_text = ds.create_body_text(
                "Interface de consolidação carregada. Clique no botão acima para iniciar.",
                size="sm",
                color=ds.colors.SUCCESS,
                italic=True
            )
            
            # Container para o progresso global da consolidação (inicialmente oculto)
            print("[Step4] Criando containers de progresso...")
            self.progress_container = ft.Container(
                visible=False,  # Inicialmente oculto
                content=ft.Column([
                    # Título do progresso
                    ds.create_body_text(
                        "Progresso da consolidação",
                        size="lg",
                        weight="bold",
                        color=ds.colors.NEUTRAL_900
                    ),
                    ft.Container(height=ds.spacing.MD),
                    
                    # Barra de progresso global
                    self.overall_progress,
                    ft.Container(height=ds.spacing.XS),
                    
                    # Status do progresso
                    ft.Row([
                        self.status_text,
                        ft.Container(width=ds.spacing.SM),
                    ]),
                    ft.Container(height=ds.spacing.LG),
                    
                    # Passos da consolidação
                    ft.Column(self._build_progress_steps(), spacing=ds.spacing.MD, tight=True)
                ]),
                padding=ft.padding.all(ds.spacing.LG),
                bgcolor=ds.colors.BACKGROUND,
                border_radius=ds.border_radius.LG,
                border=ft.border.all(1, ds.colors.NEUTRAL_200)
            )
            
            # Estrutura principal
            print("[Step4] Montando container principal...")
            main_container = ft.Container(
                content=ft.Column([
                    header_container,
                    ft.Container(height=ds.spacing.MD),
                    start_button_container,
                    ft.Container(
                        content=ft.Row([debug_text], alignment=ft.MainAxisAlignment.CENTER),
                        padding=ft.padding.symmetric(vertical=ds.spacing.SM)
                    ),
                    ft.Container(height=ds.spacing.MD),
                    self.progress_container,
                ], spacing=0, tight=True),
                padding=ft.padding.all(ds.spacing.LG),
                bgcolor=ds.colors.SURFACE,
                expand=True,
                border_radius=ds.border_radius.LG,
                scroll=ft.ScrollMode.AUTO  # Adiciona scroll para garantir visibilidade em telas pequenas
            )
            
            print("[Step4] build() concluído com sucesso")
            return main_container
        except Exception as e:
            print(f"[Step4] ERRO ao construir UI: {e}")
            import traceback
            traceback.print_exc()
            # Retorna uma mensagem de erro visível para o usuário
            return ft.Container(
                content=ft.Column([
                    ft.Icon(name=ft.icons.ERROR_OUTLINE, color=ds.colors.ERROR, size=48),
                    ft.Text("Erro ao carregar a interface de consolidação", color=ds.colors.ERROR),
                    ft.Text(f"Detalhes: {str(e)}", size=12, color=ds.colors.NEUTRAL_600),
                    ft.Container(height=20),
                    ft.ElevatedButton(
                        "Tentar novamente",
                        on_click=lambda _: self.page.go("/")
                    )
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                alignment=ft.alignment.center,
                padding=20,
                expand=True
            )
    
    def _build_progress_steps(self):
        """Constrói os controles de progresso para cada passo"""
        steps_controls = []
        
        for step in self.consolidation_steps:
            step_id = step["id"]
            
            # Ícone do status com design profissional
            status_icon = ft.Icon(
                ft.Icons.RADIO_BUTTON_UNCHECKED,
                color=ds.colors.NEUTRAL_400,
                size=20,
            )
            
            # Texto do passo com tipografia padronizada
            step_title = ds.create_body_text(
                f"{step_id}. {step['name']}",
                size="base",
                weight=ft.FontWeight.W_600,
                color=ds.colors.NEUTRAL_800
            )
            
            step_description = ds.create_body_text(
                step["description"],
                size="sm",
                color=ds.colors.NEUTRAL_600
            )
            
            # Barra de progresso individual
            progress_bar = ft.ProgressBar(
                width=350,
                height=4,
                value=0,
                visible=True,
                bgcolor=ds.colors.NEUTRAL_200,
                color=ds.colors.SUCCESS,
                border_radius=ds.border_radius.SM
            )
            
            # Texto de status
            status_text = ds.create_body_text(
                "Aguardando...",
                size="xs",
                color=ds.colors.NEUTRAL_500
            )
            
            # Armazena referências
            self.step_progress_bars[step_id] = progress_bar
            self.step_status_texts[step_id] = status_text
            
            # Container do passo com design profissional
            step_container = ft.Container(
                content=ft.Row([
                    status_icon,
                    ft.Container(width=ds.spacing.BASE),
                    ft.Column([
                        step_title,
                        step_description,
                        ft.Container(height=ds.spacing.SM),
                        progress_bar,
                        ft.Container(height=ds.spacing.XS),
                        status_text,
                    ], 
                    spacing=0,
                    expand=True),
                ], 
                alignment=ft.MainAxisAlignment.START),
                padding=ft.padding.all(ds.spacing.BASE),
                margin=ft.margin.only(bottom=ds.spacing.SM),
                bgcolor=ds.colors.BACKGROUND,
                border_radius=ds.border_radius.BASE,
                border=ft.border.all(1, ds.colors.BORDER),
            )
            
            # Armazena referência do ícone para atualizações
            setattr(step_container, 'status_icon', status_icon)
            
            steps_controls.append(step_container)
        
        return steps_controls
    
    def _handle_start(self, e):
        """Inicia o processo de consolidação"""
        print("[Step4] Botão 'Iniciar Consolidação' clicado")
        if self.start_callback and not self.is_running and not self.is_completed:
            # Atualiza estado
            self.is_running = True
            
            # Atualiza UI - oculta botão e mostra progresso
            self.start_button.visible = False
            self.overall_progress.visible = True
            self.status_text.visible = True
            self.progress_container.visible = True
            
            # Inicializa barras de progresso
            for step_id in self.step_progress_bars:
                self.step_progress_bars[step_id].value = 0
                self.step_status_texts[step_id].value = "Aguardando..."
                self.step_status_texts[step_id].color = ds.colors.NEUTRAL_500
            
            # Força atualização da UI antes de iniciar a consolidação
            print("[Step4] Atualizando UI antes de iniciar consolidação")
            self.page.update()
            
            # Inicia consolidação com pequeno delay para garantir UI atualizada
            print("[Step4] Chamando start_callback para iniciar consolidação")
            # Usar thread para não bloquear a UI
            import threading, time
            def delayed_start():
                time.sleep(0.5)  # Pequeno delay para garantir que a UI seja atualizada
                self.start_callback()
            
            thread = threading.Thread(target=delayed_start)
            thread.daemon = True
            thread.start()
    
    def update_progress(self, step_id: int, status: str, progress: float):
        """Atualiza o progresso de um passo específico"""
        print(f"[Step4] Atualizando progresso: step_id={step_id}, status={status}, progress={progress}")
        
        # Garante que os elementos de progresso estão visíveis
        self.overall_progress.visible = True
        self.status_text.visible = True
        self.progress_container.visible = True
        self.start_button.visible = False
        
        if step_id in self.step_progress_bars:
            progress_bar = self.step_progress_bars[step_id]
            status_text = self.step_status_texts[step_id]
            
            # Atualiza barra de progresso
            progress_bar.value = progress / 100.0
            
            # Atualiza texto de status
            status_text.value = status
            
            # Atualiza ícone baseado no progresso
            step_container = progress_bar.parent.parent.parent
            if hasattr(step_container, 'status_icon'):
                icon = step_container.status_icon
                if progress >= 100:
                    icon.name = ft.Icons.CHECK_CIRCLE
                    icon.color = ds.colors.SUCCESS
                    status_text.color = ds.colors.SUCCESS
                elif progress > 0:
                    icon.name = ft.Icons.HOURGLASS_TOP
                    icon.color = ds.colors.WARNING
                    status_text.color = ds.colors.WARNING
            
            # Atualiza progresso geral
            total_progress = sum(bar.value for bar in self.step_progress_bars.values()) / len(self.step_progress_bars)
            self.overall_progress.value = total_progress
            
            # Atualiza status geral
            if total_progress >= 1.0:
                self.status_text.value = "Consolidação concluída com sucesso!"
                self.status_text.color = ds.colors.SUCCESS
            else:
                current_step = next((s for s in self.consolidation_steps if s["id"] == step_id), None)
                if current_step:
                    self.status_text.value = f"Executando: {current_step['name']}..."
        
        # Força atualização da UI
        try:
            self.page.update()
            print(f"[Step4] UI atualizada com sucesso para step_id={step_id}")
        except Exception as e:
            print(f"[Step4] Erro ao atualizar UI: {e}")
            import traceback
            traceback.print_exc()
    
    def on_consolidation_finished(self, result: ConsolidationResult):
        """Chamado quando a consolidação é finalizada"""
        print(f"[Step4] Consolidação finalizada: success={result.success}, rows_added={result.total_rows_added}")
        self.is_running = False
        self.is_completed = True
        self.result = result
        
        # Atualiza status final
        if result.success:
            self.status_text.value = f"Consolidação concluída! {result.total_rows_added} linhas adicionadas."
            self.status_text.color = ds.colors.SUCCESS
        else:
            self.status_text.value = "Consolidação falhou. Verifique os erros."
            self.status_text.color = ds.colors.ERROR
        
        # Adiciona botão para próximo passo com design profissional
        if result.success:
            next_button = ft.ElevatedButton(
                content=ft.Row([
                    ft.Text("Ver Resultados", size=16, weight=ft.FontWeight.W_500, color="#FFFFFF"),
                    ft.Icon(ft.Icons.ARROW_FORWARD, size=20, color="#FFFFFF")
                ], 
                alignment=ft.MainAxisAlignment.CENTER,
                tight=True),
                on_click=self._handle_next,
                style=ds.get_button_style("primary", "medium"),
                width=200
            )
            
            # Container para o botão de próximo
            next_container = ft.Container(
                content=ft.Row([
                    next_button
                ], alignment=ft.MainAxisAlignment.CENTER),
                margin=ft.margin.only(top=ds.spacing.LG)
            )
            
            # Adiciona o botão ao layout
            # Acessa a coluna principal dentro do container de progresso
            main_column = self.progress_container.content
            main_column.controls.append(next_container)
        
        # Atualiza a UI
        try:
            self.page.update()
            print("[Step4] UI atualizada após finalização da consolidação")
        except Exception as e:
            print(f"[Step4] Erro ao atualizar UI após finalização: {e}")
            import traceback
            traceback.print_exc()
    
    def _handle_next(self, e):
        """Lida com o clique no botão próximo"""
        print("[Step4] Botão 'Ver Resultados' clicado")
        if self.on_next_click:
            self.on_next_click()
    
    def reset(self):
        """Reseta o componente ao estado inicial"""
        self.is_running = False
        self.is_completed = False
        self.result = None
        
        # Reseta botão de início
        if self.start_button:
            self.start_button.visible = True
            self.start_button.disabled = False

        if self.progress_container:
            self.progress_container.visible = False
        
        if self.overall_progress:
            self.overall_progress.value = 0
        
        if self.status_text:
            self.status_text.value = "Aguardando início da consolidação..."
            self.status_text.color = ds.colors.NEUTRAL_600
        
        # Reseta progresso dos passos
        for step_id in self.step_progress_bars:
            progress_bar = self.step_progress_bars[step_id]
            status_text = self.step_status_texts[step_id]

            progress_bar.value = 0
            status_text.value = "Aguardando..."
            status_text.color = ds.colors.NEUTRAL_500
            
            # Reseta ícones
            step_container = progress_bar.parent.parent.parent
            if hasattr(step_container, 'status_icon'):
                icon = step_container.status_icon
                icon.name = ft.icons.RADIO_BUTTON_UNCHECKED
                icon.color = ds.colors.NEUTRAL_400
        
        # Atualiza a UI
        try:
            self.page.update()
            print("[Step4] Componente resetado com sucesso")
        except Exception as e:
            print(f"[Step4] Erro ao resetar componente: {e}")
            import traceback
            traceback.print_exc()