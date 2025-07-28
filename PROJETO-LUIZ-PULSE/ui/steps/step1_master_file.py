import os
import flet as ft
from typing import Callable, List
from ui.design_system import ds


class Step1MasterFile:
    """
    Passo 1: Seleção do arquivo mestre
    
    Interface profissional para seleção do arquivo Excel principal
    que servirá como base para a consolidação de dados.
    
    Características:
    - Design limpo e intuitivo
    - Validação em tempo real
    - Feedback visual claro
    - Suporte a múltiplas planilhas
    """
    
    def __init__(
        self,
        page: ft.Page,
        on_next_click: Callable[[str], None],
        on_back_click: Callable[[], None],
        file_service,
    ):
        self.page = page
        self.on_next_click = on_next_click
        self.on_back_click = on_back_click
        self.file_service = file_service
        self.selected_file = None
        self.selected_sheet = None
        self.file_picker = ft.FilePicker(on_result=self._handle_file_selection)
        self.sheet_dropdown = ft.Dropdown(
            label="Selecione a Planilha",
            options=[],
            width=400,
            disabled=True,
            on_change=self._validate_form,
            border_color=ds.colors.BORDER,
            focused_border_color=ds.colors.PRIMARY_500,
            bgcolor=ds.colors.BACKGROUND,
            border_radius=ds.border_radius.BASE,
            content_padding=ds.spacing.BASE,
            text_size=ds.typography.SIZE_SM
        )
        self.next_button = None
        self.back_button = None
        self.container = None
        self.warning_container = None
        self.file_info_container = None
        
        # Adiciona o file picker à página
        page.overlay.append(self.file_picker)
    
    def build(self):
        """Constrói a interface do Step 1 com design profissional"""
        # Cabeçalho da seção
        title = ds.create_heading(
            "Arquivo Mestre",
            level=2,
            color=ds.colors.NEUTRAL_800
        )
        
        description = ds.create_body_text(
            "Selecione o arquivo Excel que servirá como base para a consolidação de dados. "
            "Este arquivo será usado como referência principal para o processo.",
            size="base",
            color=ds.colors.NEUTRAL_600
        )
        # Aviso importante com design profissional
        warning_content = ft.Row(
            controls=[
                ft.Icon(
                    ft.Icons.WARNING_AMBER,
                    color=ds.colors.WARNING,
                    size=24
                ),
                ft.Column(
                    controls=[
                        ds.create_body_text(
                            "Importante",
                            size="sm",
                            weight=ds.typography.WEIGHT_SEMIBOLD,
                            color=ds.colors.WARNING
                        ),
                        ds.create_body_text(
                            "Feche todos os programas de planilhas (Excel, LibreOffice, etc.) antes de continuar.",
                            size="sm",
                            color=ds.colors.NEUTRAL_700
                        )
                    ],
                    spacing=4,
                    tight=True,
                    expand=True
                )
            ],
            spacing=ds.spacing.BASE,
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.START
        )
        
        self.warning_container = ft.Container(
            content=warning_content,
            padding=ds.spacing.LG,
            bgcolor=ds.colors.WARNING_LIGHT,
            border=ft.border.all(1, ds.colors.WARNING),
            border_radius=ds.border_radius.BASE,
            margin=ft.margin.only(bottom=ds.spacing.LG)
        )
        print(f"[Step1] Warning container created: {type(self.warning_container)}")
        # Botão de seleção de arquivo com design profissional
        select_button = ft.ElevatedButton(
            content=ft.Row([
                ft.Icon(ft.Icons.FOLDER_OPEN, size=20),
                ds.create_body_text(
                    "Selecionar Arquivo Excel",
                    size="sm",
                    weight=ds.typography.WEIGHT_MEDIUM,
                    color="#FFFFFF"
                )
            ], 
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=ds.spacing.SM),
            on_click=lambda _: self.file_picker.pick_files(
                allow_multiple=False, 
                allowed_extensions=["xlsx", "xls"]
            ),
            width=280,
            style=ds.get_button_style("primary", "large")
        )
        # Container de informações do arquivo com design profissional
        self.file_info_container = ft.Container(
            content=ft.Column([
                # Cabeçalho da seção de arquivo
                ft.Row([
                    ft.Icon(
                        ft.Icons.DESCRIPTION,
                        color=ds.colors.PRIMARY_600,
                        size=24
                    ),
                    ds.create_heading(
                        "Arquivo Selecionado",
                        level=4,
                        color=ds.colors.PRIMARY_600
                    )
                ], 
                spacing=ds.spacing.SM,
                alignment=ft.MainAxisAlignment.START),
                
                ds.create_divider(),
                
                # Conteúdo dinâmico do arquivo
                ft.Column(
                    controls=[
                        ft.Row([
                            ft.Icon(
                                ft.Icons.INFO_OUTLINE,
                                color=ds.colors.NEUTRAL_400,
                                size=20
                            ),
                            ds.create_body_text(
                                "Nenhum arquivo selecionado",
                                size="sm",
                                color=ds.colors.NEUTRAL_500
                            ),
                        ], 
                        spacing=ds.spacing.SM),
                    ],
                    spacing=ds.spacing.SM
                ),
                
                # Seleção de planilha
                ft.Column([
                    ft.Row([
                        ft.Icon(
                            ft.Icons.TABLE_CHART,
                            color=ds.colors.SUCCESS,
                            size=20
                        ),
                        ds.create_body_text(
                            "Planilha:",
                            size="sm",
                            weight=ds.typography.WEIGHT_MEDIUM,
                            color=ds.colors.NEUTRAL_700
                        )
                    ], 
                    spacing=ds.spacing.SM),
                    
                    self.sheet_dropdown,
                ], 
                spacing=ds.spacing.SM),
                
                # Botão de remoção
                ft.Container(
                    content=ft.ElevatedButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.DELETE_OUTLINE, size=18),
                            ds.create_body_text(
                                "Remover Arquivo",
                                size="sm",
                                color="#FFFFFF"
                            )
                        ], 
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=ds.spacing.SM),
                        on_click=self._handle_delete_file,
                        width=200,
                        style=ft.ButtonStyle(
                            bgcolor=ds.colors.ERROR,
                            color="#FFFFFF",
                            shape=ft.RoundedRectangleBorder(radius=ds.border_radius.BASE),
                            padding=ds.spacing.BASE
                        )
                    ),
                    margin=ft.margin.only(top=ds.spacing.LG)
                )
            ], 
            spacing=ds.spacing.LG),
            **ds.get_card_style(elevated=True),
            width=700,
            visible=False
        )
        print(f"[Step1] File info container created: {type(self.file_info_container)}")
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
            visible=False
        )
        print(f"[Step1] Back button created: {type(self.back_button)}")
        
        self.next_button = ft.ElevatedButton(
            content=ft.Row([
                ds.create_body_text(
                    "Próximo",
                    size="sm",
                    color="#FFFFFF"
                ),
                ft.Icon(ft.Icons.ARROW_FORWARD, size=18)
            ], 
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=ds.spacing.SM),
            on_click=self._handle_next,
            width=160,
            style=ds.get_button_style("primary", "medium"),
            disabled=True
        )
        print(f"[Step1] Next button created: {type(self.next_button)}")
        # Linha de navegação
        navigation_row = ft.Row(
            [self.back_button, self.next_button], 
            spacing=ds.spacing.LG, 
            alignment=ft.MainAxisAlignment.CENTER
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
                            description
                        ]),
                        padding=ds.spacing.LG,
                        margin=ft.margin.only(bottom=ds.spacing.LG)
                    ),
                    
                    # Aviso
                    self.warning_container,
                    
                    # Botão de seleção
                    ft.Container(
                        content=select_button,
                        alignment=ft.alignment.center,
                        margin=ft.margin.only(bottom=ds.spacing.LG)
                    ),
                    
                    # Informações do arquivo
                    self.file_info_container,
                    
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
            bgcolor=ds.colors.BACKGROUND
        )
        print(f"[Step1] Container created: {type(self.container)}")
        self._start_warning_animation()
        return self.container
    
    def _handle_file_selection(self, e: ft.FilePickerResultEvent):
        """Lida com a seleção de arquivo"""
        if e.files and len(e.files) > 0:
            saved_path = self.file_service.save_uploaded_file(e.files[0].path, 'mestre')
            if saved_path and self.file_service.validate_excel_file(saved_path):
                sheet_names = self._get_excel_sheets(saved_path)
                if sheet_names:
                    self.selected_file = saved_path
                    self.sheet_dropdown.options = [ft.dropdown.Option(sheet) for sheet in sheet_names]
                    self.sheet_dropdown.disabled = False
                    # Atualiza o conteúdo do container com informações do arquivo
                    file_info_content = ft.Column([
                        # Cabeçalho da seção de arquivo
                        ft.Row([
                            ft.Icon(
                                ft.Icons.DESCRIPTION,
                                color=ds.colors.PRIMARY_600,
                                size=24
                            ),
                            ds.create_heading(
                                "Arquivo Selecionado",
                                level=4,
                                color=ds.colors.PRIMARY_600
                            )
                        ], 
                        spacing=ds.spacing.SM,
                        alignment=ft.MainAxisAlignment.START),
                        
                        ds.create_divider(),
                        
                        # Informações do arquivo
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Icon(
                                        ft.Icons.CHECK_CIRCLE,
                                        color=ds.colors.SUCCESS,
                                        size=20
                                    ),
                                    ds.create_body_text(
                                        f"Arquivo: {os.path.basename(saved_path)}",
                                        size="sm",
                                        weight=ds.typography.WEIGHT_MEDIUM,
                                        color=ds.colors.NEUTRAL_700
                                    )
                                ], 
                                spacing=ds.spacing.SM),
                                
                                ft.Row([
                                    ft.Icon(
                                        ft.Icons.FOLDER,
                                        color=ds.colors.NEUTRAL_500,
                                        size=18
                                    ),
                                    ds.create_body_text(
                                        f"Local: {os.path.dirname(saved_path)}",
                                        size="xs",
                                        color=ds.colors.NEUTRAL_500
                                    )
                                ], 
                                spacing=ds.spacing.SM)
                            ], 
                            spacing=ds.spacing.XS),
                            padding=ds.spacing.BASE,
                            bgcolor=ds.colors.SUCCESS_LIGHT,
                            border_radius=ds.border_radius.BASE,
                            border=ft.border.all(1, ds.colors.SUCCESS)
                        ),
                        
                        # Seleção de planilha
                        ft.Column([
                            ft.Row([
                                ft.Icon(
                                    ft.Icons.TABLE_CHART,
                                    color=ds.colors.SUCCESS,
                                    size=20
                                ),
                                ds.create_body_text(
                                    "Planilha:",
                                    size="sm",
                                    weight=ds.typography.WEIGHT_MEDIUM,
                                    color=ds.colors.NEUTRAL_700
                                )
                            ], 
                            spacing=ds.spacing.SM),
                            
                            self.sheet_dropdown,
                        ], 
                        spacing=ds.spacing.SM),
                        
                        # Botão de remoção
                        ft.Container(
                            content=ft.ElevatedButton(
                                content=ft.Row([
                                    ft.Icon(ft.Icons.DELETE_OUTLINE, size=18),
                                    ds.create_body_text(
                                        "Remover Arquivo",
                                        size="sm",
                                        color="#FFFFFF"
                                    )
                                ], 
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=ds.spacing.SM),
                                on_click=self._handle_delete_file,
                                width=200,
                                style=ft.ButtonStyle(
                                    bgcolor=ds.colors.ERROR,
                                    color="#FFFFFF",
                                    shape=ft.RoundedRectangleBorder(radius=ds.border_radius.BASE),
                                    padding=ds.spacing.BASE
                                )
                            ),
                            margin=ft.margin.only(top=ds.spacing.LG)
                        )
                    ], 
                    spacing=ds.spacing.LG)
                    
                    self.file_info_container.content = file_info_content
                    self.file_info_container.visible = True
                    self.file_info_container.update()
                    self._validate_form()
                else:
                    self._show_error("Arquivo inválido ou sem planilhas.")
            else:
                self._show_error("Falha ao salvar arquivo mestre.")
        else:
            # Nenhum arquivo selecionado (cancelado)
            pass
    
    def _handle_delete_file(self, e):
        """Lida com a exclusão do arquivo selecionado"""
        self.selected_file = None
        self.selected_sheet = None
        self.sheet_dropdown.options = []
        self.sheet_dropdown.value = None
        self.sheet_dropdown.disabled = True
        
        # Reseta o conteúdo para o estado inicial
        initial_content = ft.Column([
            # Cabeçalho da seção de arquivo
            ft.Row([
                ft.Icon(
                    ft.Icons.DESCRIPTION,
                    color=ds.colors.PRIMARY_600,
                    size=24
                ),
                ds.create_heading(
                    "Arquivo Selecionado",
                    level=4,
                    color=ds.colors.PRIMARY_600
                )
            ], 
            spacing=ds.spacing.SM,
            alignment=ft.MainAxisAlignment.START),
            
            ds.create_divider(),
            
            # Conteúdo dinâmico do arquivo
            ft.Column(
                controls=[
                    ft.Row([
                        ft.Icon(
                            ft.Icons.INFO_OUTLINE,
                            color=ds.colors.NEUTRAL_400,
                            size=20
                        ),
                        ds.create_body_text(
                            "Nenhum arquivo selecionado",
                            size="sm",
                            color=ds.colors.NEUTRAL_500
                        ),
                    ], 
                    spacing=ds.spacing.SM),
                ],
                spacing=ds.spacing.SM
            ),
            
            # Seleção de planilha
            ft.Column([
                ft.Row([
                    ft.Icon(
                        ft.Icons.TABLE_CHART,
                        color=ds.colors.SUCCESS,
                        size=20
                    ),
                    ds.create_body_text(
                        "Planilha:",
                        size="sm",
                        weight=ds.typography.WEIGHT_MEDIUM,
                        color=ds.colors.NEUTRAL_700
                    )
                ], 
                spacing=ds.spacing.SM),
                
                self.sheet_dropdown,
            ], 
            spacing=ds.spacing.SM),
        ], 
        spacing=ds.spacing.LG)
        
        self.file_info_container.content = initial_content
        self.file_info_container.visible = False
        self.file_info_container.update()
        self._validate_form()
    
    def _show_error(self, message: str):
        """Exibe mensagem de erro com design profissional"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Row([
                ft.Icon(
                    ft.Icons.ERROR_OUTLINE,
                    color="#FFFFFF",
                    size=20
                ),
                ds.create_body_text(
                    message,
                    size="sm",
                    color="#FFFFFF"
                )
            ], 
            spacing=ds.spacing.SM),
            bgcolor=ds.colors.ERROR,
            duration=4000
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def _handle_next(self, e):
        """Lida com o clique no botão próximo"""
        if self.selected_file and self.selected_sheet:
            self.on_next_click(self.selected_file)
    
    def _handle_back(self, e):
        """Lida com o clique no botão voltar"""
        if self.on_back_click:
            self.on_back_click()
    
    def _start_warning_animation(self):
        """Inicia a animação do aviso - removido para compatibilidade"""
        # Animação removida para compatibilidade com a versão atual do Flet
        pass
    
    def _validate_form(self, e=None):
        """Valida o formulário"""
        if e is not None:
            self.selected_sheet = e.control.value
        if self.selected_file and self.selected_sheet:
            self.next_button.disabled = False
        else:
            self.next_button.disabled = True
        self.page.update()
    
    def _get_excel_sheets(self, file_path):
        """Obtém as planilhas do arquivo Excel"""
        try:
            import pandas as pd
            return pd.ExcelFile(file_path).sheet_names
        except Exception as e:
            print(f"Erro ao ler planilhas: {e}")
            return []
    
    def reset(self):
        """Reseta o componente ao estado inicial"""
        self.selected_file = None
        self.selected_sheet = None
        self.sheet_dropdown.options = []
        self.sheet_dropdown.value = None
        self.sheet_dropdown.disabled = True
        self.next_button.disabled = True
        self.file_info_container.visible = False
        self.file_info_container.content = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.INFO_OUTLINE, color="#03A9F4", size=18),
                        ft.Text("Nenhum arquivo selecionado", italic=True, color="#9E9E9E"),
                    ],
                    spacing=15,
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