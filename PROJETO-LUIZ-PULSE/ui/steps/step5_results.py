import flet as ft
import os
from typing import Callable, Optional
from models.consolidation_model import ConsolidationResult

class Step5Results:
    """Passo 5: Exibição dos resultados da consolidação"""
    
    def __init__(self, page: ft.Page, on_new_session: Callable[[], None]):
        self.page = page
        self.on_new_session = on_new_session
        self.result = None
        
        # Controles da UI
        self.results_container = None
        self.container = None
        
    def build(self):
        # Título e descrição
        title = ft.Text("5. Resultados da Consolidação", size=20, weight=ft.FontWeight.BOLD)
        description = ft.Text(
            "Confira os resultados da consolidação e as ações disponíveis.",
            size=14,
            color="#757575",
        )
        
        # Container para os resultados
        self.results_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.INFO_OUTLINE, color="#42A5F5", size=18),
                            ft.Text("Os resultados serão exibidos aqui após a consolidação", 
                                   italic=True, color="#9E9E9E"),
                        ],
                        spacing=10,
                    ),
                ],
                spacing=10,
            ),
            padding=ft.padding.all(20),
            bgcolor="#ECEFF1",
            border_radius=10,
            border=ft.border.all(1, "#CFD8DC"),
        )
        
        # Botões de ação
        new_session_button = ft.ElevatedButton(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.REFRESH, size=18),
                    ft.Text("Nova Consolidação"),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            on_click=self._handle_new_session,
            width=200,
            height=45,
            style=ft.ButtonStyle(
                shape={
                    ft.ControlState.DEFAULT: ft.RoundedRectangleBorder(radius=8),
                },
                padding=10,
                bgcolor="#1976D2",
                color="#FFFFFF",
            ),
        )
        
        self.container = ft.Container(
            content=ft.Column(
                controls=[
                    title,
                    description,
                    ft.Container(height=30),
                    self.results_container,
                    ft.Container(height=30),
                    ft.Row(
                        controls=[new_session_button],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                spacing=0,
                expand=True,
            ),
            padding=ft.padding.all(30),
        )
        return self.container
    
    def show_results(self, result: ConsolidationResult):
        """Exibe os resultados da consolidação"""
        self.result = result
        
        if result.success:
            self._show_success_results(result)
        else:
            self._show_error_results(result)
        
        self.update()
    
    def _show_success_results(self, result: ConsolidationResult):
        """Exibe resultados de sucesso"""
        # Ícone de sucesso
        success_header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.CHECK_CIRCLE, color="#4CAF50", size=32),
                    ft.Text("Consolidação Concluída com Sucesso!", 
                           size=18, weight=ft.FontWeight.BOLD, color="#388E3C"),
                ],
                spacing=15,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=ft.padding.all(15),
            bgcolor="#E8F5E9",
            border_radius=8,
            border=ft.border.all(2, "#C8E6C9"),
        )
        
        # Estatísticas principais
        stats_cards = ft.Row(
            controls=[
                self._create_stat_card(
                    "Arquivos Processados",
                    str(result.total_files_processed),
                    ft.Icons.FOLDER_OPEN,
                    "#1976D2"
                ),
                self._create_stat_card(
                    "Linhas Adicionadas",
                    str(result.total_rows_added),
                    ft.Icons.ADD_BOX,
                    "#4CAF50"
                ),
                self._create_stat_card(
                    "Tempo de Execução",
                    f"{result.execution_time:.1f}s",
                    ft.Icons.TIMER,
                    "#FF9800"
                ),
                self._create_stat_card(
                    "Formatação",
                    "Aplicada" if self._formatting_applied(result) else "N/A",
                    ft.Icons.PALETTE,
                    "#9C27B0"
                ),
            ],
            spacing=15,
            alignment=ft.MainAxisAlignment.CENTER,
        )
        
        # Informações do backup
        backup_info = None
        if result.backup_path:
            backup_filename = os.path.basename(result.backup_path)
            backup_info = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.BACKUP, color="#FFC107", size=20),
                                ft.Text("Backup Criado:", weight=ft.FontWeight.BOLD),
                            ],
                            spacing=10,
                        ),
                        ft.Row(
                            controls=[
                                ft.Text(backup_filename, color="#FFA000"),
                                ft.IconButton(
                                    icon=ft.Icons.FOLDER_OPEN,
                                    tooltip="Abrir pasta do backup",
                                    on_click=lambda e: self._open_backup_folder(result.backup_path),
                                ),
                            ],
                            spacing=10,
                        ),
                    ],
                    spacing=5,
                ),
                padding=ft.padding.all(15),
                bgcolor="#FFF8E1",
                border_radius=8,
                border=ft.border.all(1, "#FFD700"),
            )
        
        # Detalhes dos passos
        steps_details = self._create_steps_summary(result.steps)
        
        # Atualiza o container de resultados
        controls = [success_header, ft.Container(height=20), stats_cards]
        
        if backup_info:
            controls.extend([ft.Container(height=20), backup_info])
        
        if steps_details:
            controls.extend([ft.Container(height=20), steps_details])
        
        self.results_container.content = ft.Column(
            controls=controls,
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    
    def _show_error_results(self, result: ConsolidationResult):
        """Exibe resultados de erro"""
        # Ícone de erro
        error_header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.ERROR, color="#F44336", size=32),
                    ft.Text("Consolidação Falhou", 
                           size=18, weight=ft.FontWeight.BOLD, color="#D32F2F"),
                ],
                spacing=15,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=ft.padding.all(15),
            bgcolor="#FFEBEE",
            border_radius=8,
            border=ft.border.all(2, "#FFCDD2"),
        )
        
        # Lista de erros
        error_list = ft.Column(
            controls=[
                ft.Text("Erros encontrados:", weight=ft.FontWeight.BOLD, color="#F44336"),
            ],
            spacing=5,
        )
        
        for error in result.errors:
            error_item = ft.Row(
                controls=[
                    ft.Icon(ft.Icons.ERROR_OUTLINE, color="#F44336", size=16),
                    ft.Text(error, color="#F44336", size=12),
                ],
                spacing=8,
            )
            error_list.controls.append(error_item)
        
        error_container = ft.Container(
            content=error_list,
            padding=ft.padding.all(15),
            bgcolor="#FFEBEE",
            border_radius=8,
            border=ft.border.all(1, "#FFCDD2"),
        )
        
        # Detalhes dos passos (se houver)
        steps_details = self._create_steps_summary(result.steps)
        
        # Atualiza o container de resultados
        controls = [error_header, ft.Container(height=20), error_container]
        
        if steps_details:
            controls.extend([ft.Container(height=20), steps_details])
        
        self.results_container.content = ft.Column(
            controls=controls,
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    
    def _create_stat_card(self, title: str, value: str, icon, color):
        """Cria um cartão de estatística"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(icon, color=color, size=24),
                    ft.Text(value, size=20, weight=ft.FontWeight.BOLD, color=color),
                    ft.Text(title, size=12, color="#757575", text_align=ft.TextAlign.CENTER),
                ],
                spacing=8,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.all(20),
            bgcolor="#FFFFFF",
            border_radius=10,
            border=ft.border.all(1, "#E0E0E0"),
            width=150,
            height=120,
        )
    
    def _create_steps_summary(self, steps):
        """Cria um resumo dos passos executados"""
        if not steps:
            return None
        
        steps_list = ft.Column(
            controls=[
                ft.Text("Detalhes da Execução:", weight=ft.FontWeight.BOLD),
            ],
            spacing=8,
        )
        
        for step in steps:
            # Ícone baseado no status
            if step.status == "completed":
                icon = ft.Icon(ft.Icons.CHECK_CIRCLE, color="#4CAF50", size=16)
            elif step.status == "error":
                icon = ft.Icon(ft.Icons.ERROR, color="#F44336", size=16)
            else:
                icon = ft.Icon(ft.Icons.RADIO_BUTTON_UNCHECKED, color="#9E9E9E", size=16)
            
            step_row = ft.Row(
                controls=[
                    icon,
                    ft.Text(f"{step.id}. {step.name}", size=12),
                    ft.Text(f"({step.progress:.0f}%)", size=11, color="#757575"),
                ],
                spacing=8,
            )
            
            steps_list.controls.append(step_row)
            
            # Adiciona mensagem de erro se houver
            if step.error_message:
                error_text = ft.Text(
                    f"   Erro: {step.error_message}",
                    size=11,
                    color="#F44336",
                    italic=True,
                )
                steps_list.controls.append(error_text)
        
        return ft.Container(
            content=steps_list,
            padding=ft.padding.all(15),
            bgcolor="#ECEFF1",
            border_radius=8,
            border=ft.border.all(1, "#CFD8DC"),
            width=400,
        )
    
    def _formatting_applied(self, result: ConsolidationResult) -> bool:
        """Verifica se a formatação foi aplicada com sucesso"""
        try:
            # Verifica se o step 5 (formatação) foi concluído com sucesso
            if result.steps:
                formatting_step = next((step for step in result.steps if step.id == 5), None)
                if formatting_step:
                    return formatting_step.status == "completed" and not formatting_step.error_message
            
            # Se não encontrou o step, verifica se houve erros relacionados à formatação
            if result.errors:
                formatting_errors = [error for error in result.errors if "formatação" in error.lower()]
                return len(formatting_errors) == 0
            
            return True  # Assume que foi aplicada se não há informações em contrário
        except Exception as e:
            print(f"Erro ao verificar formatação: {e}")
            return False
    
    def _open_backup_folder(self, backup_path: str):
        """Abre a pasta onde o backup foi salvo"""
        try:
            import subprocess
            import platform
            
            folder_path = os.path.dirname(backup_path)
            
            if platform.system() == "Windows":
                subprocess.run(["explorer", folder_path])
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", folder_path])
            else:  # Linux
                subprocess.run(["xdg-open", folder_path])
        except Exception as e:
            print(f"Erro ao abrir pasta: {e}")
    
    def _handle_new_session(self, e):
        """Lida com o clique no botão de nova sessão"""
        if self.on_new_session:
            self.on_new_session()
    
    def reset(self):
        """Reseta o componente ao estado inicial"""
        self.result = None
        
        if self.results_container:
            self.results_container.content = ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.INFO_OUTLINE, color="#42A5F5", size=18),
                            ft.Text("Os resultados serão exibidos aqui após a consolidação", 
                                   italic=True, color="#9E9E9E"),
                        ],
                        spacing=10,
                    ),
                ],
                spacing=10,
            )
        
        if self.container:
            self.container.update()
    
    def update(self):
        """Atualiza o componente"""
        if self.container:
            self.container.update()