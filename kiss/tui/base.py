"""Base Component System for XSINT TUI.

Provides foundation for all UI components with consistent behavior.
"""

import curses
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple, List
from ..tui.colors import get_color_manager


class Component(ABC):
    """Base class for all TUI components."""

    def __init__(
        self, parent, x: int = 0, y: int = 0, width: int = 10, height: int = 3
    ):
        """Initialize component with position and dimensions."""
        self.parent = parent
        self.stdscr = parent.stdscr if hasattr(parent, "stdscr") else parent
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.visible = True
        self.focused = False
        self.enabled = True
        self.color_manager = get_color_manager()

        # Component state
        self.state = {}
        self.children = []
        self.event_handlers = {}

        # Layout properties
        self.margin_top = 0
        self.margin_bottom = 0
        self.margin_left = 0
        self.margin_right = 0
        self.padding_top = 0
        self.padding_bottom = 0
        self.padding_left = 0
        self.padding_right = 0

        # Content area (excluding padding)
        self.content_x = x + self.padding_left
        self.content_y = y + self.padding_top
        self.content_width = width - self.padding_left - self.padding_right
        self.content_height = height - self.padding_top - self.padding_bottom

    @abstractmethod
    def render(self):
        """Render the component."""
        pass

    def get_content_bounds(self) -> Tuple[int, int, int, int]:
        """Get the content area bounds (x, y, width, height)."""
        return (self.content_x, self.content_y, self.content_width, self.content_height)

    def set_position(self, x: int, y: int):
        """Set component position."""
        self.x = x
        self.y = y
        self.content_x = x + self.padding_left
        self.content_y = y + self.padding_top

    def set_size(self, width: int, height: int):
        """Set component size."""
        self.width = width
        self.height = height
        self.content_width = width - self.padding_left - self.padding_right
        self.content_height = height - self.padding_top - self.padding_bottom

    def set_padding(self, top: int = 0, bottom: int = 0, left: int = 0, right: int = 0):
        """Set component padding."""
        self.padding_top = top
        self.padding_bottom = bottom
        self.padding_left = left
        self.padding_right = right
        self.content_x = self.x + left
        self.content_y = self.y + top
        self.content_width = self.width - left - right
        self.content_height = self.height - top - bottom

    def set_margins(self, top: int = 0, bottom: int = 0, left: int = 0, right: int = 0):
        """Set component margins."""
        self.margin_top = top
        self.margin_bottom = bottom
        self.margin_left = left
        self.margin_right = right

    def add_child(self, child: "Component"):
        """Add a child component."""
        child.parent = self
        self.children.append(child)

    def remove_child(self, child: "Component"):
        """Remove a child component."""
        if child in self.children:
            self.children.remove(child)
            child.parent = None

    def on_event(self, event_type: str, data: Any = None):
        """Handle an event."""
        if event_type in self.event_handlers:
            self.event_handlers[event_type](data)
        elif hasattr(self, f"handle_{event_type}"):
            getattr(self, f"handle_{event_type}")(data)
        elif self.parent:
            self.parent.on_event(event_type, data)

    def add_event_handler(self, event_type: str, handler):
        """Add an event handler."""
        self.event_handlers[event_type] = handler

    def set_focus(self, focused: bool):
        """Set focus state."""
        self.focused = focused
        self.on_event("focus_changed", focused)

    def set_visible(self, visible: bool):
        """Set visibility."""
        self.visible = visible
        self.on_event("visibility_changed", visible)

    def set_enabled(self, enabled: bool):
        """Set enabled state."""
        self.enabled = enabled
        self.on_event("enabled_changed", enabled)

    def contains_point(self, x: int, y: int) -> bool:
        """Check if point is within component bounds."""
        return self.x <= x < self.x + self.width and self.y <= y < self.y + self.height

    def get_rect(self) -> Tuple[int, int, int, int]:
        """Get component rectangle (x, y, width, height)."""
        return (self.x, self.y, self.width, self.height)

    def invalidate(self):
        """Mark component as needing redraw."""
        self.on_event("invalidate", None)


