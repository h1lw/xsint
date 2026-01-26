"""Header Component for XSINT TUI.

Modern header with logo, status indicators, and quick actions.
"""

from typing import List, Optional
from .base import Container, Label, Button
from ..colors import get_color_manager


class Header(Container):
    """Modern header component with OpenCode-inspired design."""

    def __init__(self, parent, width: int = 80):
        super().__init__(parent, 0, 0, width, 3)
        self.layout_type = "horizontal"
        self.spacing = 2

        # Header sections
        self.logo_section = None
        self.status_section = None
        self.actions_section = None

        # Initialize header components
        self._create_components()

    def _create_components(self):
        """Create header sub-components."""
        color_manager = get_color_manager()

        # Logo section (left) - using simple text for component header
        self.logo_section = Label(
            self, "modern OSINT", x=2, y=0, color="primary", bold=True
        )

        # Status section (center)
        self.status_section = Container(self, x=0, y=0, width=self.width // 2, height=3)
        self.status_section.layout_type = "horizontal"

        # Create status indicators
        self.status_labels = {
            "ready": Label(self.status_section, "● READY", color="success"),
            "scanning": Label(self.status_section, "● SCANNING", color="warning"),
            "error": Label(self.status_section, "● ERROR", color="error"),
            "api": Label(self.status_section, "● API: OK", color="info"),
        }

        # Add visible status indicators
        self.status_section.add_child(self.status_labels["ready"])
        self.status_section.add_child(self.status_labels["api"])

        # Actions section (right)
        self.actions_section = Container(self, x=0, y=0, width=20, height=3)
        self.actions_section.layout_type = "horizontal"

        # Quick action buttons
        self.scan_button = Button(
            self.actions_section,
            "Scan",
            x=0,
            y=0,
            width=8,
            on_click=self._handle_scan_click,
        )

        self.help_button = Button(
            self.actions_section,
            "Help",
            x=0,
            y=0,
            width=8,
            on_click=self._handle_help_click,
        )

        self.actions_section.add_child(self.scan_button)
        self.actions_section.add_child(self.help_button)

        # Add main sections to container
        self.add_child(self.logo_section)
        self.add_child(self.status_section)
        self.add_child(self.actions_section)

    def set_status(self, status: str, message: str = ""):
        """Set header status."""
        # Hide all status labels first
        for label in self.status_labels.values():
            label.set_visible(False)

        # Show relevant status
        if status in self.status_labels:
            self.status_labels[status].set_visible(True)
            if message:
                self.status_labels[status].set_text(f"● {message.upper()}")

    def set_api_status(self, connected: bool):
        """Set API connection status."""
        api_label = self.status_labels["api"]
        if connected:
            api_label.set_text("● API: OK")
            api_label.color = "success"
        else:
            api_label.set_text("● API: OFFLINE")
            api_label.color = "error"

    def _handle_scan_click(self, button):
        """Handle scan button click."""
        # Notify parent to start new scan
        self.on_event("start_scan", None)

    def _handle_help_click(self, button):
        """Handle help button click."""
        # Show help dialog
        self.on_event("show_help", None)

    def render(self):
        """Render the header with OpenCode-inspired design."""
        if not self.visible:
            return

        try:
            color_manager = get_color_manager()

            # Draw header background
            if color_manager.can_use_color():
                bg_pair = color_manager.get_color_pair("surface")
                self.stdscr.attron(curses.color_pair(bg_pair))

            # Fill header background
            for y in range(self.y, self.y + self.height):
                try:
                    self.stdscr.addstr(y, self.x, " " * self.width)
                except:
                    pass

            if color_manager.can_use_color():
                self.stdscr.attroff(curses.color_pair(bg_pair))

            # Draw separator line at bottom
            if color_manager.can_use_color():
                border_pair = color_manager.get_color_pair("border")
                self.stdscr.attron(curses.color_pair(border_pair))

            try:
                separator = "─" * self.width
                self.stdscr.addstr(self.y + self.height - 1, self.x, separator)
            except:
                pass

            if color_manager.can_use_color():
                self.stdscr.attroff(curses.color_pair(border_pair))

            # Layout components manually for better control
            self._layout_header_components()

            # Render components
            for child in self.children:
                if child.visible:
                    child.render()

        except:
            pass

    def _layout_header_components(self):
        """Layout header components with proper spacing."""
        # Logo on the left
        logo_x = self.x + 2
        self.logo_section.set_position(logo_x, self.y + 1)

        # Status in the center
        status_width = 30
        status_x = self.x + (self.width - status_width) // 2
        self.status_section.set_position(status_x, self.y + 1)
        self.status_section.set_size(status_width, 3)

        # Actions on the right
        actions_width = 20
        actions_x = self.x + self.width - actions_width - 2
        self.actions_section.set_position(actions_x, self.y + 1)
        self.actions_section.set_size(actions_width, 3)


class StatusBar(Container):
    """Modern status bar with progress indicators and system info."""

    def __init__(self, parent, y: int = 0, width: int = 80):
        super().__init__(parent, 0, y, width, 3)
        self.layout_type = "horizontal"
        self.spacing = 1

        # Status bar sections
        self.progress_section = None
        self.info_section = None
        self.shortcuts_section = None

        # State
        self.progress = 0.0
        self.status_message = "Ready"
        self.scanning = False

        # Initialize components
        self._create_components()

    def _create_components(self):
        """Create status bar components."""
        color_manager = get_color_manager()

        # Progress section (left)
        self.progress_section = Container(self, x=0, y=0, width=30, height=3)

        self.progress_label = Label(
            self.progress_section, "Ready", x=1, y=1, color="text"
        )

        self.progress_section.add_child(self.progress_label)

        # Info section (center)
        self.info_section = Container(self, x=0, y=0, width=30, height=3)

        self.info_label = Label(
            self.info_section, "Ready", x=1, y=1, color="text_muted"
        )

        self.info_section.add_child(self.info_label)

        # Shortcuts section (right)
        self.shortcuts_section = Container(self, x=0, y=0, width=25, height=3)

        self.shortcuts_label = Label(
            self.shortcuts_section,
            "[Ctrl+C] Exit | [Tab] Focus",
            x=1,
            y=1,
            color="text_muted",
        )

        self.shortcuts_section.add_child(self.shortcuts_label)

        # Add sections to status bar
        self.add_child(self.progress_section)
        self.add_child(self.info_section)
        self.add_child(self.shortcuts_section)

    def set_progress(self, progress: float, message: str = ""):
        """Set progress and status message."""
        self.progress = max(0.0, min(1.0, progress))
        self.scanning = progress > 0.0 and progress < 1.0

        # Update progress label
        if self.scanning:
            progress_text = f"Scanning... {int(self.progress * 100)}%"
            self.progress_label.set_text(progress_text)
            self.progress_label.color = "warning"
        elif self.progress >= 1.0:
            self.progress_label.set_text("Complete")
            self.progress_label.color = "success"
        else:
            self.progress_label.set_text("Ready")
            self.progress_label.color = "text"

        # Update info message
        if message:
            self.info_label.set_text(message)

    def set_status_message(self, message: str, color: str = "text"):
        """Set status message."""
        self.status_message = message
        self.info_label.set_text(message)
        self.info_label.color = color

    def set_shortcuts(self, shortcuts: str):
        """Set shortcuts display."""
        self.shortcuts_label.set_text(shortcuts)

    def render(self):
        """Render status bar with OpenCode design."""
        if not self.visible:
            return

        try:
            color_manager = get_color_manager()

            # Draw status bar background
            if color_manager.can_use_color():
                bg_pair = color_manager.get_color_pair("surface")
                self.stdscr.attron(curses.color_pair(bg_pair))

            # Fill background
            for y in range(self.y, self.y + self.height):
                try:
                    self.stdscr.addstr(y, self.x, " " * self.width)
                except:
                    pass

            if color_manager.can_use_color():
                self.stdscr.attroff(curses.color_pair(bg_pair))

            # Draw separator line at top
            if color_manager.can_use_color():
                border_pair = color_manager.get_color_pair("border")
                self.stdscr.attron(curses.color_pair(border_pair))

            try:
                separator = "─" * self.width
                self.stdscr.addstr(self.y, self.x, separator)
            except:
                pass

            if color_manager.can_use_color():
                self.stdscr.attroff(curses.color_pair(border_pair))

            # Layout and render sections
            self._layout_status_bar()

            # Render progress bar if scanning
            if self.scanning:
                self._render_progress_bar()

            # Render components
            for child in self.children:
                if child.visible:
                    child.render()

        except:
            pass

    def _layout_status_bar(self):
        """Layout status bar sections."""
        # Progress section (left side)
        progress_x = self.x + 2
        self.progress_section.set_position(progress_x, self.y + 1)
        self.progress_section.set_size(25, 3)

        # Info section (center)
        info_width = 30
        info_x = self.x + (self.width - info_width) // 2
        self.info_section.set_position(info_x, self.y + 1)
        self.info_section.set_size(info_width, 3)

        # Shortcuts section (right)
        shortcuts_width = 25
        shortcuts_x = self.x + self.width - shortcuts_width - 2
        self.shortcuts_section.set_position(shortcuts_x, self.y + 1)
        self.shortcuts_section.set_size(shortcuts_width, 3)

    def _render_progress_bar(self):
        """Render progress bar."""
        if self.progress <= 0.0:
            return

        try:
            color_manager = get_color_manager()

            # Progress bar dimensions
            bar_width = 20
            bar_x = self.x + self.width - bar_width - 25
            bar_y = self.y + 1

            # Calculate filled width
            filled_width = int(bar_width * self.progress)

            # Draw progress bar background
            if color_manager.can_use_color():
                bg_pair = color_manager.get_color_pair("border")
                self.stdscr.attron(curses.color_pair(bg_pair))

            # Background characters
            for x in range(bar_x, bar_x + bar_width):
                try:
                    self.stdscr.addch(bar_y, x, "░")
                except:
                    pass

            # Draw filled portion
            if color_manager.can_use_color():
                self.stdscr.attroff(curses.color_pair(bg_pair))
                fg_pair = color_manager.get_color_pair("accent")
                self.stdscr.attron(curses.color_pair(fg_pair))

            for x in range(bar_x, bar_x + filled_width):
                try:
                    self.stdscr.addch(bar_y, x, "█")
                except:
                    pass

            if color_manager.can_use_color():
                self.stdscr.attroff(curses.color_pair(fg_pair))

        except:
            pass
