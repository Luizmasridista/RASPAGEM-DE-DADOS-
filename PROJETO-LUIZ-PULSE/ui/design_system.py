"""
Sistema de Design Profissional
==============================

Este módulo define um sistema de design sóbrio e profissional para a aplicação,
baseado em princípios de design corporativo e acessibilidade.

Características:
- Paleta de cores neutra e profissional
- Tipografia clara e legível
- Espaçamentos consistentes
- Componentes reutilizáveis
- Transições suaves
"""

import flet as ft
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ColorPalette:
    """Paleta de cores profissional e acessível"""
    
    # Cores primárias - tons de azul corporativo
    PRIMARY_50 = "#F0F4F8"
    PRIMARY_100 = "#D9E2EC"
    PRIMARY_200 = "#BCCCDC"
    PRIMARY_300 = "#9FB3C8"
    PRIMARY_400 = "#829AB1"
    PRIMARY_500 = "#627D98"  # Cor principal
    PRIMARY_600 = "#486581"
    PRIMARY_700 = "#334E68"
    PRIMARY_800 = "#243B53"
    PRIMARY_900 = "#102A43"
    
    # Cores neutras - escala de cinzas
    NEUTRAL_50 = "#F7FAFC"
    NEUTRAL_100 = "#EDF2F7"
    NEUTRAL_200 = "#E2E8F0"
    NEUTRAL_300 = "#CBD5E0"
    NEUTRAL_400 = "#A0AEC0"
    NEUTRAL_500 = "#718096"
    NEUTRAL_600 = "#4A5568"
    NEUTRAL_700 = "#2D3748"
    NEUTRAL_800 = "#1A202C"
    NEUTRAL_900 = "#171923"
    
    # Cores de estado
    SUCCESS = "#38A169"
    SUCCESS_LIGHT = "#C6F6D5"
    WARNING = "#D69E2E"
    WARNING_LIGHT = "#FAF089"
    ERROR = "#E53E3E"
    ERROR_LIGHT = "#FED7D7"
    INFO = "#3182CE"
    INFO_LIGHT = "#BEE3F8"
    
    # Cores de superfície
    BACKGROUND = "#FFFFFF"
    SURFACE = "#F7FAFC"
    SURFACE_ELEVATED = "#FFFFFF"
    BORDER = "#E2E8F0"
    DIVIDER = "#CBD5E0"


@dataclass
class Typography:
    """Sistema tipográfico profissional"""
    
    # Tamanhos de fonte
    SIZE_XS = 12
    SIZE_SM = 14
    SIZE_BASE = 16
    SIZE_LG = 18
    SIZE_XL = 20
    SIZE_2XL = 24
    SIZE_3XL = 30
    SIZE_4XL = 36
    
    # Pesos de fonte
    WEIGHT_LIGHT = ft.FontWeight.W_300
    WEIGHT_NORMAL = ft.FontWeight.W_400
    WEIGHT_MEDIUM = ft.FontWeight.W_500
    WEIGHT_SEMIBOLD = ft.FontWeight.W_600
    WEIGHT_BOLD = ft.FontWeight.W_700
    
    # Altura de linha
    LINE_HEIGHT_TIGHT = 1.25
    LINE_HEIGHT_NORMAL = 1.5
    LINE_HEIGHT_RELAXED = 1.75


@dataclass
class Spacing:
    """Sistema de espaçamento consistente"""
    
    XS = 4
    SM = 8
    BASE = 16
    LG = 24
    XL = 32
    XXL = 48
    XXXL = 64


@dataclass
class BorderRadius:
    """Sistema de bordas arredondadas"""
    
    NONE = 0
    SM = 4
    BASE = 8
    LG = 12
    XL = 16
    FULL = 999


@dataclass
class Shadows:
    """Sistema de sombras profissionais"""
    
    NONE = "none"
    SM = "0 1px 2px 0 rgba(0, 0, 0, 0.05)"
    BASE = "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)"
    MD = "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)"
    LG = "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)"
    XL = "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)"


