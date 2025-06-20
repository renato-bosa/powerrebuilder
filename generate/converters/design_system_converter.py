"""Design system converter for modern UI aesthetics.

Converts PowerBuilder UI elements to use modern design systems like
Apple's Liquid Glass (glassmorphism) in Flutter/Dart.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import json
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class GlassmorphicStyle:
    """Represents glassmorphic styling properties."""
    blur: float = 20.0
    opacity: float = 0.1
    border_opacity: float = 0.2
    border_width: float = 1.5
    light_intensity: float = 1.2
    thickness: float = 10.0
    border_radius: float = 20.0
    
    def to_flutter(self) -> Dict[str, Any]:
        """Convert to Flutter glassmorphism properties."""
        return {
            'blur': self.blur,
            'linearGradient': {
                'colors': [
                    f'Color(0xFFFFFFFF).withOpacity({self.opacity})',
                    f'Color(0xFFFFFFFF).withOpacity({self.opacity * 0.5})',
                ],
                'stops': [0.1, 1.0],
            },
            'borderGradient': {
                'colors': [
                    f'Color(0xFFFFFFFF).withOpacity({self.border_opacity})',
                    f'Color(0xFFFFFFFF).withOpacity({self.border_opacity * 0.5})',
                ],
            },
            'border': self.border_width,
            'borderRadius': self.border_radius,
        }


@dataclass
class IconMapping:
    """Represents an icon mapping from PowerBuilder to modern icons."""
    pb_name: str
    modern_icon: str
    icon_library: str = "material"  # material, cupertino, sf_symbols, custom
    keywords: List[str] = field(default_factory=list)
    confidence: float = 1.0
    
    def to_flutter_import(self) -> Optional[str]:
        """Get Flutter import statement for this icon."""
        imports = {
            'material': "import 'package:flutter/material.dart';",
            'cupertino': "import 'package:flutter/cupertino.dart';",
            'sf_symbols': "import 'package:flutter_sficon/flutter_sficon.dart';",
            'custom': None
        }
        return imports.get(self.icon_library)
    
    def to_flutter_code(self) -> str:
        """Get Flutter code for this icon."""
        if self.icon_library == 'material':
            return f'Icons.{self.modern_icon}'
        elif self.icon_library == 'cupertino':
            return f'CupertinoIcons.{self.modern_icon}'
        elif self.icon_library == 'sf_symbols':
            return f'SFIcons.{self.modern_icon}'
        else:
            return f'CustomIcons.{self.modern_icon}'


class DesignSystemConverter:
    """Converts PowerBuilder UI to modern design systems."""
    
    def __init__(self, design_theme: str = "liquid_glass"):
        """Initialize the design system converter.
        
        Args:
            design_theme: Theme to apply ('liquid_glass', 'material', 'fluent')
        """
        self.design_theme = design_theme
        self.icon_mappings = self._load_icon_mappings()
        self.ml_classifier = None  # Lazy load if needed
        
        # Define glassmorphic styles for different UI elements
        self.glass_styles = {
            'window': GlassmorphicStyle(blur=30, opacity=0.08, border_radius=16),
            'panel': GlassmorphicStyle(blur=20, opacity=0.1, border_radius=12),
            'button': GlassmorphicStyle(blur=15, opacity=0.15, border_radius=8),
            'card': GlassmorphicStyle(blur=25, opacity=0.12, border_radius=16),
            'dialog': GlassmorphicStyle(blur=40, opacity=0.1, border_radius=20),
            'toolbar': GlassmorphicStyle(blur=35, opacity=0.07, border_radius=0),
            'menu': GlassmorphicStyle(blur=30, opacity=0.08, border_radius=12),
            'datawindow': GlassmorphicStyle(blur=10, opacity=0.05, border_radius=8),
        }
    
    def _load_icon_mappings(self) -> Dict[str, IconMapping]:
        """Load predefined icon mappings."""
        mappings = {}
        
        # Common PowerBuilder toolbar icons to modern equivalents
        common_mappings = [
            # File operations
            IconMapping('new', 'add_box', 'material', ['new', 'create', 'add']),
            IconMapping('open', 'folder_open', 'material', ['open', 'folder', 'browse']),
            IconMapping('save', 'save', 'material', ['save', 'disk']),
            IconMapping('saveas', 'save_as', 'material', ['save', 'as']),
            IconMapping('close', 'close', 'material', ['close', 'exit']),
            IconMapping('print', 'print', 'material', ['print', 'printer']),
            IconMapping('preview', 'preview', 'material', ['preview', 'view']),
            
            # Edit operations
            IconMapping('cut', 'cut', 'material', ['cut', 'scissors']),
            IconMapping('copy', 'copy', 'material', ['copy', 'duplicate']),
            IconMapping('paste', 'paste', 'material', ['paste', 'clipboard']),
            IconMapping('undo', 'undo', 'material', ['undo', 'back']),
            IconMapping('redo', 'redo', 'material', ['redo', 'forward']),
            IconMapping('delete', 'delete', 'material', ['delete', 'remove', 'trash']),
            IconMapping('clear', 'clear', 'material', ['clear', 'erase']),
            
            # Navigation
            IconMapping('first', 'first_page', 'material', ['first', 'begin', 'start']),
            IconMapping('prior', 'navigate_before', 'material', ['previous', 'back']),
            IconMapping('next', 'navigate_next', 'material', ['next', 'forward']),
            IconMapping('last', 'last_page', 'material', ['last', 'end']),
            IconMapping('retrieve', 'refresh', 'material', ['retrieve', 'refresh', 'reload']),
            
            # View operations
            IconMapping('zoom', 'zoom_in', 'material', ['zoom', 'magnify']),
            IconMapping('filter', 'filter_list', 'material', ['filter', 'funnel']),
            IconMapping('sort', 'sort', 'material', ['sort', 'order']),
            IconMapping('find', 'search', 'material', ['find', 'search', 'locate']),
            IconMapping('help', 'help_outline', 'material', ['help', 'question']),
            IconMapping('info', 'info_outline', 'material', ['info', 'information']),
            
            # Data operations
            IconMapping('insert', 'add_circle_outline', 'material', ['insert', 'add', 'new']),
            IconMapping('update', 'edit', 'material', ['update', 'edit', 'modify']),
            IconMapping('cancel', 'cancel', 'material', ['cancel', 'abort']),
            IconMapping('ok', 'check_circle', 'material', ['ok', 'confirm', 'accept']),
            
            # SF Symbols for Apple-like design
            IconMapping('new', 'sf_plus_square', 'sf_symbols', ['new', 'create']),
            IconMapping('save', 'sf_square_and_arrow_down', 'sf_symbols', ['save']),
            IconMapping('share', 'sf_square_and_arrow_up', 'sf_symbols', ['share', 'export']),
            IconMapping('settings', 'sf_gear', 'sf_symbols', ['settings', 'preferences']),
            IconMapping('user', 'sf_person_circle', 'sf_symbols', ['user', 'account']),
        ]
        
        for mapping in common_mappings:
            # Store by PowerBuilder name and keywords
            mappings[mapping.pb_name.lower()] = mapping
            for keyword in mapping.keywords:
                if keyword not in mappings:
                    mappings[keyword] = mapping
        
        return mappings
    
    def convert_icon(self, pb_icon_name: str, context: Dict[str, Any] = None) -> IconMapping:
        """Convert a PowerBuilder icon to a modern icon.
        
        Args:
            pb_icon_name: PowerBuilder icon name or path
            context: Additional context (control type, business logic, etc.)
            
        Returns:
            IconMapping with the best match
        """
        # Clean icon name
        icon_key = self._extract_icon_key(pb_icon_name)
        
        # 1. Try direct mapping
        if icon_key in self.icon_mappings:
            return self.icon_mappings[icon_key]
        
        # 2. Try keyword matching
        keywords = self._extract_keywords(pb_icon_name, context)
        for keyword in keywords:
            if keyword in self.icon_mappings:
                mapping = self.icon_mappings[keyword]
                mapping.confidence = 0.8  # Lower confidence for keyword match
                return mapping
        
        # 3. Try ML-based matching (if available)
        if self.ml_classifier:
            ml_match = self._ml_match_icon(pb_icon_name, context)
            if ml_match:
                return ml_match
        
        # 4. Fallback based on context
        return self._contextual_fallback(pb_icon_name, context)
    
    def _extract_icon_key(self, icon_name: str) -> str:
        """Extract a clean key from icon name."""
        # Remove path and extension
        name = Path(icon_name).stem
        # Remove common prefixes/suffixes
        name = re.sub(r'^(pb_|btn_|ico_|icon_)', '', name, flags=re.IGNORECASE)
        name = re.sub(r'(_icon|_btn|_button)$', '', name, flags=re.IGNORECASE)
        return name.lower()
    
    def _extract_keywords(self, icon_name: str, context: Dict[str, Any] = None) -> List[str]:
        """Extract keywords from icon name and context."""
        keywords = []
        
        # From icon name
        clean_name = self._extract_icon_key(icon_name)
        keywords.extend(clean_name.split('_'))
        
        # From context
        if context:
            if 'control_type' in context:
                keywords.append(context['control_type'].lower())
            if 'action' in context:
                keywords.append(context['action'].lower())
            if 'tooltip' in context:
                keywords.extend(context['tooltip'].lower().split())
        
        return list(set(keywords))
    
    def _ml_match_icon(self, icon_path: str, context: Dict[str, Any] = None) -> Optional[IconMapping]:
        """Use ML to match icon (placeholder for ML implementation)."""
        # This would use TensorFlow Lite or similar to:
        # 1. Extract visual features from the icon
        # 2. Compare with modern icon database
        # 3. Return best match with confidence score
        
        # For now, return None (would implement actual ML logic)
        return None
    
    def _contextual_fallback(self, icon_name: str, context: Dict[str, Any] = None) -> IconMapping:
        """Provide fallback icon based on context."""
        if context:
            control_type = context.get('control_type', '').lower()
            
            # Control-specific defaults
            defaults = {
                'commandbutton': 'touch_app',
                'datawindow': 'table_chart',
                'treeview': 'account_tree',
                'listbox': 'list',
                'dropdown': 'arrow_drop_down',
                'checkbox': 'check_box_outline_blank',
                'radiobutton': 'radio_button_unchecked',
            }
            
            if control_type in defaults:
                return IconMapping(
                    pb_name=icon_name,
                    modern_icon=defaults[control_type],
                    icon_library='material',
                    confidence=0.5
                )
        
        # Generic fallback
        return IconMapping(
            pb_name=icon_name,
            modern_icon='help_outline',
            icon_library='material',
            confidence=0.3
        )
    
    def apply_glassmorphism(self, control_type: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Apply glassmorphic styling to a control.
        
        Args:
            control_type: Type of control (window, button, etc.)
            properties: Original control properties
            
        Returns:
            Enhanced properties with glassmorphism
        """
        if self.design_theme != 'liquid_glass':
            return properties
        
        # Get appropriate glass style
        glass_style = self.glass_styles.get(control_type.lower(), self.glass_styles['panel'])
        
        # Apply glassmorphic properties
        enhanced = properties.copy()
        enhanced['glassmorphic'] = glass_style.to_flutter()
        
        # Adjust colors for glass effect
        if 'background_color' in enhanced:
            # Make background semi-transparent
            enhanced['background_color'] = 'Colors.white.withOpacity(0.1)'
        
        # Add backdrop blur
        enhanced['needs_backdrop_filter'] = True
        
        # Enhance borders
        if 'border' not in enhanced:
            enhanced['border'] = {}
        enhanced['border']['gradient'] = True
        
        return enhanced
    
    def generate_glass_container(self, control: Dict[str, Any], child_widget: str) -> List[str]:
        """Generate Flutter code for a glassmorphic container.
        
        Args:
            control: Control properties
            child_widget: Widget code to wrap
            
        Returns:
            Flutter code lines
        """
        lines = []
        
        if 'glassmorphic' in control:
            glass = control['glassmorphic']
            
            lines.append("GlassmorphicContainer(")
            lines.append(f"  width: {control.get('width', 'double.infinity')},")
            lines.append(f"  height: {control.get('height', 'double.infinity')},")
            lines.append(f"  borderRadius: {glass['borderRadius']},")
            lines.append(f"  blur: {glass['blur']},")
            lines.append(f"  border: {glass['border']},")
            lines.append("  linearGradient: LinearGradient(")
            lines.append("    begin: Alignment.topLeft,")
            lines.append("    end: Alignment.bottomRight,")
            lines.append(f"    colors: [{glass['linearGradient']['colors'][0]}, {glass['linearGradient']['colors'][1]}],")
            lines.append(f"    stops: {glass['linearGradient']['stops']},")
            lines.append("  ),")
            lines.append("  borderGradient: LinearGradient(")
            lines.append("    begin: Alignment.topLeft,")
            lines.append("    end: Alignment.bottomRight,")
            lines.append(f"    colors: [{glass['borderGradient']['colors'][0]}, {glass['borderGradient']['colors'][1]}],")
            lines.append("  ),")
            lines.append("  child: " + child_widget + ",")
            lines.append(")")
        else:
            # Fallback to regular container
            lines.append("Container(")
            if 'width' in control:
                lines.append(f"  width: {control['width']},")
            if 'height' in control:
                lines.append(f"  height: {control['height']},")
            lines.append("  child: " + child_widget + ",")
            lines.append(")")
        
        return lines
    
    def get_required_packages(self) -> List[str]:
        """Get required Flutter packages for the design system."""
        packages = []
        
        if self.design_theme == 'liquid_glass':
            packages.append('glassmorphism: ^3.0.0')
        
        # Check if we need icon packages
        used_libraries = set()
        for mapping in self.icon_mappings.values():
            used_libraries.add(mapping.icon_library)
        
        if 'sf_symbols' in used_libraries:
            packages.append('flutter_sficon: ^1.0.2')
        
        return packages
    
    def generate_theme_extensions(self) -> Dict[str, List[str]]:
        """Generate theme extensions for the design system."""
        extensions = {
            'colors': [],
            'decorations': [],
            'animations': []
        }
        
        if self.design_theme == 'liquid_glass':
            # Glass-specific colors
            extensions['colors'] = [
                "static const glassBackground = Color(0x0DFFFFFF);",
                "static const glassBorder = Color(0x33FFFFFF);",
                "static const glassHighlight = Color(0x1AFFFFFF);",
            ]
            
            # Glass decorations
            extensions['decorations'] = [
                "static BoxDecoration glassDecoration({double radius = 20}) {",
                "  return BoxDecoration(",
                "    borderRadius: BorderRadius.circular(radius),",
                "    border: Border.all(color: glassBorder, width: 1.5),",
                "    gradient: LinearGradient(",
                "      begin: Alignment.topLeft,",
                "      end: Alignment.bottomRight,",
                "      colors: [glassHighlight, glassBackground],",
                "    ),",
                "  );",
                "}",
            ]
            
            # Smooth animations
            extensions['animations'] = [
                "static const glassAnimationDuration = Duration(milliseconds: 300);",
                "static const glassAnimationCurve = Curves.easeInOutCubic;",
            ]
        
        return extensions