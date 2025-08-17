"""Design system converter for PowerBuilder UI to Flutter themes.

This module converts PowerBuilder visual properties and styles to Flutter
design systems and themes.
"""

import logging
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ColorScheme:
    """Flutter color scheme."""

    primary: str
    secondary: str
    surface: str
    background: str
    error: str
    onPrimary: str
    onSecondary: str
    onSurface: str
    onBackground: str
    onError: str


@dataclass
class ThemeConfig:
    """Theme configuration."""

    name: str
    colorScheme: ColorScheme
    fontFamily: str
    borderRadius: float
    elevation: dict[str, float]


class DesignSystemConverter:
    """Converts PowerBuilder UI styles to Flutter design systems."""

    def __init__(self, theme_name: str = "material") -> None:
        """Initialize the design system converter.

        Args:
            theme_name: Design theme ('material', 'fluent', 'liquid_glass')
        """
        self.theme_name = theme_name

        # PowerBuilder color to hex mappings
        self.pb_colors = {
            # PowerBuilder system colors
            "buttonface": "#F0F0F0",
            "window": "#FFFFFF",
            "windowtext": "#000000",
            "highlight": "#0078D4",
            "highlighttext": "#FFFFFF",
            "inactivecaption": "#CCCCCC",
            "menu": "#F0F0F0",
            "menutext": "#000000",
            "scrollbar": "#C0C0C0",
            "3ddkshadow": "#696969",
            "3dface": "#F0F0F0",
            "3dhighlight": "#FFFFFF",
            "3dlight": "#E0E0E0",
            "3dshadow": "#A0A0A0",
            "activeborder": "#B4B4B4",
            "activecaption": "#99B4D1",
            "appworkspace": "#ABABAB",
            "background": "#000000",
            "desktop": "#000000",
            "graytext": "#6D6D6D",
            "hotlight": "#0066CC",
            "inactiveborder": "#F4F7FC",
            "infobackground": "#FFFFE1",
            "infotext": "#000000",
            "windowframe": "#646464",
            # Common colors
            "black": "#000000",
            "white": "#FFFFFF",
            "red": "#FF0000",
            "green": "#00FF00",
            "blue": "#0000FF",
            "yellow": "#FFFF00",
            "cyan": "#00FFFF",
            "magenta": "#FF00FF",
            "gray": "#808080",
            "darkgray": "#404040",
            "lightgray": "#C0C0C0",
        }

        # Theme configurations
        self.themes = {
            "material": ThemeConfig(
                name="Material Design",
                colorScheme=ColorScheme(
                    primary="#2196F3",
                    secondary="#FF5722",
                    surface="#FFFFFF",
                    background="#FAFAFA",
                    error="#F44336",
                    onPrimary="#FFFFFF",
                    onSecondary="#FFFFFF",
                    onSurface="#000000",
                    onBackground="#000000",
                    onError="#FFFFFF",
                ),
                fontFamily="Roboto",
                borderRadius=4.0,
                elevation={
                    "card": 2.0,
                    "button": 2.0,
                    "appBar": 4.0,
                    "dialog": 24.0,
                },
            ),
            "fluent": ThemeConfig(
                name="Fluent Design",
                colorScheme=ColorScheme(
                    primary="#0078D4",
                    secondary="#107C10",
                    surface="#FFFFFF",
                    background="#F3F3F3",
                    error="#C42B1C",
                    onPrimary="#FFFFFF",
                    onSecondary="#FFFFFF",
                    onSurface="#000000",
                    onBackground="#000000",
                    onError="#FFFFFF",
                ),
                fontFamily="Segoe UI",
                borderRadius=2.0,
                elevation={
                    "card": 0.0,
                    "button": 0.0,
                    "appBar": 0.0,
                    "dialog": 8.0,
                },
            ),
            "liquid_glass": ThemeConfig(
                name="Liquid Glass",
                colorScheme=ColorScheme(
                    primary="#6C63FF",
                    secondary="#FF6B6B",
                    surface="#FFFFFF",
                    background="#F8F9FA",
                    error="#EE5A24",
                    onPrimary="#FFFFFF",
                    onSecondary="#FFFFFF",
                    onSurface="#2D3436",
                    onBackground="#2D3436",
                    onError="#FFFFFF",
                ),
                fontFamily="Inter",
                borderRadius=12.0,
                elevation={
                    "card": 8.0,
                    "button": 4.0,
                    "appBar": 0.0,
                    "dialog": 16.0,
                },
            ),
        }

        self.current_theme = self.themes.get(theme_name, self.themes["material"])

    def convert_color(self, pb_color: str) -> str:
        """Convert PowerBuilder color to Flutter color.

        Args:
            pb_color: PowerBuilder color (name or RGB value)

        Returns:
            Flutter color string (hex format)
        """
        if not pb_color:
            return "#000000"

        pb_color = pb_color.lower().strip()

        # Check if it's a named color
        if pb_color in self.pb_colors:
            return self.pb_colors[pb_color]

        # Check if it's an RGB value (e.g., "rgb(255,0,0)" or "255,0,0")
        if "rgb" in pb_color:
            rgb_match = re.match(r"rgb\((\d+),\s*(\d+),\s*(\d+)\)", pb_color)
            if rgb_match:
                r, g, b = rgb_match.groups()
                return f"#{int(r):02X}{int(g):02X}{int(b):02X}"
        elif "," in pb_color:
            parts = pb_color.split(",")
            if len(parts) == 3:
                try:
                    r, g, b = [int(p.strip()) for p in parts]
                    return f"#{r:02X}{g:02X}{b:02X}"
                except ValueError:
                    # Invalid RGB color format
                    logger.debug("Invalid RGB color format: %s", pb_color)

        # Check if it's already a hex value
        if pb_color.startswith("#"):
            return pb_color.upper()

        # Check if it's a PowerBuilder color number
        try:
            color_num = int(pb_color)
            # PowerBuilder uses BGR format for color numbers
            b = (color_num >> 16) & 0xFF
            g = (color_num >> 8) & 0xFF
            r = color_num & 0xFF
            return f"#{r:02X}{g:02X}{b:02X}"
        except ValueError:
            # Not a numeric color value
            logger.debug("Not a numeric color value: %s", pb_color)

        # Default to black
        logger.warning("Unknown color format: %s", pb_color)
        return "#000000"

    def convert_font(self, pb_font: dict[str, Any]) -> dict[str, Any]:
        """Convert PowerBuilder font to Flutter TextStyle.

        Args:
            pb_font: PowerBuilder font properties

        Returns:
            Flutter TextStyle properties
        """
        flutter_font = {
            "fontFamily": self.current_theme.fontFamily,
            "fontSize": 14.0,
            "fontWeight": "FontWeight.normal",
            "fontStyle": "FontStyle.normal",
        }

        if not pb_font:
            return flutter_font

        # Convert font size (PowerBuilder uses points)
        if "size" in pb_font:
            flutter_font["fontSize"] = float(pb_font["size"])

        # Convert font family
        if "face" in pb_font:
            font_face = pb_font["face"]
            # Map common PowerBuilder fonts to Flutter equivalents
            font_map = {
                "arial": "Arial",
                "times new roman": "Times",
                "courier new": "Courier",
                "tahoma": "Roboto",
                "ms sans serif": "Roboto",
                "system": self.current_theme.fontFamily,
            }
            flutter_font["fontFamily"] = font_map.get(font_face.lower(), font_face)

        # Convert font weight
        if pb_font.get("weight", 400) >= 700:
            flutter_font["fontWeight"] = "FontWeight.bold"

        # Convert font style
        if pb_font.get("italic", False):
            flutter_font["fontStyle"] = "FontStyle.italic"

        # Convert text decoration
        decorations = []
        if pb_font.get("underline", False):
            decorations.append("TextDecoration.underline")
        if pb_font.get("strikethrough", False):
            decorations.append("TextDecoration.lineThrough")

        if decorations:
            flutter_font["decoration"] = " | ".join(decorations)

        return flutter_font

    def get_widget_style(
        self, widget_type: str, pb_props: dict[str, Any]
    ) -> dict[str, Any]:
        """Get Flutter widget style based on PowerBuilder properties.

        Args:
            widget_type: Type of widget
            pb_props: PowerBuilder properties

        Returns:
            Flutter style properties
        """
        style: dict[str, Any] = {}

        # Add elevation based on widget type
        if widget_type in ["Card", "ElevatedButton", "Dialog"]:
            elevation_key = {
                "Card": "card",
                "ElevatedButton": "button",
                "Dialog": "dialog",
            }.get(widget_type, "card")
            style["elevation"] = self.current_theme.elevation[elevation_key]

        # Add border radius
        if widget_type in ["Card", "Container", "ElevatedButton"]:
            style["borderRadius"] = (
                f"BorderRadius.circular({self.current_theme.borderRadius})"
            )

        # Convert background color
        if "backcolor" in pb_props:
            color = self.convert_color(pb_props["backcolor"])
            style["backgroundColor"] = f"Color(0xFF{color[1:]})"

        # Convert border
        if pb_props.get("border", False):
            border_color = self.convert_color(pb_props.get("bordercolor", "black"))
            border_width = pb_props.get("borderwidth", 1)
            style["border"] = (
                f"Border.all(color: Color(0xFF{border_color[1:]}), width: {border_width})"
            )

        # Add padding
        if "padding" in pb_props:
            padding = pb_props["padding"]
            if isinstance(padding, int | float):
                style["padding"] = f"EdgeInsets.all({padding})"
            elif isinstance(padding, dict):
                style["padding"] = (
                    f"EdgeInsets.only("
                    f"left: {padding.get('left', 0)}, "
                    f"top: {padding.get('top', 0)}, "
                    f"right: {padding.get('right', 0)}, "
                    f"bottom: {padding.get('bottom', 0)})"
                )

        return style

    def generate_theme_data(self) -> str:
        """Generate Flutter ThemeData code.

        Returns:
            Flutter ThemeData code string
        """
        theme = self.current_theme
        scheme = theme.colorScheme

        return f"""ThemeData(
            useMaterial3: true,
            colorScheme: ColorScheme(
                brightness: Brightness.light,
                primary: Color(0xFF{scheme.primary[1:]}),
                secondary: Color(0xFF{scheme.secondary[1:]}),
                surface: Color(0xFF{scheme.surface[1:]}),
                background: Color(0xFF{scheme.background[1:]}),
                error: Color(0xFF{scheme.error[1:]}),
                onPrimary: Color(0xFF{scheme.onPrimary[1:]}),
                onSecondary: Color(0xFF{scheme.onSecondary[1:]}),
                onSurface: Color(0xFF{scheme.onSurface[1:]}),
                onBackground: Color(0xFF{scheme.onBackground[1:]}),
                onError: Color(0xFF{scheme.onError[1:]}),
            ),
            fontFamily: '{theme.fontFamily}',
            cardTheme: CardTheme(
                elevation: {theme.elevation["card"]},
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular({theme.borderRadius}),
                ),
            ),
            elevatedButtonTheme: ElevatedButtonThemeData(
                style: ElevatedButton.styleFrom(
                    elevation: {theme.elevation["button"]},
                    shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular({theme.borderRadius}),
                    ),
                ),
            ),
        )"""

    def get_glass_morphism_style(self) -> dict[str, str]:
        """Get glass morphism style for liquid glass theme.

        Returns:
            Glass morphism style properties
        """
        return {
            "backdropFilter": "ImageFilter.blur(sigmaX: 10, sigmaY: 10)",
            "backgroundColor": "Colors.white.withOpacity(0.1)",
            "border": "Border.all(color: Colors.white.withOpacity(0.2))",
            "borderRadius": f"BorderRadius.circular({self.current_theme.borderRadius * 2})",
            "boxShadow": """[
                BoxShadow(
                    color: Colors.black.withOpacity(0.1),
                    blurRadius: 20,
                    offset: Offset(0, 10),
                ),
            ]""",
        }
