"""PowerBuilder to Flutter layout conversion.

This module handles the conversion of PowerBuilder's absolute positioning
to Flutter's widget-based layout system.
"""

import logging
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import math

logger = logging.getLogger(__name__)


class LayoutStrategy(Enum):
    """Layout conversion strategies."""
    ABSOLUTE = "absolute"  # Use Stack/Positioned (preserves exact layout)
    INTELLIGENT = "intelligent"  # Detect rows/columns and use Flutter layouts
    RESPONSIVE = "responsive"  # Convert to responsive layout with breakpoints


@dataclass
class ControlPosition:
    """Represents a control's position and size."""
    x: int
    y: int
    width: int
    height: int
    name: str
    control_type: str
    z_order: int = 0


@dataclass
class LayoutGroup:
    """Represents a group of controls with similar positioning."""
    controls: List[ControlPosition]
    group_type: str  # 'row', 'column', 'grid', 'free'
    bounds: Tuple[int, int, int, int]  # x, y, width, height


class LayoutConverter:
    """Converts PowerBuilder absolute positioning to Flutter layouts."""
    
    def __init__(self, strategy: LayoutStrategy = LayoutStrategy.ABSOLUTE, ui_converter=None, event_wiring_system=None):
        """Initialize the layout converter.
        
        Args:
            strategy: The layout conversion strategy to use
            ui_converter: UIConverter instance for widget generation with glassmorphism
            event_wiring_system: EventWiringSystem instance for handling event wirings
        """
        self.strategy = strategy
        self.position_tolerance = 10  # Pixels tolerance for alignment detection
        self.ui_converter = ui_converter
        self.event_wiring_system = event_wiring_system
        self.event_wirings = []  # Store event wirings
        
    def set_event_wirings(self, wirings: List[Any]):
        """Set event wirings for controls.
        
        Args:
            wirings: List of EventWiring objects
        """
        self.event_wirings = wirings or []
        
    def convert_layout(self, controls: List[Dict[str, Any]], 
                      window_width: int = 800, 
                      window_height: int = 600) -> str:
        """Convert PowerBuilder control layout to Flutter widget tree.
        
        Args:
            controls: List of controls with position data
            window_width: Window width in pixels
            window_height: Window height in pixels
            
        Returns:
            Flutter widget code as string
        """
        if not controls:
            return "Center(child: Text('No controls defined'))"
            
        if self.strategy == LayoutStrategy.ABSOLUTE:
            return self._convert_absolute_layout(controls, window_width, window_height)
        elif self.strategy == LayoutStrategy.INTELLIGENT:
            return self._convert_intelligent_layout(controls, window_width, window_height)
        else:  # RESPONSIVE
            return self._convert_responsive_layout(controls, window_width, window_height)
    
    def _convert_absolute_layout(self, controls: List[Dict[str, Any]], 
                                window_width: int, window_height: int) -> str:
        """Convert to absolute positioning using Stack/Positioned.
        
        This preserves the exact PowerBuilder layout including Z-order.
        """
        # Sort controls by z-order (tab_order in PowerBuilder)
        # Lower values are drawn first (behind higher values)
        sorted_controls = sorted(controls, 
                               key=lambda c: c.get("properties", {}).get("tab_order", 999999))
        
        code = "Stack(\n          children: [\n"
        
        for control in sorted_controls:
            # Extract position data
            position = control.get("position", {})
            size = control.get("size", {})
            x = position.get("x", 0)
            y = position.get("y", 0)
            width = size.get("width", 100)
            height = size.get("height", 30)
            
            # Get the Flutter widget
            widget_code = self._build_control_widget(control)
            
            # Add comment for z-order debugging
            tab_order = control.get("properties", {}).get("tab_order", 999999)
            code += f"            // {control.get('name', 'unknown')} - tab_order: {tab_order}\n"
            
            # Wrap in Positioned
            code += f"            Positioned(\n"
            code += f"              left: {x}.0,\n"
            code += f"              top: {y}.0,\n"
            code += f"              width: {width}.0,\n"
            code += f"              height: {height}.0,\n"
            code += f"              child: {widget_code},\n"
            code += f"            ),\n"
        
        code += "          ],\n        )"
        return code
    
    def _convert_intelligent_layout(self, controls: List[Dict[str, Any]], 
                                   window_width: int, window_height: int) -> str:
        """Convert to Flutter layout widgets by detecting rows/columns.
        
        This creates a more Flutter-like responsive layout.
        """
        # Create ControlPosition objects
        positions = []
        for control in controls:
            pos = control.get("position", {})
            size = control.get("size", {})
            z_order = control.get("properties", {}).get("tab_order", 999999)
            positions.append(ControlPosition(
                x=pos.get("x", 0),
                y=pos.get("y", 0),
                width=size.get("width", 100),
                height=size.get("height", 30),
                name=control.get("name", ""),
                control_type=control.get("type", ""),
                z_order=z_order
            ))
        
        # Detect layout groups
        groups = self._detect_layout_groups(positions)
        
        # Generate Flutter layout
        return self._generate_intelligent_layout(groups, controls)
    
    def _convert_responsive_layout(self, controls: List[Dict[str, Any]], 
                                  window_width: int, window_height: int) -> str:
        """Convert to responsive layout using LayoutBuilder with breakpoints.
        
        This creates an adaptive layout that responds to different screen sizes
        with appropriate breakpoints and layout strategies.
        """
        code = "LayoutBuilder(\n"
        code += "          builder: (context, constraints) {\n"
        
        # Define breakpoints
        code += "            // Responsive breakpoints\n"
        code += "            final isMobile = constraints.maxWidth < 600;\n"
        code += "            final isTablet = constraints.maxWidth >= 600 && constraints.maxWidth < 900;\n"
        code += "            final isDesktop = constraints.maxWidth >= 900;\n"
        code += "            \n"
        
        # Calculate scaling factors with constraints
        code += "            // Calculate responsive scaling\n"
        code += "            final baseWidth = {}.0;\n".format(window_width)
        code += "            final baseHeight = {}.0;\n".format(window_height)
        code += "            final scaleX = math.min(constraints.maxWidth / baseWidth, 2.0);\n"
        code += "            final scaleY = math.min(constraints.maxHeight / baseHeight, 2.0);\n"
        code += "            final scale = math.min(scaleX, scaleY);\n"
        code += "            \n"
        
        # Determine layout strategy based on screen size
        code += "            // Choose layout strategy based on screen size\n"
        code += "            if (isMobile) {\n"
        code += "              return _buildMobileLayout(context, scale);\n"
        code += "            } else if (isTablet) {\n"
        code += "              return _buildTabletLayout(context, scale);\n"
        code += "            } else {\n"
        code += "              return _buildDesktopLayout(context, scale);\n"
        code += "            }\n"
        code += "          },\n"
        code += "        )"
        
        return code
    
    def _detect_layout_groups(self, positions: List[ControlPosition]) -> List[LayoutGroup]:
        """Detect rows, columns, and other layout patterns.
        
        Args:
            positions: List of control positions
            
        Returns:
            List of detected layout groups
        """
        groups = []
        used_controls = set()
        
        # First try to detect grid patterns
        grid_groups = self._detect_grid_patterns(positions)
        for grid_group in grid_groups:
            if len(grid_group) > 3:  # Minimum 4 controls for a grid
                groups.append(self._create_group(grid_group, "grid"))
                used_controls.update(p.name for p in grid_group)
        
        # Detect rows (controls with similar Y coordinates)
        row_groups = self._detect_aligned_groups(
            [p for p in positions if p.name not in used_controls],
            alignment="horizontal"
        )
        for row in row_groups:
            if len(row) > 1:
                groups.append(self._create_group(row, "row"))
                used_controls.update(p.name for p in row)
        
        # Detect columns (controls with similar X coordinates)
        col_groups = self._detect_aligned_groups(
            [p for p in positions if p.name not in used_controls],
            alignment="vertical"
        )
        for col in col_groups:
            if len(col) > 1:
                groups.append(self._create_group(col, "column"))
                used_controls.update(p.name for p in col)
        
        # Add ungrouped controls as free-positioned
        for pos in positions:
            if pos.name not in used_controls:
                groups.append(self._create_group([pos], "free"))
        
        return groups
    
    def _detect_aligned_groups(self, positions: List[ControlPosition], 
                               alignment: str) -> List[List[ControlPosition]]:
        """Detect groups of aligned controls.
        
        Args:
            positions: List of control positions
            alignment: 'horizontal' for rows or 'vertical' for columns
            
        Returns:
            List of aligned control groups
        """
        if not positions:
            return []
        
        groups = []
        
        if alignment == "horizontal":
            # Sort by Y position to detect rows
            sorted_positions = sorted(positions, key=lambda p: p.y)
            coord_getter = lambda p: p.y
        else:  # vertical
            # Sort by X position to detect columns
            sorted_positions = sorted(positions, key=lambda p: p.x)
            coord_getter = lambda p: p.x
        
        current_group = []
        current_coord = None
        
        for pos in sorted_positions:
            if current_coord is None:
                current_group = [pos]
                current_coord = coord_getter(pos)
            elif abs(coord_getter(pos) - current_coord) <= self.position_tolerance:
                current_group.append(pos)
                # Update current_coord to be the average for better tolerance
                current_coord = sum(coord_getter(p) for p in current_group) / len(current_group)
            else:
                # Start new group
                if len(current_group) > 1:
                    groups.append(current_group)
                current_group = [pos]
                current_coord = coord_getter(pos)
        
        # Don't forget the last group
        if len(current_group) > 1:
            groups.append(current_group)
        
        return groups
    
    def _detect_grid_patterns(self, positions: List[ControlPosition]) -> List[List[ControlPosition]]:
        """Detect grid patterns in control positions.
        
        Returns:
            List of control groups that form grids
        """
        grid_groups = []
        
        # For each control, try to find other controls that form a grid with it
        for i, anchor in enumerate(positions):
            grid_candidates = [anchor]
            
            # Find controls aligned horizontally with anchor
            horizontal_aligned = [p for p in positions[i+1:] 
                                if abs(p.y - anchor.y) <= self.position_tolerance]
            
            # Find controls aligned vertically with anchor
            vertical_aligned = [p for p in positions[i+1:]
                              if abs(p.x - anchor.x) <= self.position_tolerance]
            
            # Find controls that form a grid
            if horizontal_aligned and vertical_aligned:
                # Check if we can form a grid
                for h_control in horizontal_aligned:
                    for v_control in vertical_aligned:
                        # Look for the fourth corner
                        corner = next((p for p in positions 
                                     if abs(p.x - h_control.x) <= self.position_tolerance
                                     and abs(p.y - v_control.y) <= self.position_tolerance
                                     and p != anchor and p != h_control and p != v_control), None)
                        
                        if corner:
                            grid_candidates.extend([h_control, v_control, corner])
            
            if len(grid_candidates) >= 4:
                # Remove duplicates while preserving order
                seen = set()
                unique_grid = []
                for control in grid_candidates:
                    if control.name not in seen:
                        seen.add(control.name)
                        unique_grid.append(control)
                
                if len(unique_grid) >= 4:
                    grid_groups.append(unique_grid)
        
        # Remove overlapping grids (keep the larger ones)
        final_grids = []
        for grid in sorted(grid_groups, key=len, reverse=True):
            # Check if any control in this grid is already in a final grid
            if not any(control.name in [c.name for g in final_grids for c in g] 
                      for control in grid):
                final_grids.append(grid)
        
        return final_grids
    
    def _create_group(self, controls: List[ControlPosition], group_type: str) -> LayoutGroup:
        """Create a layout group from controls."""
        min_x = min(c.x for c in controls)
        min_y = min(c.y for c in controls)
        max_x = max(c.x + c.width for c in controls)
        max_y = max(c.y + c.height for c in controls)
        
        return LayoutGroup(
            controls=controls,
            group_type=group_type,
            bounds=(min_x, min_y, max_x - min_x, max_y - min_y)
        )
    
    def _generate_intelligent_layout(self, groups: List[LayoutGroup], 
                                   original_controls: List[Dict[str, Any]]) -> str:
        """Generate Flutter layout code from detected groups."""
        if len(groups) == 1 and groups[0].group_type == "free":
            # Only one free control, just return it
            return self._build_control_widget(original_controls[0])
        
        # Build a column of groups
        code = "Column(\n          children: [\n"
        
        # Sort groups by Y position
        sorted_groups = sorted(groups, key=lambda g: g.bounds[1])
        
        for i, group in enumerate(sorted_groups):
            if i > 0:
                # Add spacing between groups
                prev_group = sorted_groups[i-1]
                spacing = group.bounds[1] - (prev_group.bounds[1] + prev_group.bounds[3])
                if spacing > 0:
                    code += f"            SizedBox(height: {spacing}),\n"
            
            if group.group_type == "row":
                code += self._generate_row_layout(group, original_controls)
            elif group.group_type == "column":
                code += self._generate_column_layout(group, original_controls)
            elif group.group_type == "grid":
                code += self._generate_grid_layout(group, original_controls)
            else:  # free
                # Use positioned for free controls within the column
                code += self._generate_free_layout(group, original_controls)
        
        code += "          ],\n        )"
        return code
    
    def _generate_row_layout(self, group: LayoutGroup, 
                           original_controls: List[Dict[str, Any]]) -> str:
        """Generate a Row widget for horizontally aligned controls."""
        code = "            Row(\n"
        code += "              children: [\n"
        
        # Sort controls by X position
        sorted_controls = sorted(group.controls, key=lambda c: c.x)
        
        for i, control_pos in enumerate(sorted_controls):
            if i > 0:
                # Add spacing between controls
                prev_control = sorted_controls[i-1]
                spacing = control_pos.x - (prev_control.x + prev_control.width)
                if spacing > 0:
                    code += f"                SizedBox(width: {spacing}),\n"
            
            # Find original control data
            control = next((c for c in original_controls if c.get("name") == control_pos.name), None)
            if control:
                widget = self._build_control_widget(control)
                code += f"                SizedBox(\n"
                code += f"                  width: {control_pos.width}.0,\n"
                code += f"                  height: {control_pos.height}.0,\n"
                code += f"                  child: {widget},\n"
                code += f"                ),\n"
        
        code += "              ],\n"
        code += "            ),\n"
        return code
    
    def _generate_column_layout(self, group: LayoutGroup,
                              original_controls: List[Dict[str, Any]]) -> str:
        """Generate a Column widget for vertically aligned controls."""
        code = "            Column(\n"
        code += "              children: [\n"
        
        # Sort controls by Y position
        sorted_controls = sorted(group.controls, key=lambda c: c.y)
        
        for i, control_pos in enumerate(sorted_controls):
            if i > 0:
                # Add spacing between controls
                prev_control = sorted_controls[i-1]
                spacing = control_pos.y - (prev_control.y + prev_control.height)
                if spacing > 0:
                    code += f"                SizedBox(height: {spacing}),\n"
            
            # Find original control data
            control = next((c for c in original_controls if c.get("name") == control_pos.name), None)
            if control:
                widget = self._build_control_widget(control)
                code += f"                SizedBox(\n"
                code += f"                  width: {control_pos.width}.0,\n"
                code += f"                  height: {control_pos.height}.0,\n"
                code += f"                  child: {widget},\n"
                code += f"                ),\n"
        
        code += "              ],\n"
        code += "            ),\n"
        return code
    
    def _generate_grid_layout(self, group: LayoutGroup,
                            original_controls: List[Dict[str, Any]]) -> str:
        """Generate a GridView widget for grid-aligned controls."""
        # Determine grid dimensions
        x_positions = sorted(set(c.x for c in group.controls))
        y_positions = sorted(set(c.y for c in group.controls))
        
        cols = len(x_positions)
        rows = len(y_positions)
        
        # Create position map
        position_map = {}
        for control_pos in group.controls:
            # Find grid indices
            col_idx = x_positions.index(control_pos.x) if control_pos.x in x_positions else 0
            row_idx = y_positions.index(control_pos.y) if control_pos.y in y_positions else 0
            position_map[(row_idx, col_idx)] = control_pos
        
        code = "            GridView.count(\n"
        code += f"              crossAxisCount: {cols},\n"
        code += "              shrinkWrap: true,\n"
        code += "              physics: NeverScrollableScrollPhysics(),\n"
        code += "              children: [\n"
        
        # Generate grid cells in order
        for row in range(rows):
            for col in range(cols):
                if (row, col) in position_map:
                    control_pos = position_map[(row, col)]
                    control = next((c for c in original_controls 
                                  if c.get("name") == control_pos.name), None)
                    if control:
                        widget = self._build_control_widget(control)
                        code += f"                Padding(\n"
                        code += f"                  padding: EdgeInsets.all(4),\n"
                        code += f"                  child: {widget},\n"
                        code += f"                ),\n"
                else:
                    # Empty cell
                    code += "                Container(),\n"
        
        code += "              ],\n"
        code += "            ),\n"
        return code
    
    def _generate_free_layout(self, group: LayoutGroup, 
                            original_controls: List[Dict[str, Any]]) -> str:
        """Generate layout for free-positioned controls."""
        # For now, just return the control
        # In a full implementation, this might use Container with margins
        control = next((c for c in original_controls 
                       if c.get("name") == group.controls[0].name), None)
        if control:
            return f"            {self._build_control_widget(control)},\n"
        return ""
    
    def generate_responsive_layout_methods(self, controls: List[Dict[str, Any]],
                                          window_width: int, window_height: int) -> str:
        """Generate responsive layout helper methods for mobile, tablet, and desktop.
        
        These methods will be added to the generated screen/window class.
        """
        code = ""
        
        # Create position data for controls
        positions = []
        for control in controls:
            pos = control.get("position", {})
            size = control.get("size", {})
            z_order = control.get("properties", {}).get("tab_order", 999999)
            positions.append(ControlPosition(
                x=pos.get("x", 0),
                y=pos.get("y", 0),
                width=size.get("width", 100),
                height=size.get("height", 30),
                name=control.get("name", ""),
                control_type=control.get("type", ""),
                z_order=z_order
            ))
        
        # Detect layout groups for intelligent responsive behavior
        groups = self._detect_layout_groups(positions)
        
        # Generate mobile layout method
        code += "\n  Widget _buildMobileLayout(BuildContext context, double scale) {\n"
        code += "    return SingleChildScrollView(\n"
        code += "      child: Padding(\n"
        code += "        padding: EdgeInsets.all(16),\n"
        code += "        child: Column(\n"
        code += "          crossAxisAlignment: CrossAxisAlignment.stretch,\n"
        code += "          children: [\n"
        
        # For mobile, stack controls vertically
        for control in controls:
            widget = self._build_control_widget(control)
            name = control.get("name", "unknown")
            code += f"            // {name}\n"
            code += "            Padding(\n"
            code += "              padding: EdgeInsets.symmetric(vertical: 8),\n"
            code += f"              child: {widget},\n"
            code += "            ),\n"
        
        code += "          ],\n"
        code += "        ),\n"
        code += "      ),\n"
        code += "    );\n"
        code += "  }\n\n"
        
        # Generate tablet layout method
        code += "  Widget _buildTabletLayout(BuildContext context, double scale) {\n"
        code += "    return SingleChildScrollView(\n"
        code += "      child: Padding(\n"
        code += "        padding: EdgeInsets.all(24),\n"
        code += "        child: "
        
        # For tablet, use intelligent grouping with some scaling
        if len(groups) > 1:
            code += self._generate_intelligent_layout(groups, controls)
        else:
            # Fall back to scaled absolute positioning
            # Sort by z-order for proper layering
            sorted_controls = sorted(controls, 
                                   key=lambda c: c.get("properties", {}).get("tab_order", 999999))
            
            code += "Stack(\n"
            code += "          children: [\n"
            for control in sorted_controls:
                pos = control.get("position", {})
                size = control.get("size", {})
                widget = self._build_control_widget(control)
                code += f"            Positioned(\n"
                code += f"              left: {pos.get('x', 0)} * scale * 0.8,\n"
                code += f"              top: {pos.get('y', 0)} * scale * 0.8,\n"
                code += f"              width: {size.get('width', 100)} * scale * 0.8,\n"
                code += f"              height: {size.get('height', 30)} * scale * 0.8,\n"
                code += f"              child: {widget},\n"
                code += "            ),\n"
            code += "          ],\n"
            code += "        )"
        
        code += ",\n"
        code += "      ),\n"
        code += "    );\n"
        code += "  }\n\n"
        
        # Generate desktop layout method
        code += "  Widget _buildDesktopLayout(BuildContext context, double scale) {\n"
        code += "    return Padding(\n"
        code += "      padding: EdgeInsets.all(32),\n"
        code += "      child: "
        
        # For desktop, use full absolute positioning with scaling
        # Sort by z-order for proper layering
        sorted_controls = sorted(controls, 
                               key=lambda c: c.get("properties", {}).get("tab_order", 999999))
        
        code += "Stack(\n"
        code += "          children: [\n"
        
        for control in sorted_controls:
            pos = control.get("position", {})
            size = control.get("size", {})
            widget = self._build_control_widget(control)
            
            code += f"            Positioned(\n"
            code += f"              left: {pos.get('x', 0)} * scale,\n"
            code += f"              top: {pos.get('y', 0)} * scale,\n"
            code += f"              width: {size.get('width', 100)} * scale,\n"
            code += f"              height: {size.get('height', 30)} * scale,\n"
            code += f"              child: {widget},\n"
            code += "            ),\n"
        
        code += "          ],\n"
        code += "        ),\n"
        code += "    );\n"
        code += "  }\n"
        
        return code
    
    def _build_control_widget(self, control: Dict[str, Any]) -> str:
        """Build the Flutter widget for a control.
        
        Uses EventWiringSystem if available for event handling,
        UIConverter if available for proper glassmorphism support.
        """
        control_name = control.get("name", "")
        
        # Check if we have event wirings for this control
        if self.event_wiring_system and self.event_wirings:
            # Find wirings for this control
            control_wirings = [w for w in self.event_wirings if w.control_name == control_name]
            if control_wirings:
                # Use event wiring system to generate widget with events
                return self.event_wiring_system.generate_control_with_events(control, control_wirings)
        
        # Use UIConverter if available for full glassmorphism support
        if self.ui_converter and hasattr(self.ui_converter, '_generate_widget_code'):
            # Extract flutter_widget if it exists, otherwise return simple widget
            if 'flutter_widget' in control and isinstance(control['flutter_widget'], dict):
                return self.ui_converter._generate_widget_code(control['flutter_widget'])
            else:
                # If no flutter_widget info, fall through to simple generation
                pass
        
        # Fallback to simple generation if no UIConverter
        flutter_widget = control.get("flutter_widget", {})
        widget_type = flutter_widget.get("widget", "Container")
        widget_name = control.get("name", "unknown")
        
        # Build basic widget based on type
        if widget_type == "Text":
            text = flutter_widget.get('flutter_properties', {}).get('data', widget_name)
            return f"Text('{text}')"
        elif widget_type == "TextField":
            return f"TextField(controller: {widget_name}Controller)"
        elif widget_type == "ElevatedButton":
            text = flutter_widget.get('flutter_properties', {}).get('text', widget_name)
            return f"ElevatedButton(onPressed: () {{}}, child: Text('{text}'))"
        elif widget_type == "Checkbox":
            return f"Checkbox(value: false, onChanged: (value) {{}})"
        elif widget_type == "DropdownButton":
            return "DropdownButton<String>(items: [], onChanged: (value) {})"
        elif widget_type == "Container" and control.get("type") == "rectangle":
            # Rectangle shape
            color = flutter_widget.get('flutter_properties', {}).get('_fillColor', 'Colors.grey')
            return f"Container(decoration: BoxDecoration(color: {color}, border: Border.all()))"
        else:
            return f"Container() // {widget_type} - {widget_name}"