class DesignSystem:
    """Sistema de design centralizado"""
    
    colors = ColorPalette()
    typography = Typography()
    spacing = Spacing()
    border_radius = BorderRadius()
    shadows = Shadows()
    
    @staticmethod
    def get_button_style(variant: str = "primary", size: str = "medium") -> ft.ButtonStyle:
        """
        Retorna estilos padronizados para botões
        
        Args:
            variant: 'primary', 'secondary', 'outline', 'ghost'
            size: 'small', 'medium', 'large'
        """
        colors = DesignSystem.colors
        spacing = DesignSystem.spacing
        
        # Configurações de tamanho
        size_config = {
            "small": {"height": 32, "padding": spacing.SM},
            "medium": {"height": 40, "padding": spacing.BASE},
            "large": {"height": 48, "padding": spacing.LG}
        }
        
        # Configurações de variante
        variant_config = {
            "primary": {
                "bgcolor": colors.PRIMARY_600,
                "color": "#FFFFFF",
                "overlay_color": colors.PRIMARY_700
            },
            "secondary": {
                "bgcolor": colors.NEUTRAL_200,
                "color": colors.NEUTRAL_700,
                "overlay_color": colors.NEUTRAL_300
            },
            "outline": {
                "bgcolor": "transparent",
                "color": colors.PRIMARY_600,
                "overlay_color": colors.PRIMARY_50,
                "border": ft.BorderSide(1, colors.PRIMARY_600)
            },
            "ghost": {
                "bgcolor": "transparent",
                "color": colors.NEUTRAL_600,
                "overlay_color": colors.NEUTRAL_100
            }
        }
        
        size_props = size_config.get(size, size_config["medium"])
        variant_props = variant_config.get(variant, variant_config["primary"])
        
        style = ft.ButtonStyle(
            bgcolor=variant_props["bgcolor"],
            color=variant_props["color"],
            overlay_color=variant_props.get("overlay_color"),
            shape=ft.RoundedRectangleBorder(radius=DesignSystem.border_radius.BASE),
            padding=size_props["padding"],
            elevation={"": 0, ft.ControlState.HOVERED: 2},
        )
        
        if "border" in variant_props:
            style.side = variant_props["border"]
            
        return style
    
    @staticmethod
    def get_card_style(elevated: bool = False) -> Dict[str, Any]:
        """
        Retorna estilos padronizados para cards
        
        Args:
            elevated: Se o card deve ter sombra elevada
        """
        colors = DesignSystem.colors
        
        return {
            "bgcolor": colors.SURFACE_ELEVATED,
            "border": ft.border.all(1, colors.BORDER),
            "border_radius": DesignSystem.border_radius.LG,
            "padding": DesignSystem.spacing.LG,
            "shadow": ft.BoxShadow(
                spread_radius=0,
                blur_radius=4 if elevated else 1,
                color="rgba(0, 0, 0, 0.1)" if elevated else "rgba(0, 0, 0, 0.05)",
                offset=ft.Offset(0, 2 if elevated else 1)
            )
        }
    
    @staticmethod
    def get_input_style() -> Dict[str, Any]:
        """Retorna estilos padronizados para campos de entrada"""
        colors = DesignSystem.colors
        
        return {
            "border_color": colors.BORDER,
            "focused_border_color": colors.PRIMARY_500,
            "bgcolor": colors.BACKGROUND,
            "border_radius": DesignSystem.border_radius.BASE,
            "content_padding": DesignSystem.spacing.BASE,
        }
    
    @staticmethod
    def create_heading(
        text: str,
        level: int = 1,
        color: Optional[str] = None,
        weight: Optional[ft.FontWeight] = None
    ) -> ft.Text:
        """
        Cria um cabeçalho padronizado
        
        Args:
            text: Texto do cabeçalho
            level: Nível do cabeçalho (1-6)
            color: Cor personalizada
            weight: Peso da fonte personalizado
        """
        typography = DesignSystem.typography
        colors = DesignSystem.colors
        
        size_map = {
            1: typography.SIZE_4XL,
            2: typography.SIZE_3XL,
            3: typography.SIZE_2XL,
            4: typography.SIZE_XL,
            5: typography.SIZE_LG,
            6: typography.SIZE_BASE
        }
        
        weight_map = {
            1: typography.WEIGHT_BOLD,
            2: typography.WEIGHT_BOLD,
            3: typography.WEIGHT_SEMIBOLD,
            4: typography.WEIGHT_SEMIBOLD,
            5: typography.WEIGHT_MEDIUM,
            6: typography.WEIGHT_MEDIUM
        }
        
        return ft.Text(
            text,
            size=size_map.get(level, typography.SIZE_BASE),
            weight=weight or weight_map.get(level, typography.WEIGHT_MEDIUM),
            color=color or colors.NEUTRAL_800
        )
    
    @staticmethod
    def create_body_text(
        text: str,
        size: str = "base",
        color: Optional[str] = None,
        weight: Optional[ft.FontWeight] = None
    ) -> ft.Text:
        """
        Cria texto de corpo padronizado
        
        Args:
            text: Texto
            size: 'xs', 'sm', 'base', 'lg', 'xl'
            color: Cor personalizada
            weight: Peso da fonte personalizado
        """
        typography = DesignSystem.typography
        colors = DesignSystem.colors
        
        size_map = {
            "xs": typography.SIZE_XS,
            "sm": typography.SIZE_SM,
            "base": typography.SIZE_BASE,
            "lg": typography.SIZE_LG,
            "xl": typography.SIZE_XL
        }
        
        return ft.Text(
            text,
            size=size_map.get(size, typography.SIZE_BASE),
            weight=weight or typography.WEIGHT_NORMAL,
            color=color or colors.NEUTRAL_700
        )
    
    @staticmethod
    def create_divider(margin: int = None) -> ft.Divider:
        """Cria um divisor padronizado"""
        colors = DesignSystem.colors
        spacing = DesignSystem.spacing
        
        return ft.Divider(
            height=1,
            color=colors.DIVIDER,
            thickness=1
        )
    
    @staticmethod
    def create_loading_indicator(size: int = 24) -> ft.ProgressRing:
        """Cria um indicador de carregamento padronizado"""
        colors = DesignSystem.colors
        
        return ft.ProgressRing(
            width=size,
            height=size,
            stroke_width=2,
            color=colors.PRIMARY_600
        )
    
    @staticmethod
    def create_icon_button(
        icon: ft.Icons,
        tooltip: str = "",
        on_click=None,
        color: Optional[str] = None,
        size: int = 24
    ) -> ft.IconButton:
        """Cria um botão de ícone padronizado"""
        colors = DesignSystem.colors
        
        return ft.IconButton(
            icon=icon,
            tooltip=tooltip,
            on_click=on_click,
            icon_color=color or colors.NEUTRAL_600,
            icon_size=size,
            style=ft.ButtonStyle(
                shape=ft.CircleBorder(),
                overlay_color=colors.NEUTRAL_100,
                padding=DesignSystem.spacing.SM
            )
        )


# Instância global do sistema de design
ds = DesignSystem()
