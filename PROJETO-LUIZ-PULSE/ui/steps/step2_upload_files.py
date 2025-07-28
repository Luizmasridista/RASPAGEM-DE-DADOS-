import os
import sys
# Adiciona o diretório raiz do projeto ao sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import time
from typing import Callable, List, Optional
from datetime import datetime
from zoneinfo import ZoneInfo
import flet as ft
from services.file_service import FileService
from models.consolidation_model import FileInfo
from ui.design_system import ds

class Step2UploadFiles:
    """
    Passo 2: Upload de arquivos subordinados
    
    Interface profissional para upload e gerenciamento de arquivos Excel
    que serão consolidados com o arquivo mestre.
    
    Características:
    - Design limpo e intuitivo
    - Upload múltiplo de arquivos
    - Validação em tempo real
    - Feedback visual claro
    - Gerenciamento de lista de arquivos
    """
    
    def __init__(
        self,
        page: ft.Page,
        on_next_click: Callable[[List[FileInfo]], None],
        on_back_click: Callable[[], None],
        on_files_change: Callable[[List[FileInfo]], None],
        file_service: FileService,
    ):
        self.page = page
        self.on_next_click = on_next_click
        self.on_back_click = on_back_click
        self.on_files_change = on_files_change
        self.file_service = file_service
        self.uploaded_files: List[FileInfo] = []
        self.file_picker = ft.FilePicker(on_result=self._process_files)
        self.file_list = ft.ListView(expand=True, spacing=8, padding=15)
        self.upload_area = self._create_upload_area()
        self.files_header = None
        self.next_button = None
        self.back_button = None
        self.container = None
        self.page.overlay.append(self.file_picker)
        print("[Step2] Initialized with empty file list, FilePicker added to overlay")

    def build(self):
        """Constrói a interface do Step 2 com design profissional"""
        # Cabeçalho da seção
        title = ds.create_heading(
            "Arquivos Subordinados",
            level=2,
            color=ds.colors.NEUTRAL_800
        )
        
        subtitle = ds.create_body_text(
            "Selecione os arquivos Excel que serão consolidados com o arquivo mestre. "
            "Você pode adicionar múltiplos arquivos de uma vez.",
            size="base",
            color=ds.colors.NEUTRAL_600
        )
        
        # Header de arquivos com design profissional
        self.files_header = ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Icon(
                        ft.Icons.FOLDER_OPEN,
                        color=ds.colors.PRIMARY_600,
                        size=24
                    ),
                    ds.create_heading(
                        "Arquivos Carregados",
                        level=4,
                        color=ds.colors.PRIMARY_600
                    )
                ], 
                spacing=ds.spacing.SM),
                
                ft.Container(expand=True),
                
                # Contador de arquivos
                ft.Container(
                    content=ds.create_body_text(
                        f"{len(self.uploaded_files)}",
                        size="sm",
                        weight=ds.typography.WEIGHT_SEMIBOLD,
                        color="#FFFFFF"
                    ),
                    bgcolor=ds.colors.PRIMARY_600,
                    border_radius=ds.border_radius.FULL,
                    padding=ft.padding.symmetric(
                        horizontal=ds.spacing.BASE,
                        vertical=ds.spacing.XS
                    )
                )
            ], 
            vertical_alignment=ft.CrossAxisAlignment.CENTER),
            
            **ds.get_card_style(elevated=False),
            visible=False,
            width=None  # Remover largura fixa
        )
        
        # Botões de navegação com design profissional
        self.back_button = ft.OutlinedButton(
            content=ft.Row([
                ft.Icon(ft.Icons.ARROW_BACK, size=18),
                ds.create_body_text(
                    "Voltar",
                    size="sm",
                    color=ds.colors.PRIMARY_600
                )
            ], 
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=ds.spacing.SM),
            on_click=self._handle_back,
            width=160,
            style=ds.get_button_style("outline", "medium"),
            tooltip="Voltar para a etapa anterior"
        )
        self.next_button = ft.ElevatedButton(
            content=ft.Row([
                ds.create_body_text(
                    "Avançar",
                    size="sm",
                    color="#FFFFFF"
                ),
                ft.Icon(ft.Icons.ARROW_FORWARD, size=18)
            ], 
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=ds.spacing.SM),
            style=ds.get_button_style("primary"),
            disabled=True,
            on_click=self._handle_next
        )
        
        # Linha de navegação com layout responsivo
        navigation_row = ft.Row(
            [self.back_button, self.next_button], 
            spacing=ds.spacing.LG, 
            alignment=ft.MainAxisAlignment.CENTER,
            wrap=True  # Permitir quebra de linha se necessário
        )
        
        # Container principal com layout profissional
        self.container = ft.Container(
            content=ft.Column(
                controls=[
                    # Cabeçalho
                    ft.Container(
                        content=ft.Column([
                            title,
                            ft.Container(height=ds.spacing.SM),
                            subtitle
                        ]),
                        margin=ft.margin.only(bottom=ds.spacing.XL),
                        width=None  # Remover largura fixa
                    ),
                    
                    # Área de upload
                    ft.Container(
                        content=self.upload_area,
                        alignment=ft.alignment.center,
                        margin=ft.margin.only(bottom=ds.spacing.LG),
                        expand=True  # Added to make container responsive
                    ),
                    
                    # Header dos arquivos
                    ft.Container(
                        content=self.files_header,
                        alignment=ft.alignment.center,
                        margin=ft.margin.only(bottom=ds.spacing.BASE)
                    ),
                    
                    # Lista de arquivos
                    ft.Container(
                        content=self.file_list,
                        bgcolor=ds.colors.SURFACE,
                        border_radius=ds.border_radius.BASE,
                        border=ft.border.all(1, ds.colors.BORDER),
                        padding=ds.spacing.BASE,
                        expand=True,
                        width=None,  # Remover largura fixa
                        height=200 if len(self.uploaded_files) > 0 else None
                    ),
                    
                    # Navegação
                    ft.Container(
                        content=navigation_row,
                        margin=ft.margin.only(top=ds.spacing.XL)
                    )
                ],
                spacing=0,
                expand=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO
            ),
            padding=ds.spacing.XL,
            bgcolor=ds.colors.BACKGROUND,
            alignment=ft.alignment.center,
            expand=True
        )
        
        return self.container

    def _create_upload_area(self):
        """Cria a área de upload com design profissional"""
        # Cria o botão de seleção de arquivos
        select_button = ft.ElevatedButton(
            content=ft.Row([
                ft.Icon(ft.Icons.FOLDER_OPEN, size=20),
                ds.create_body_text(
                    "Selecionar Arquivos",
                    size="sm",
                    weight=ds.typography.WEIGHT_MEDIUM,
                    color="#FFFFFF"
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,  # Centraliza horizontalmente
            vertical_alignment=ft.CrossAxisAlignment.CENTER,  # Centraliza verticalmente
            spacing=ds.spacing.SM),
            on_click=self._pick_files,
            style=ft.ButtonStyle(
                color="#FFFFFF",
                bgcolor=ds.colors.PRIMARY_600,
                padding=ft.padding.symmetric(horizontal=ds.spacing.XL, vertical=ds.spacing.LG),
                overlay_color='transparent',
                elevation=2,
                shape=ft.RoundedRectangleBorder(radius=8)
            ),
            height=45,
            width=340
        )
        
        return ft.Container(
            content=ft.Column([
                # Ícone principal
                ft.Icon(
                    ft.Icons.CLOUD_UPLOAD_OUTLINED,
                    size=64,
                    color=ds.colors.PRIMARY_500
                ),
                # Texto principal
                ds.create_heading(
                    "Adicionar Arquivos Excel",
                    level=4,
                    color=ds.colors.NEUTRAL_700
                ),
                # Texto descritivo
                ds.create_body_text(
                    "Arraste e solte os arquivos aqui ou clique no botão abaixo",
                    size="sm",
                    color=ds.colors.NEUTRAL_500
                ),
                # Separador visual
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            height=1,
                            bgcolor=ds.colors.BORDER,
                            expand=True
                        ),
                        ft.Container(
                            content=ds.create_body_text(
                                "ou",
                                size="xs",
                                color=ds.colors.NEUTRAL_400
                            ),
                            padding=ft.padding.symmetric(horizontal=ds.spacing.BASE)
                        ),
                        ft.Container(
                            height=1,
                            bgcolor=ds.colors.BORDER,
                            expand=True
                        )
                    ]),
                    width=300,
                    margin=ft.margin.symmetric(vertical=ds.spacing.BASE)
                ),
                # Botão de seleção
                ft.Container(
                    content=select_button,
                    alignment=ft.alignment.center,
                    width=340  # Limita o tamanho do botão (fixo, seguro para Flet)
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER, 
            spacing=ds.spacing.LG,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor="#F5F5F7",
            border=ft.border.all(1, "#E0E0E0"),
            border_radius=10,
            padding=20,
            alignment=ft.alignment.center,
            expand=True
        )

    def _pick_files(self, e):
        self.file_picker.pick_files(allow_multiple=True)

    def _process_files(self, e: ft.FilePickerResultEvent):
        """Processa o resultado do FilePicker e extrai os caminhos dos arquivos"""
        if e.files:
            file_paths = [f.path for f in e.files if f.path.endswith(('.xlsx', '.xls'))]
            print(f"[Step2] Processando {len(file_paths)} arquivos selecionados")
            self._process_file_paths(file_paths)
        else:
            print("[Step2] File selection cancelled")

    def _process_file_paths(self, file_paths: List[str]):
        # Garante que o container está na página antes de qualquer update
        if self.container not in self.page.controls:
            self.page.controls.append(self.container)
            self.page.update()
        new_files = []
        
        # Mostrar animação de carregamento com design profissional
        loading_container = ft.Container(
            content=ft.Column([
                ds.create_loading_indicator(48),
                ft.Container(height=ds.spacing.BASE),
                ds.create_heading(
                    "Processando Arquivos",
                    level=4,
                    color=ds.colors.NEUTRAL_700
                ),
                ds.create_body_text(
                    "Aguarde enquanto os arquivos são validados e carregados...",
                    size="sm",
                    color=ds.colors.NEUTRAL_500
                )
            ], 
            alignment=ft.MainAxisAlignment.CENTER, 
            spacing=ds.spacing.SM),
            
            **ds.get_card_style(elevated=False),
            width=None,  # Remover largura fixa
            height=280,
            alignment=ft.alignment.center
        )
        
        # Atualizar a UI com o loading
        original_content = self.upload_area.content
        original_bgcolor = self.upload_area.bgcolor
        original_border = self.upload_area.border
        
        self.upload_area.content = loading_container.content
        self.upload_area.bgcolor = loading_container.bgcolor
        self.upload_area.border = loading_container.border
        self.upload_area.update()
        self.page.update()
        
        # Garantir que a UI seja atualizada antes de processar os arquivos
        time.sleep(0.1)  # Pequena pausa para garantir que a UI atualize
        
        # Processar cada arquivo
        new_files = []
        for file_path in file_paths:
            if file_path not in [f.path for f in self.uploaded_files]:
                # Validar se é um arquivo Excel válido
                if not self.file_service.validate_excel_file(file_path):
                    print(f"[Step2] Invalid Excel file: {file_path}")
                    continue
                
                # Mover o arquivo para a pasta ARQUIVOS_SUBORDINADOS
                new_path = self.file_service.move_to_subordinate_folder(file_path)
                if new_path:
                    # Usar o FileService para obter informações completas do arquivo
                    file_info = self.file_service.get_file_info(new_path)
                    if file_info:
                        self.uploaded_files.append(file_info)
                        new_files.append(file_info)
                        print(f"[Step2] Added file: {new_path} - {file_info.rows_count} rows, {file_info.columns_count} columns")
                    else:
                        print(f"[Step2] Failed to get file info: {new_path}")
                else:
                    print(f"[Step2] Failed to move file: {file_path}")
        
        # Atualizar a interface para mostrar os arquivos carregados
        self._update_file_list()
        self._update_next_button()
        
        # Criar mensagem de sucesso personalizada
        if new_files:
            success_message = ft.SnackBar(
                content=ft.Row([
                    ft.Icon(ft.Icons.CHECK_CIRCLE, color="#FFFFFF", size=20),
                    ds.create_body_text(
                        f"{len(new_files)} arquivo(s) carregado(s) com sucesso!",
                        size="sm",
                        color="#FFFFFF"
                    )
                ], 
                spacing=ds.spacing.SM),
                bgcolor=ds.colors.SUCCESS,
                duration=3000
            )
            self.page.snack_bar = success_message
            self.page.snack_bar.open = True
            
            # Notificar sobre a mudança mas NÃO redirecionar automaticamente
            if self.on_files_change:
                self.on_files_change(self.uploaded_files)
                print(f"[Step2] Files ready: {len(self.uploaded_files)} files uploaded - user can proceed manually")
                
        elif file_paths:
            warning_message = ft.SnackBar(
                content=ft.Row([
                    ft.Icon(ft.Icons.WARNING_AMBER, color="#FFFFFF", size=20),
                    ds.create_body_text(
                        "Nenhum novo arquivo foi adicionado.",
                        size="sm",
                        color="#FFFFFF"
                    )
                ], 
                spacing=ds.spacing.SM),
                bgcolor=ds.colors.WARNING,
                duration=3000
            )
            self.page.snack_bar = warning_message
            self.page.snack_bar.open = True
        
        # IMPORTANTE: Restaurar a área de upload para o estado inicial
        # Criando uma nova instância para garantir que o loading seja removido
        new_upload_area = self._create_upload_area()
        self.upload_area.content = new_upload_area.content
        self.upload_area.bgcolor = new_upload_area.bgcolor
        self.upload_area.border = new_upload_area.border
        
        # Atualizar apenas a página inteira para evitar erros de controles não adicionados
        self.page.update()
        print(f"[Step2] Updated UI with {len(self.uploaded_files)} files")

    def _update_file_list(self):
        try:
            # Garante que o container está na página antes de atualizar o ListView
            if self.container not in self.page.controls:
                self.page.controls.append(self.container)
                self.page.update()
            if hasattr(self.file_list, '_page') and self.file_list._page is not None:
                self.file_list.controls.clear()
                
                # Adicionar resumo visual se houver arquivos
                if self.uploaded_files:
                    summary_card = ft.Container(
                        content=ft.Row([
                            ft.Icon(
                                ft.Icons.CHECK_CIRCLE,
                                color=ds.colors.SUCCESS,
                                size=24
                            ),
                            ft.Column([
                                ds.create_body_text(
                                    f"{len(self.uploaded_files)} arquivo{'s' if len(self.uploaded_files) > 1 else ''} carregado{'s' if len(self.uploaded_files) > 1 else ''}",
                                    size="base",
                                    weight=ds.typography.WEIGHT_SEMIBOLD,
                                    color=ds.colors.NEUTRAL_800
                                ),
                                ds.create_body_text(
                                    "Pronto para avançar para a próxima etapa",
                                    size="sm",
                                    color=ds.colors.NEUTRAL_600
                                )
                            ], 
                            spacing=2, 
                            alignment=ft.MainAxisAlignment.CENTER,
                            expand=True)
                        ], 
                        spacing=ds.spacing.BASE, 
                        alignment=ft.MainAxisAlignment.START),
                        
                        bgcolor=ds.colors.SUCCESS_LIGHT,
                        border=ft.border.all(1, ds.colors.SUCCESS),
                        border_radius=ds.border_radius.BASE,
                        padding=ds.spacing.LG,
                        margin=ft.margin.only(bottom=ds.spacing.LG)
                    )
                    self.file_list.controls.append(summary_card)
                
                # Cards de arquivo com design profissional
                for i, file_info in enumerate(self.uploaded_files):
                    file_name = os.path.basename(file_info.path)
                    file_size_mb = file_info.size / (1024 * 1024) if hasattr(file_info, 'size') else 0
                    
                    file_card = ft.Container(
                        content=ft.Row([
                            # Ícone do arquivo
                            ft.Container(
                                content=ft.Icon(
                                    ft.Icons.DESCRIPTION,
                                    color=ds.colors.PRIMARY_600,
                                    size=24
                                ),
                                bgcolor=ds.colors.PRIMARY_50,
                                border_radius=ds.border_radius.BASE,
                                padding=ds.spacing.SM,
                                width=48,
                                height=48,
                                alignment=ft.alignment.center
                            ),
                            # Informações do arquivo
                            ft.Column([
                                ds.create_body_text(
                                    file_name,
                                    size="sm",
                                    weight=ds.typography.WEIGHT_MEDIUM,
                                    color=ds.colors.NEUTRAL_800
                                ),
                                ds.create_body_text(
                                    f"{file_size_mb:.2f} MB",
                                    size="xs",
                                    color=ds.colors.NEUTRAL_500
                                )
                            ],
                            spacing=2,
                            expand=True,
                            alignment=ft.MainAxisAlignment.CENTER),
                            # Botão de remoção
                            ds.create_icon_button(
                                icon=ft.Icons.DELETE_OUTLINE,
                                tooltip="Remover arquivo",
                                on_click=lambda e, idx=i: self._remove_file(idx),
                                color=ds.colors.ERROR,
                                size=20
                            )
                        ],
                        spacing=ds.spacing.BASE,
                        alignment=ft.MainAxisAlignment.START),
                        **ds.get_card_style(elevated=False),
                        margin=ft.margin.only(bottom=ds.spacing.SM)
                    )
                    self.file_list.controls.append(file_card)
            
            # Atualizar contador de arquivos de forma segura
            try:
                counter_container = self.files_header.content.controls[-1]
                # Verificar se o container tem o atributo content e se é um Text control
                if hasattr(counter_container, 'content') and hasattr(counter_container.content, 'value'):
                    counter_container.content.value = f"{len(self.uploaded_files)}"
            except Exception as e:
                print(f"[Step2] Error updating file counter in _update_file_list: {e}")
        except AttributeError as ae:
            print(f"[Step2] Attribute error in _update_file_list: {ae}")
        except Exception as ex:
            print(f"[Step2] Error in _update_file_list: {ex}")

    def _update_next_button(self):
        """Atualiza o estado do botão de avançar"""
        is_valid = len(self.uploaded_files) >= 1
        self.next_button.disabled = not is_valid
        
        # Atualizar conteúdo do botão para refletir o status
        if is_valid:
            button_text = f"Confirmar ({len(self.uploaded_files)} arquivo{'s' if len(self.uploaded_files) > 1 else ''})"
            button_icon = ft.Icons.CHECK_CIRCLE
        else:
            button_text = "Avançar"
            button_icon = ft.Icons.ARROW_FORWARD
        
        # Atualizar o conteúdo do botão
        self.next_button.content = ft.Row([
            ds.create_body_text(
                button_text,
                size="sm",
                color="#FFFFFF"
            ),
            ft.Icon(button_icon, size=18)
        ], 
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=ds.spacing.SM,
        tight=True)  # Adicionar tight=True para melhor ajuste
        
        # Garantir que o botão se ajuste ao conteúdo
        
            
        self.page.update()
        print(f"[Step2] Next button {'enabled' if is_valid else 'disabled'} - {len(self.uploaded_files)} files ready")

    def _remove_file(self, index: int):
        if 0 <= index < len(self.uploaded_files):
            removed_file = self.uploaded_files.pop(index)
            print(f"[Step2] Removed file: {removed_file.path}")
            self._update_file_list()
            self._update_next_button()
            if self.on_files_change:
                self.on_files_change(self.uploaded_files)
                print("[Step2] Notified listeners after removal")

    def _handle_next(self, e):
        if self.uploaded_files and self.on_next_click:
            self.on_next_click(self.uploaded_files)
            print("[Step2] Next button clicked, proceeding")

    def _handle_back(self, e):
        if self.on_back_click:
            self.on_back_click()
            print("[Step2] Back button clicked")

    def reset(self):
        self.uploaded_files = []
        self.file_list.controls.clear()
        
        # Atualizar contador de arquivos de forma segura
        try:
            if len(self.files_header.content.controls) >= 3:
                counter_container = self.files_header.content.controls[2]
                # Verificar se o container tem o atributo content e se é um Text control
                if hasattr(counter_container, 'content'):
                    counter_container.content.value = "0"
        except Exception as e:
            print(f"[Step2] Error updating file counter in reset: {e}")
            
        # Restaurar estado inicial
        self.files_header.visible = False
        self.next_button.disabled = True
        
        # Garantir que a área de upload esteja no estado inicial
        new_upload_area = self._create_upload_area()
        self.upload_area.content = new_upload_area.content
        self.upload_area.bgcolor = new_upload_area.bgcolor
        self.upload_area.border = new_upload_area.border
        
        # Atualizar apenas a página inteira para evitar erros
        self.page.update()
        print("[Step2] Reset to initial state")

    def get_uploaded_files(self) -> List[FileInfo]:
        return self.uploaded_files