class Container(Component):
    """Container component that can hold and layout other components."""

    def __init__(
        self, parent, x: int = 0, y: int = 0, width: int = 10, height: int = 3
    ):
        super().__init__(parent, x, y, width, height)
        self.layout_type = "vertical"  # vertical, horizontal, grid
        self.spacing = 1
        self.scroll_offset = 0

    def render(self):
        """Render container and all children."""
        if not self.visible:
            return

        # Clear container area
        self._clear_area()

        # Layout and render children
        self._layout_children()

        for child in self.children:
            if child.visible:
                child.render()

    def _clear_area(self):
        """Clear the container area."""
        try:
            color_pair = self.color_manager.get_color_pair("surface")
            if self.color_manager.can_use_color():
                self.stdscr.attron(curses.color_pair(color_pair))

            # Fill area with spaces
            for y in range(self.y, self.y + self.height):
                try:
                    self.stdscr.addstr(y, self.x, " " * self.width)
                except:
                    pass

            if self.color_manager.can_use_color():
                self.stdscr.attroff(curses.color_pair(color_pair))
        except:
            pass

    def _layout_children(self):
        """Layout children based on layout type."""
        if self.layout_type == "vertical":
            self._layout_vertical()
        elif self.layout_type == "horizontal":
            self._layout_horizontal()
        elif self.layout_type == "grid":
            self._layout_grid()

    def _layout_vertical(self):
        """Layout children vertically."""
        current_y = self.y + self.padding_top
        max_width = self.width - self.padding_left - self.padding_right

        for child in self.children:
            if not child.visible:
                continue

            child.set_position(self.x + self.padding_left, current_y)
            child.set_size(max_width, child.height)
            current_y += child.height + self.spacing

    def _layout_horizontal(self):
        """Layout children horizontally."""
        current_x = self.x + self.padding_left
        max_height = self.height - self.padding_top - self.padding_bottom

        for child in self.children:
            if not child.visible:
                continue

            child.set_position(current_x, self.y + self.padding_top)
            child.set_size(child.width, max_height)
            current_x += child.width + self.spacing

    def _layout_grid(self):
        """Layout children in a grid."""
        # Simple 2-column grid
        current_x = self.x + self.padding_left
        current_y = self.y + self.padding_top
        max_width = (
            self.width - self.padding_left - self.padding_right - self.spacing
        ) // 2

        for i, child in enumerate(self.children):
            if not child.visible:
                continue

            child.set_position(current_x, current_y)
            child.set_size(max_width, child.height)

            if i % 2 == 1:  # Second column, move to next row
                current_x = self.x + self.padding_left
                current_y += child.height + self.spacing
            else:
                current_x += max_width + self.spacing


class Panel(Component):
    """Panel component with borders and title."""

    def __init__(
        self,
        parent,
        x: int = 0,
        y: int = 0,
        width: int = 20,
        height: int = 10,
        title: str = "",
        border_type: str = "single",
    ):
        super().__init__(parent, x, y, width, height)
        self.title = title
        self.border_type = border_type
        self.padding = 1

    def render(self):
        """Render panel with borders and title."""
        if not self.visible:
            return

        try:
            # Choose border color based on focus state
            border_color = "border_focus" if self.focused else "border"
            border_pair = self.color_manager.get_color_pair(border_color)

            # Choose background color
            bg_color = "surface"
            bg_pair = self.color_manager.get_color_pair(bg_color)

            # Draw background
            if self.color_manager.can_use_color():
                self.stdscr.attron(curses.color_pair(bg_pair))

            # Fill panel area
            for y in range(self.y + 1, self.y + self.height - 1):
                try:
                    self.stdscr.addstr(y, self.x + 1, " " * (self.width - 2))
                except:
                    pass

            if self.color_manager.can_use_color():
                self.stdscr.attroff(curses.color_pair(bg_pair))

            # Draw borders
            if self.color_manager.can_use_color():
                self.stdscr.attron(curses.color_pair(border_pair))

            self._draw_borders()

            # Draw title
            if self.title:
                self._draw_title()

            if self.color_manager.can_use_color():
                self.stdscr.attroff(curses.color_pair(border_pair))

            # Render children
            for child in self.children:
                if child.visible:
                    child.render()

        except:
            pass

    def _draw_borders(self):
        """Draw panel borders."""
        if self.width < 2 or self.height < 2:
            return

        # Border characters
        if self.border_type == "single":
            h_line = "─"
            v_line = "│"
            corners = {"tl": "┌", "tr": "┐", "bl": "└", "br": "┘"}
        elif self.border_type == "double":
            h_line = "═"
            v_line = "║"
            corners = {"tl": "╔", "tr": "╗", "bl": "╚", "br": "╝"}
        else:  # rounded
            h_line = "─"
            v_line = "│"
            corners = {"tl": "╭", "tr": "╮", "bl": "╰", "br": "╯"}

        # Draw horizontal lines
        try:
            # Top border
            top_border = corners["tl"] + h_line * (self.width - 2) + corners["tr"]
            if len(self.title) > 0:
                # Insert title in top border
                title_space = self.width - len(self.title) - 4
                if title_space > 0:
                    title_pos = (self.width - len(self.title)) // 2
                    top_border = (
                        corners["tl"]
                        + h_line * (title_pos - 2)
                        + f" {self.title} "
                        + h_line * (self.width - title_pos - len(self.title) - 2)
                        + corners["tr"]
                    )
            self.stdscr.addstr(self.y, self.x, top_border)

            # Bottom border
            bottom_border = corners["bl"] + h_line * (self.width - 2) + corners["br"]
            self.stdscr.addstr(self.y + self.height - 1, self.x, bottom_border)

            # Vertical lines
            for y in range(self.y + 1, self.y + self.height - 1):
                self.stdscr.addch(y, self.x, v_line)
                self.stdscr.addch(y, self.x + self.width - 1, v_line)
        except:
            pass

    def _draw_title(self):
        """Draw panel title."""
        try:
            title_color = self.color_manager.get_color_pair("text")
            if self.color_manager.can_use_color():
                self.stdscr.attron(curses.color_pair(title_color))

            # Center title in top border
            title_x = self.x + (self.width - len(self.title)) // 2
            if self.title_x >= self.x and self.title_x < self.x + self.width:
                self.stdscr.addstr(self.y, title_x, self.title)

            if self.color_manager.can_use_color():
                self.stdscr.attroff(curses.color_pair(title_color))
        except:
            pass


