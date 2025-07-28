import flet as ft
from typing import Callable, Dict, List
from models.consolidation_model import ConsolidationStep
from ui.design_system import ds

class Sidebar:
    """
    Componente de barra lateral com navegação em etapas
    
    Design profissional e sóbrio com:
    - Paleta de cores neutra
    - Tipografia clara e consistente
    - Estados visuais bem definidos
    - Transições suaves
    """
    
    def __init__(
        self,
        steps: List[Dict],
        current_step: int = 1,
        on_step_click: Callable[[int], None] = None,
        on_reset: Callable[[], None] = None,
    ):
        self.steps = steps
        self.current_step = current_step
        self.on_step_click = on_step_click
        self.on_reset = on_reset
        self.step_controls = {}
        self.container = None
    
    def build(self):
        """Constrói o componente sidebar com design profissional"""
        # Cabeçalho com identidade visual sóbria
        header = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(
                                ft.Icons.ANALYTICS_OUTLINED,
                                size=28,
                                color=ds.colors.PRIMARY_400
                            ),
                            ft.Column(
                                controls=[
                                    ds.create_heading(
                                        "Consolidador",
                                        level=5,
                                        color=ds.colors.NEUTRAL_100
                                    ),
                                    ds.create_body_text(
                                        "Sistema Profissional",
                                        size="xs",
                                        color=ds.colors.NEUTRAL_400
                                    )
                                ],
                                spacing=2,
                                tight=True
                            )
                        ],
                        spacing=ds.spacing.BASE,
                        alignment=ft.MainAxisAlignment.START,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    ft.Container(
                        content=ft.Divider(
                            height=1,
                            color=ds.colors.PRIMARY_800,
                            thickness=1
                        ),
                        margin=ft.margin.only(top=ds.spacing.LG)
                    )
                ],
                spacing=0,
                tight=True
            ),
            padding=ft.padding.all(ds.spacing.LG),
        )
        print(f"[Sidebar] Header created: {type(header)}")
        
        # Lista de passos com espaçamento profissional
        steps_list = ft.ListView(
            expand=True,
            spacing=ds.spacing.XS,
            padding=ft.padding.symmetric(
                horizontal=ds.spacing.BASE,
                vertical=ds.spacing.SM
            )
        )
        print(f"[Sidebar] Steps list created: {type(steps_list)}")
        
        for step in self.steps:
            step_control = self._create_step_control(step)
            self.step_controls[step["id"]] = step_control
            steps_list.controls.append(step_control)
        
        # Adiciona print statements para debugar os controles dos passos
        for index, control in enumerate(steps_list.controls):
            print(f"[Sidebar] Step control at index {index} type: {type(control)}")
        
        # Rodapé com botão de reset profissional
        footer = ft.Container(
            content=ft.ElevatedButton(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.REFRESH, size=18),
                        ds.create_body_text(
                            "Nova Consolidação",
                            size="sm",
                            color="#FFFFFF"
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=ds.spacing.SM
                ),
                on_click=lambda e: self._handle_reset(),
                width=240,
                style=ds.get_button_style("primary", "medium"),
            ),
            padding=ft.padding.all(ds.spacing.LG),
            alignment=ft.alignment.center,
        )
        print(f"[Sidebar] Footer created: {type(footer)}")
        
        self.container = ft.Container(
            content=ft.Column(
                controls=[
                    header,
                    steps_list,
                    footer,
                ],
                spacing=0,
                expand=True,
            ),
            width=300,
            bgcolor=ds.colors.PRIMARY_900,
            border_radius=ft.border_radius.only(
                top_right=ds.border_radius.LG,
                bottom_right=ds.border_radius.LG
            ),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=8,
                color="rgba(0, 0, 0, 0.15)",
                offset=ft.Offset(2, 0)
            )
        )
        return self.container
    
    def _create_step_control(self, step: Dict):
        try:
            step_id = step["id"]
            is_current = step_id == self.current_step
            is_completed = step_id < self.current_step
            is_accessible = step_id <= self.current_step + 1
            
            # Definição de cores baseada no estado
            if is_completed:
                icon_color = ds.colors.SUCCESS
                text_color = ds.colors.NEUTRAL_100
                bg_color = "transparent"
            elif is_current:
                icon_color = ds.colors.PRIMARY_500
                text_color = ds.colors.PRIMARY_500
                bg_color = ds.colors.PRIMARY_50
            else:  # Pending
                icon_color = ds.colors.NEUTRAL_500
                text_color = ds.colors.NEUTRAL_500
                bg_color = "transparent"
            
            # Ícone baseado no estado
            if is_completed:
                icon_name = ft.Icons.CHECK_CIRCLE
            elif is_current:
                icon_name = ft.Icons.RADIO_BUTTON_CHECKED
            else:
                icon_name = ft.Icons.RADIO_BUTTON_UNCHECKED
            
            # Container do ícone com design consistente
            icon_container = ft.Container(
                content=ft.Icon(
                    icon_name,
                    size=20,
                    color=icon_color
                ),
                width=28,
                height=28,
                alignment=ft.alignment.center
            )
            
            # Texto do passo com tipografia profissional
            step_text = ds.create_body_text(
                step["name"],
                size="sm",
                weight=ds.typography.WEIGHT_MEDIUM if is_current or is_completed else ds.typography.WEIGHT_NORMAL,
                color=text_color
            )
            
            # Descrição com design sutil
            step_description = ds.create_body_text(
                step.get("description", ""),
                size="xs",
                color=ds.colors.NEUTRAL_500 if is_current or is_completed else ds.colors.NEUTRAL_400
            )
            
            # Conteúdo do passo
            step_content = ft.Container(
                content=ft.Row([
                    icon_container,
                    ft.Column([
                        step_text,
                        step_description
                    ],
                    spacing=ds.spacing.XS,
                    tight=True)
                ],
                spacing=ds.spacing.SM,
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=ft.padding.symmetric(
                horizontal=ds.spacing.BASE,
                vertical=ds.spacing.SM
            ),
            bgcolor=bg_color,
            border_radius=ds.border_radius.BASE,
            on_click=lambda e, s=step_id: self._handle_step_click(s) if is_accessible else None,
            ink=True if is_accessible else False
            )
            print(f"[Sidebar] Created step control for {step['name']} type: {type(step_content)}")
            return step_content
        except Exception as e:
            print(f"[Debug] Erro ao criar step control para {step['name']}: {str(e)}")
            return ft.Container(content=ft.Text("Erro no controle do passo", color="red"))  # Retorna um controle fallback
    
    def _handle_step_click(self, step_id: int):
        """Lida com o clique em um passo"""
        if self.on_step_click and step_id < self.current_step + 2:  # Permite voltar ou ir para o próximo
            self.on_step_click(step_id)
    
    def _handle_reset(self):
        """Lida com o clique no botão de reset"""
        if self.on_reset:
            self.on_reset()
    
    def update_step(self, step_id: int, status: str):
        """
        Atualiza o status de um passo com feedback visual profissional
        
        Args:
            step_id: ID do passo
            status: 'completed', 'error', 'running', 'pending'
        """
        if step_id in self.step_controls:
            step_control = self.step_controls[step_id]
            icon_container = step_control.content.controls[0]
            icon = icon_container.content
            
            # Atualiza ícone e cor baseado no status
            if status == "completed":
                icon.name = ft.Icons.CHECK_CIRCLE
                icon.color = ds.colors.SUCCESS
            elif status == "error":
                icon.name = ft.Icons.ERROR
                icon.color = ds.colors.ERROR
            elif status == "running":
                icon.name = ft.Icons.HOURGLASS_TOP
                icon.color = ds.colors.WARNING
            elif status == "pending":
                icon.name = ft.Icons.RADIO_BUTTON_UNCHECKED
                icon.color = ds.colors.NEUTRAL_500
            
            if self.container:
                self.container.update()
    
    def update(self):
        """Atualiza o componente"""
        if self.container:
            self.container.update()
    
    def set_current_step(self, step_id: int):
        """
        Define o passo atual com transições suaves
        
        Args:
            step_id: ID do passo a ser definido como atual
        """
        if 1 <= step_id <= len(self.step_controls):
            old_step = self.current_step
            self.current_step = step_id
            
            # Reconstrói os controles com os novos estados
            for step in self.steps:
                step_control = self._create_step_control(step)
                self.step_controls[step["id"]] = step_control
            
            # Atualiza a lista de passos
            if hasattr(self, 'container') and self.container:
                steps_list = self.container.content.controls[1]  # ListView dos passos
                steps_list.controls.clear()
                
                for step in self.steps:
                    steps_list.controls.append(self.step_controls[step["id"]])
                
                self.container.update()