import flet as ft
from typing import Callable, List
from models.consolidation_model import ConsolidationConfig
from ui.design_system import ds

class Step3Configuration:
    """
    Passo 3: Configuração da consolidação
    
    Interface profissional para configurar as opções de consolidação
    dos arquivos Excel selecionados.
    
    Características:
    - Design limpo e intuitivo
    - Configurações claras e organizadas
    - Validação em tempo real
    - Feedback visual profissional
    """
    
    def __init__(self, page: ft.Page, on_next_click: Callable[[dict], None]):
        self.page = page
        # Garantindo que o callback seja explicitamente armazenado
        self.on_next_click = on_next_click
        print(f"[Step3] Inicializado com callback: {on_next_click.__name__ if on_next_click else 'None'}")
        self.configuration = {}
        self.master_file_path = ""
        self.master_sheet_name = ""
        
        # Controles da UI
        self.merge_strategy_radio = ft.RadioGroup(
            content=ft.Column([
                ft.Radio(
                    value="append",
                    label="Adicionar (Append) - Adiciona novas linhas ao final"
                ),
                ft.Radio(
                    value="replace",
                    label="Substituir (Replace) - Substitui dados existentes"
                ),
                ft.Radio(
                    value="update",
                    label="Atualizar (Update) - Atualiza dados com base em chave"
                ),
            ], 
            spacing=ds.spacing.SM),
            value="append",
            on_change=self._on_strategy_change
        )
        
        self.columns_description = ft.Text(
            "Deixe em branco para consolidar todas as colunas, ou especifique as colunas separadas por vírgula (ex: A,B,C ou Nome,Idade,Email)",
            size=12,
            color="#757575",
        )
        
        self.target_columns_text = ft.TextField(
            label="Colunas alvo",
            hint_text="Exemplo: A,B,C ou Nome,Idade,Email",
            multiline=False,
            width=400,
            on_change=self._validate_form,
            **ds.get_input_style()
        )
        
        self.backup_checkbox = ft.Checkbox(
            label="Criar backup antes da consolidação",
            value=True,
            on_change=self._validate_form
        )
        
        self.next_button = None
        self.master_info_display = None
        self.container = None
        
    def set_master_info(self, file_path: str, sheet_name: str):
        """Define as informações do arquivo mestre"""
        self.master_file_path = file_path
        self.master_sheet_name = sheet_name
        self._update_master_info_display()
        
    def build(self):
        """Constrói a interface do Step 3 com design profissional"""
        # Cabeçalho da seção
        title = ds.create_heading(
            "Configuração",
            level=2,
            color=ds.colors.NEUTRAL_800
        )
        
        description = ds.create_body_text(
            "Configure as opções de consolidação dos dados. "
            "Defina como os arquivos subordinados serão integrados ao arquivo mestre.",
            size="base",
            color=ds.colors.NEUTRAL_600
        )
        
        # Informações do arquivo mestre com design profissional
        card_style = ds.get_card_style(elevated=False)
        card_style["bgcolor"] = ds.colors.INFO_LIGHT
        print("[DEBUG] card_style passado ao Container:", card_style)
        
        # Remover border e bgcolor duplicados do card_style se existirem
        card_style_copy = card_style.copy()
        card_style_copy.pop("border", None)
        card_style_copy.pop("bgcolor", None)
        
        self.master_info_display = ft.Container(
            content=ft.Column([
                # Cabeçalho
                ft.Row([
                    ft.Icon(
                        ft.Icons.INFO_OUTLINE,
                        color=ds.colors.INFO,
                        size=24
                    ),
                    ds.create_heading(
                        "Arquivo Mestre",
                        level=4,
                        color=ds.colors.INFO
                    )
                ], 
                spacing=ds.spacing.SM),
                
                ds.create_divider(),
                
                # Informações do arquivo
                ft.Column([
                    ft.Row([
                        ft.Icon(
                            ft.Icons.DESCRIPTION,
                            color=ds.colors.NEUTRAL_500,
                            size=20
                        ),
                        ds.create_body_text(
                            "Arquivo: N/A",
                            size="sm",
                            color=ds.colors.NEUTRAL_600
                        )
                    ], 
                    spacing=ds.spacing.SM),
                    
                    ft.Row([
                        ft.Icon(
                            ft.Icons.TABLE_CHART,
                            color=ds.colors.NEUTRAL_500,
                            size=20
                        ),
                        ds.create_body_text(
                            "Planilha: N/A",
                            size="sm",
                            color=ds.colors.NEUTRAL_600
                        )
                    ], 
                    spacing=ds.spacing.SM)
                ], 
                spacing=ds.spacing.SM)
            ], 
            spacing=ds.spacing.BASE),
            bgcolor=ds.colors.INFO_LIGHT,
            **card_style_copy,
            width=700
        )
        
        # Card de estratégia de consolidação
        strategy_card = ft.Container(
            content=ft.Column([
                # Cabeçalho
                ft.Row([
                    ft.Icon(
                        ft.Icons.MERGE_TYPE,
                        color=ds.colors.PRIMARY_600,
                        size=24
                    ),
                    ds.create_heading(
                        "Estratégia de Consolidação",
                        level=4,
                        color=ds.colors.PRIMARY_600
                    )
                ], 
                spacing=ds.spacing.SM),
                
                ds.create_divider(),
                
                # Descrição
                ds.create_body_text(
                    "Escolha como os dados dos arquivos subordinados serão integrados:",
                    size="sm",
                    color=ds.colors.NEUTRAL_600
                ),
                
                # Opções de estratégia
                ft.Container(
                    content=self.merge_strategy_radio,
                    margin=ft.margin.only(top=ds.spacing.SM)
                )
            ], 
            spacing=ds.spacing.BASE),
            
            **ds.get_card_style(elevated=False),
            width=700,
            margin=ft.margin.only(bottom=ds.spacing.LG)
        )
        
        # Card de colunas específicas
        columns_card = ft.Container(
            content=ft.Column([
                # Cabeçalho
                ft.Row([
                    ft.Icon(
                        ft.Icons.VIEW_COLUMN,
                        color=ds.colors.SUCCESS,
                        size=24
                    ),
                    ds.create_heading(
                        "Colunas Específicas",
                        level=4,
                        color=ds.colors.SUCCESS
                    )
                ], 
                spacing=ds.spacing.SM),
                
                ds.create_divider(),
                
                # Descrição
                ds.create_body_text(
                    "Deixe em branco para consolidar todas as colunas, ou especifique "
                    "as colunas desejadas separadas por vírgula (ex: A,B,C ou Nome,Idade,Email).",
                    size="sm",
                    color=ds.colors.NEUTRAL_600
                ),
                
                # Campo de entrada
                ft.Container(
                    content=self.target_columns_text,
                    margin=ft.margin.only(top=ds.spacing.SM)
                )
            ], 
            spacing=ds.spacing.BASE),
            
            **ds.get_card_style(elevated=False),
            width=700,
            margin=ft.margin.only(bottom=ds.spacing.LG)
        )
        
        # Card de opções de backup
        backup_card = ft.Container(
            content=ft.Column([
                # Cabeçalho
                ft.Row([
                    ft.Icon(
                        ft.Icons.BACKUP,
                        color=ds.colors.WARNING,
                        size=24
                    ),
                    ds.create_heading(
                        "Opções de Backup",
                        level=4,
                        color=ds.colors.WARNING
                    )
                ], 
                spacing=ds.spacing.SM),
                
                ds.create_divider(),
                
                # Checkbox de backup
                self.backup_checkbox,
                
                # Informação adicional
                ds.create_body_text(
                    "O backup preserva o arquivo mestre original antes da consolidação. "
                    "Recomendado para segurança dos dados.",
                    size="sm",
                    color=ds.colors.NEUTRAL_600
                )
            ], 
            spacing=ds.spacing.BASE),
            
            **ds.get_card_style(elevated=False),
            width=700,
            margin=ft.margin.only(bottom=ds.spacing.XL)
        )
        
        # Botões de navegação com design profissional
        back_button = ft.OutlinedButton(
            content=ft.Row([
                ft.Icon(ft.Icons.ARROW_BACK, size=20),
                ds.create_body_text(
                    "Voltar",
                    size="sm",
                    weight=ds.typography.WEIGHT_MEDIUM,
                    color=ds.colors.PRIMARY_600
                )
            ], 
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=ds.spacing.SM),
            on_click=self._handle_back,
            width=140,
            style=ds.get_button_style("secondary", "large")
        )
        
        self.next_button = ft.ElevatedButton(
            content=ft.Row([
                ds.create_body_text(
                    "Consolidar",
                    size="sm",
                    weight=ds.typography.WEIGHT_MEDIUM,
                    color="#FFFFFF"
                ),
                ft.Icon(ft.Icons.PLAY_ARROW, size=20, color="#FFFFFF")
            ], 
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=ds.spacing.SM),
            on_click=self._handle_next,
            width=140,
            style=ds.get_button_style("primary", "large"),
            disabled=False
        )
        # Botões de navegação
        navigation_row = ft.Row(
            controls=[back_button, self.next_button],
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
                        margin=ft.margin.only(bottom=ds.spacing.XL)
                    ),
                    
                    # Conteúdo principal
                    ft.Column(
                        controls=[
                            self.master_info_display,
                            strategy_card,
                            columns_card,
                            backup_card
                        ],
                        spacing=ds.spacing.LG,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER
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
            padding=ft.padding.all(ds.spacing.XL),
            bgcolor=ds.colors.NEUTRAL_50
        )
        return self.container
    
    def _update_master_info_display(self):
        """
        Atualiza a exibição das informações do arquivo mestre
        com design profissional e informações atualizadas.
        """
        if not self.master_file_path or not self.master_info_display:
            return
            
        import os
        file_name = os.path.basename(self.master_file_path)
        
        # Atualiza o conteúdo com design profissional
        if self.master_info_display is not None:
            self.master_info_display.content = ft.Column([
                # Cabeçalho
                ft.Row([
                    ft.Icon(
                        ft.Icons.INFO_OUTLINE,
                        color=ds.colors.INFO,
                        size=24
                    ),
                    ds.create_heading(
                        "Arquivo Mestre",
                        level=4,
                        color=ds.colors.INFO
                    )
                ], 
                spacing=ds.spacing.SM),
                
                ds.create_divider(),
                
                # Informações do arquivo
                ft.Column([
                    ft.Row([
                        ft.Icon(
                            ft.Icons.DESCRIPTION,
                            color=ds.colors.NEUTRAL_500,
                            size=20
                        ),
                        ds.create_body_text(
                            f"Arquivo: {file_name}",
                            size="sm",
                            color=ds.colors.NEUTRAL_700,
                            weight=ds.typography.WEIGHT_MEDIUM
                        )
                    ], 
                    spacing=ds.spacing.SM),
                    
                    ft.Row([
                        ft.Icon(
                            ft.Icons.TABLE_CHART,
                            color=ds.colors.NEUTRAL_500,
                            size=20
                        ),
                        ds.create_body_text(
                            f"Planilha: {self.master_sheet_name}",
                            size="sm",
                            color=ds.colors.NEUTRAL_700,
                            weight=ds.typography.WEIGHT_MEDIUM
                        )
                    ], 
                    spacing=ds.spacing.SM)
                ], 
                spacing=ds.spacing.SM)
            ], 
            spacing=ds.spacing.BASE)
            
            try:
                self.master_info_display.update()
            except Exception as e:
                print(f"Erro ao atualizar display do arquivo mestre: {e}")
    
    def _on_strategy_change(self, e):
        """Lida com mudança na estratégia de consolidação"""
        self._validate_form()
    
    def _validate_form(self, e=None):
        """Valida o formulário e habilita/desabilita o botão próximo"""
        # Por enquanto, sempre válido já que todos os campos são opcionais
        if self.next_button:
            self.next_button.disabled = False
            self.next_button.update()
    
    def _handle_next(self, e):
        """Lida com o clique no botão próximo"""
        # Processa as colunas alvo
        target_columns = []
        if self.target_columns_text.value and self.target_columns_text.value.strip():
            target_columns = [col.strip() for col in self.target_columns_text.value.split(',')]
        
        # Cria a configuração
        config = ConsolidationConfig(
            master_file_path=self.master_file_path,
            master_sheet_name=self.master_sheet_name,
            target_columns=target_columns,
            merge_strategy=self.merge_strategy_radio.value,
            backup_enabled=self.backup_checkbox.value,
        )
        
        # Adicionar logs para debug
        print(f"[Step3] Botão Consolidar clicado, config: {config}")
        print(f"[Step3] on_next_click existe? {hasattr(self, 'on_next_click')}")
        print(f"[Step3] on_next_click é callable? {callable(self.on_next_click) if hasattr(self, 'on_next_click') else False}")
        
        # Notifica o controle pai
        if hasattr(self, 'on_next_click') and self.on_next_click:
            print(f"[Step3] Chamando on_next_click: {self.on_next_click.__name__ if hasattr(self.on_next_click, '__name__') else 'sem nome'}")
            self.on_next_click(config)
        else:
            print("[Step3] ERRO: on_next_click não está definido ou é None")
    
    def _handle_back(self, e):
        """Lida com o clique no botão voltar"""
        # Implementar navegação para trás se necessário
        pass
    
    def reset(self):
        """Reseta o componente ao estado inicial"""
        self.master_file_path = ""
        self.master_sheet_name = ""
        
        if self.merge_strategy_radio:
            self.merge_strategy_radio.value = "append"
        
        if self.backup_checkbox:
            self.backup_checkbox.value = True
        
        if self.target_columns_text:
            self.target_columns_text.value = ""
        
        if self.next_button:
            self.next_button.disabled = False
            
        if self.master_info_display:
            self.master_info_display.content = ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.INFO_OUTLINE, color="#2196F3", size=20),
                            ft.Text("Informações do arquivo mestre", weight=ft.FontWeight.BOLD, color="#2196F3")
                        ],
                        spacing=10,
                    ),
                    ft.Divider(height=10, color="#B2E6CE"),
                    ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.INSERT_DRIVE_FILE, color="#03A9F4", size=18),
                                    ft.Text("Arquivo: N/A", italic=True, color="#757575"),
                                ],
                                spacing=10,
                            ),
                            ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.TABLE_CHART, color="#689F38", size=18),
                                    ft.Text("Planilha: N/A", italic=True, color="#757575"),
                                ],
                                spacing=10,
                            ),
                        ],
                        spacing=5,
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