class Label(Component):
    """Simple text label component."""

    def __init__(
        self,
        parent,
        text: str,
        x: int = 0,
        y: int = 0,
        color: str = "text",
        bold: bool = False,
    ):
        super().__init__(parent, x, y, len(text), 1)
        self.text = text
        self.color = color
        self.bold = bold

    def render(self):
        """Render the label."""
        if not self.visible:
            return

        try:
            color_pair = self.color_manager.get_color_pair(self.color)
            if self.color_manager.can_use_color():
                if self.bold:
                    self.stdscr.attron(curses.A_BOLD)
                self.stdscr.attron(curses.color_pair(color_pair))

            # Truncate text if too long
            display_text = self.text[: self.width]
            self.stdscr.addstr(self.y, self.x, display_text)

            if self.color_manager.can_use_color():
                self.stdscr.attroff(curses.color_pair(color_pair))
                if self.bold:
                    self.stdscr.attroff(curses.A_BOLD)
        except:
            pass

    def set_text(self, text: str):
        """Set label text."""
        self.text = text
        self.width = len(text)


class Button(Component):
    """Button component with click handling."""

    def __init__(
        self,
        parent,
        text: str,
        x: int = 0,
        y: int = 0,
        on_click=None,
        width: int = None,
    ):
        super().__init__(parent, x, y, width or len(text) + 4, 3)
        self.text = text
        self.on_click = on_click
        self.pressed = False

    def render(self):
        """Render the button."""
        if not self.visible or not self.enabled:
            return

        try:
            # Choose colors based on state
            if self.focused:
                bg_color = "primary"
                text_color = "text"
                border_color = "border_focus"
            elif self.pressed:
                bg_color = "accent"
                text_color = "text"
                border_color = "border_active"
            else:
                bg_color = "surface"
                text_color = "text"
                border_color = "border"

            bg_pair = self.color_manager.get_color_pair(bg_color)
            text_pair = self.color_manager.get_color_pair(text_color)
            border_pair = self.color_manager.get_color_pair(border_color)

            # Draw button background
            if self.color_manager.can_use_color():
                self.stdscr.attron(curses.color_pair(bg_pair))

            for y in range(self.y, self.y + self.height):
                try:
                    self.stdscr.addstr(y, self.x + 1, " " * (self.width - 2))
                except:
                    pass

            if self.color_manager.can_use_color():
                self.stdscr.attroff(curses.color_pair(bg_pair))

            # Draw borders
            if self.color_manager.can_use_color():
                self.stdscr.attron(curses.color_pair(border_pair))

            # Corners and horizontal lines
            button_text = f" {self.text} "
            button_text = button_text[: self.width - 2]

            top_line = f"┌{button_text}┐"
            bottom_line = f"└{'─' * (len(button_text))}┘"

            # Adjust for actual width
            if len(top_line) > self.width:
                top_line = top_line[: self.width]
                bottom_line = bottom_line[: self.width]

            try:
                self.stdscr.addstr(self.y, self.x, top_line)
                self.stdscr.addstr(self.y + self.height - 1, self.x, bottom_line)

                # Vertical lines
                for y_i in range(self.y + 1, self.y + self.height - 1):
                    self.stdscr.addch(y_i, self.x, "│")
                    self.stdscr.addch(y_i, self.x + self.width - 1, "│")
            except:
                pass

            # Draw text
            if self.color_manager.can_use_color():
                self.stdscr.attroff(curses.color_pair(border_pair))
                self.stdscr.attron(curses.color_pair(text_pair))

            text_x = self.x + (self.width - len(button_text)) // 2
            text_y = self.y + self.height // 2

            try:
                self.stdscr.addstr(text_y, text_x, button_text)
            except:
                pass

            if self.color_manager.can_use_color():
                self.stdscr.attroff(curses.color_pair(text_pair))

        except:
            pass

    def activate(self):
        """Simulate button click."""
        if self.on_click and self.enabled:
            self.on_click(self)
