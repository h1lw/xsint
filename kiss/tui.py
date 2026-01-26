"""XSINT Curses TUI - Enhanced Terminal User Interface.

Robust curses-based TUI with proper error handling and terminal compatibility.
Extracted and enhanced from xsint-test.py with fixes for terminal state management.
"""

import sys
import time
import queue
import threading
import curses
from typing import Optional, Dict, List, Tuple, Any


class CursesTUI:
    """Enhanced Curses TUI with robust error handling and terminal compatibility."""

    def __init__(self, stdscr):
        """Initialize TUI with proper error handling and capability detection."""
        self.stdscr = stdscr
        self.log_buffer = []
        self.scroll_pos = 0
        self.input_buffer = ""
        self.scan_queue = queue.Queue()
        self.is_scanning = False
        self.scan_progress = 0.0
        self.sparkles = []

        # State management
        self.minimized = False
        self.active_menu = None
        self.settings = {"animations": True, "logging": False, "theme": "Ocean"}
        self.editing_api_key = None
        self.edit_buffer = ""

        # Terminal capabilities
        self.capabilities = self._detect_capabilities()

        # Themes
        self.themes = {
            "Pastel": [231, 225, 219, 213, 159, 123, 117, 120, 157, 229, 223, 224, 217],
            "Matrix": [
                46,
                47,
                48,
                49,
                50,
                51,
                82,
                83,
                84,
                85,
                86,
                87,
                118,
                119,
                120,
                121,
            ],
            "Ocean": [27, 33, 39, 45, 51, 81, 87, 123, 159, 195],
            "Fire": [196, 202, 208, 214, 220, 226, 227, 228, 229],
        }
        self.theme_names = list(self.themes.keys())

        # Initialize terminal features safely
        self._initialize_terminal_features()

        # ASCII Banner
        self.ascii_banner = [
            "█        ▀                               ",
            " █   ▄  ▄▄▄     ▄▄▄▄    ▄▄▄▄      ",
            "█ ▄▀     █    █   ▀  █   ▀▀▄ ▄ ▀▀▄▄  ▀  ▀",
            "█  ▀▄  ▄▄▄█▄▄▄  ▀▀▄▄▀  ▄▄▄▄▀  ▄▄▄▄▀  ▄▄▄▄▀",
            "█  ▀   ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄",
            "          modern OSINT toolkit              ",
        ]

        self.banner_frame = 0

        # Initialize scanner engine (will be set later)
        self.engine = None

    def _detect_capabilities(self) -> Dict[str, Any]:
        """Detect terminal capabilities for progressive enhancement."""
        capabilities = {
            "has_colors": False,
            "color_count": 0,
            "has_mouse": False,
            "has_unicode": True,  # Assume modern terminals
            "supports_resize": False,
            "min_width": 80,
            "min_height": 24,
        }

        try:
            # Check color capabilities
            if hasattr(curses, "COLORS"):
                capabilities["color_count"] = curses.COLORS
                capabilities["has_colors"] = curses.COLORS > 0

            # Check mouse support
            if hasattr(curses, "mousemask"):
                capabilities["has_mouse"] = True

            # Check terminal size
            try:
                h, w = self.stdscr.getmaxyx()
                capabilities["min_width"] = w
                capabilities["min_height"] = h
            except:
                pass  # Use defaults

        except Exception:
            # Use safe defaults if detection fails
            pass

        return capabilities

    def _initialize_terminal_features(self):
        """Initialize terminal features with proper error handling."""
        try:
            # Initialize colors safely
            if self.capabilities["has_colors"]:
                try:
                    curses.start_color()
                    curses.use_default_colors()
                    self._initialize_color_pairs()
                except curses.error:
                    # Fall back to monochrome mode
                    self.capabilities["has_colors"] = False

            # Initialize mouse support safely
            if self.capabilities["has_mouse"]:
                try:
                    curses.mousemask(
                        curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION
                    )
                except curses.error:
                    # Try basic mouse support
                    try:
                        curses.mousemask(curses.ALL_MOUSE_EVENTS)
                    except curses.error:
                        self.capabilities["has_mouse"] = False

        except Exception as e:
            # Ensure we continue even if terminal features fail
            print(f"Warning: Some terminal features not available: {e}")

    def _initialize_color_pairs(self):
        """Initialize color pairs with capability checks."""
        if not self.capabilities["has_colors"]:
            return

        # Base UI Colors with fallback
        base_colors = [
            (1, curses.COLOR_WHITE, -1),
            (2, curses.COLOR_GREEN, -1),
            (3, curses.COLOR_RED, -1),
            (4, curses.COLOR_CYAN, -1),
            (5, curses.COLOR_YELLOW, -1),
            (6, curses.COLOR_BLACK, curses.COLOR_WHITE),  # Status Bar
            (7, curses.COLOR_WHITE, curses.COLOR_BLUE),  # Window Bar
        ]

        for pair_id, fg, bg in base_colors:
            try:
                curses.init_pair(pair_id, fg, bg)
            except curses.error:
                # Skip if color pair cannot be initialized
                continue

        self.color_map = {"white": 1, "green": 2, "red": 3, "cyan": 4, "yellow": 5}

        # Apply theme
        self.apply_theme()

    def apply_theme(self):
        """Apply color theme with capability checks."""
        if not self.capabilities["has_colors"]:
            return

        try:
            spectrum = self.themes[self.settings["theme"]]
            self.spectrum_len = len(spectrum)

            # Gradient Pairs (20+)
            for i, color_idx in enumerate(spectrum):
                if self.capabilities["color_count"] > 8 and 20 + i < curses.COLOR_PAIRS:
                    try:
                        curses.init_pair(20 + i, color_idx, -1)
                    except curses.error:
                        break
                elif 20 + i < curses.COLOR_PAIRS:
                    try:
                        curses.init_pair(20 + i, (i % 7) + 1, -1)
                    except curses.error:
                        break

            # Main UI Theme Color (Pair 1 & 8)
            if self.capabilities["color_count"] > 8:
                main_color = spectrum[len(spectrum) // 2]
                try:
                    curses.init_pair(1, main_color, -1)
                    curses.init_pair(8, main_color, -1)
                except curses.error:
                    pass
            else:
                try:
                    curses.init_pair(1, curses.COLOR_CYAN, -1)
                    curses.init_pair(8, curses.COLOR_CYAN, -1)
                except curses.error:
                    pass

        except Exception:
            # Use default colors if theme application fails
            pass

    def log_callback(self, text, color="white"):
        """Safe logging callback."""
        if self.capabilities["has_colors"]:
            cp = self.color_map.get(color, 1)
        else:
            cp = 1

        for line in text.split("\n"):
            self.scan_queue.put((line, cp))

    def update_progress(self, val):
        """Update scan progress."""
        self.scan_progress = max(0.0, min(1.0, val))

    def set_engine(self, engine):
        """Set the scanner engine."""
        self.engine = engine

    def run_scan(self, target, t_type):
        """Execute scan with proper error handling."""
        if not self.engine:
            self.log_callback("Error: Scanner engine not initialized", "red")
            return

        self.is_scanning = True
        self.scan_progress = 0.0

        try:
            if t_type == "IP":
                self.engine.scan_ip(target, self.update_progress)
            elif t_type == "EMAIL":
                self.engine.scan_email(target, self.update_progress)
            elif t_type == "PHONE":
                self.engine.scan_phone(target, self.update_progress)
            elif t_type == "DOMAIN":
                self.engine.scan_domain(target, self.update_progress)
            elif t_type == "USERNAME":
                self.engine.scan_username(target, self.update_progress)
            elif t_type == "ADDRESS":
                self.engine.scan_address(target, self.update_progress)
            else:
                self.log_callback(f"Unknown scan type: {t_type}", "red")

            self.log_callback(f"✅ Scan completed: {target}", "green")

        except Exception as e:
            self.log_callback(f"❌ Scan failed: {str(e)}", "red")
        finally:
            self.is_scanning = False
            self.scan_progress = 0.0

    def _safe_getch(self) -> int:
        """Safely get character input."""
        try:
            return self.stdscr.getch()
        except curses.error:
            return -1

    def _safe_getmaxyx(self) -> Tuple[int, int]:
        """Safely get terminal size."""
        try:
            return self.stdscr.getmaxyx()
        except curses.error:
            return 24, 80  # Safe default

    def loop(self):
        """Main TUI loop with robust error handling."""
        try:
            # Initialize terminal settings safely
            try:
                self.stdscr.nodelay(True)
                self.stdscr.keypad(True)
                curses.curs_set(1)
            except curses.error:
                # Use minimal terminal settings
                self.stdscr.nodelay(False)
                self.stdscr.keypad(False)
                curses.curs_set(0)

            # Set window title after curses initialization
            try:
                sys.stdout.write("\x1b]2;modern OSINT toolkit\x07")
                sys.stdout.flush()
            except:
                pass  # Ignore if window title fails

            while True:
                # Process scan queue
                while not self.scan_queue.empty():
                    self.scan_queue.get(self.log_buffer.append)
                    self.scroll_pos = max(0, len(self.log_buffer) - 10)

                # Draw UI
                self.draw()

                # Handle input
                key = self._safe_getch()

                # Handle mouse events
                if key == curses.KEY_MOUSE and self.capabilities["has_mouse"]:
                    try:
                        _, x, y, _, _ = curses.getmouse()
                        self.handle_mouse(x, y)
                    except curses.error:
                        pass

                # Handle keyboard input
                if key != -1 and not self.minimized:
                    self.handle_input(key)

                # Small delay to prevent CPU spinning
                time.sleep(0.01)

        except KeyboardInterrupt:
            return
        except Exception as e:
            self.log_callback(f"Fatal error: {e}", "red")
            time.sleep(2)
        finally:
            # Ensure terminal is restored to clean state
            try:
                self.stdscr.nodelay(False)
                self.stdscr.keypad(False)
                curses.curs_set(1)
            except:
                pass

    def handle_input(self, key):
        """Handle keyboard input with proper validation."""
        if self.editing_api_key:
            self.handle_api_key_edit(key)
        elif not self.active_menu:
            self.handle_main_input(key)

    def handle_main_input(self, key):
        """Handle main input mode."""
        if key == 10:  # Enter
            t = self.input_buffer.strip()
            self.input_buffer = ""
            if t:
                if t.lower() in ["exit", "quit"]:
                    sys.exit(0)
                if self.engine:
                    t_type = self.engine.detect_input_type(t)
                    if t_type:
                        threading.Thread(
                            target=self.run_scan, args=(t, t_type), daemon=True
                        ).start()
                    else:
                        self.log_callback("[!] Unknown format", "red")

        elif key in (curses.KEY_BACKSPACE, 127, 8):
            self.input_buffer = self.input_buffer[:-1]

        elif key == curses.KEY_PPAGE:
            self.scroll_pos = max(0, self.scroll_pos - 10)

        elif key == curses.KEY_NPAGE:
            self.scroll_pos = min(len(self.log_buffer) - 10, self.scroll_pos + 10)

        elif 32 <= key <= 126:  # Printable characters
            self.input_buffer += chr(key)

    def handle_api_key_edit(self, key):
        """Handle API key editing."""
        if key == 10:  # Enter
            if self.edit_buffer and self.editing_api_key:
                # Store API key (implementation depends on API_KEYS access)
                pass
            self.editing_api_key = None
            self.edit_buffer = ""
        elif key == 27:  # Escape
            self.editing_api_key = None
            self.edit_buffer = ""
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            self.edit_buffer = self.edit_buffer[:-1]
        elif 32 <= key <= 126:
            self.edit_buffer += chr(key)

    def handle_mouse(self, x, y):
        """Handle mouse events."""
        # Basic mouse handling - can be extended
        pass

    def draw(self):
        """Main drawing method."""
        try:
            h, w = self._safe_getmaxyx()
            self.stdscr.clear()

            if self.minimized:
                self.draw_minimized(w, h)
            else:
                self.draw_full(w, h)

            self.stdscr.refresh()
        except curses.error:
            # Skip drawing if terminal state is invalid
            pass

    def draw_minimized(self, w, h):
        """Draw minimized window."""
        try:
            title = "XSINT [Press Space to Restore]"
            self.stdscr.addstr(0, max(0, (w - len(title)) // 2), title)
        except curses.error:
            pass

    def draw_full(self, w, h):
        """Draw full interface."""
        # Header
        self.draw_header(w)

        # Content area
        content_height = h - 6
        if content_height > 0:
            self.draw_content(w, content_height)

        # Input line
        self.draw_input_line(w, h)

        # Status bar
        self.draw_status_bar(w, h)

    def draw_header(self, w):
        """Draw header with banner."""
        try:
            if self.capabilities["has_colors"]:
                self.stdscr.attron(curses.color_pair(1))

            # Draw animated banner if enabled
            if self.settings.get("animations", True) and w >= 60:
                self.draw_animated_banner(w)
            else:
                # Static banner
                banner_text = "XSINT INTELLIGENCE"
                self.stdscr.addstr(0, max(0, (w - len(banner_text)) // 2), banner_text)

            if self.capabilities["has_colors"]:
                self.stdscr.attroff(curses.color_pair(1))

        except curses.error:
            pass

    def draw_animated_banner(self, w):
        """Draw animated ASCII banner."""
        try:
            # Simple animation by shifting colors
            for i, line in enumerate(self.ascii_banner):
                if i >= 6:  # Safety check
                    break

                if w >= len(line):
                    offset = (self.banner_frame + i) % 10
                    if (
                        self.capabilities["has_colors"]
                        and 20 + offset < curses.COLOR_PAIRS
                    ):
                        self.stdscr.attron(curses.color_pair(20 + offset))

                    self.stdscr.addstr(i + 1, max(0, (w - len(line)) // 2), line)

                    if (
                        self.capabilities["has_colors"]
                        and 20 + offset < curses.COLOR_PAIRS
                    ):
                        self.stdscr.attroff(curses.color_pair(20 + offset))

            self.banner_frame = (self.banner_frame + 1) % 10

        except curses.error:
            pass

    def draw_content(self, w, h):
        """Draw main content area."""
        try:
            # Draw log buffer
            start_line = 2
            max_lines = min(h - 4, len(self.log_buffer) - self.scroll_pos)

            for i in range(max_lines):
                idx = self.scroll_pos + i
                if idx < len(self.log_buffer):
                    line, color_pair = self.log_buffer[idx]

                    if self.capabilities["has_colors"]:
                        self.stdscr.attron(curses.color_pair(color_pair))

                    # Truncate line if too long
                    display_line = line[: w - 3] if len(line) > w - 3 else line
                    self.stdscr.addstr(start_line + i, 2, display_line)

                    if self.capabilities["has_colors"]:
                        self.stdscr.attroff(curses.color_pair(color_pair))

            # Draw progress bar if scanning
            if self.is_scanning and h > 6:
                self.draw_progress_bar(w, h)

        except curses.error:
            pass

    def draw_progress_bar(self, w, h):
        """Draw scan progress bar."""
        try:
            progress_y = h - 4
            progress_width = w - 10
            filled = int(progress_width * self.scan_progress)

            # Progress bar border
            progress_bar = "[" + "=" * filled + " " * (progress_width - filled) + "]"
            self.stdscr.addstr(progress_y, 5, progress_bar)

            # Progress percentage
            percent_text = f"{int(self.scan_progress * 100)}%"
            self.stdscr.addstr(progress_y + 1, w - len(percent_text) - 5, percent_text)

        except curses.error:
            pass

    def draw_input_line(self, w, h):
        """Draw input line."""
        try:
            input_y = h - 2
            if self.editing_api_key:
                prompt = f"API Key [{self.editing_api_key}]: "
                text = self.edit_buffer
            else:
                prompt = "> "
                text = self.input_buffer

            # Draw prompt
            if self.capabilities["has_colors"]:
                self.stdscr.attron(curses.color_pair(4))  # Cyan
            self.stdscr.addstr(input_y, 1, prompt)
            if self.capabilities["has_colors"]:
                self.stdscr.attroff(curses.color_pair(4))

            # Draw input text (truncated if needed)
            max_input_len = w - len(prompt) - 2
            display_text = text[-max_input_len:] if len(text) > max_input_len else text
            self.stdscr.addstr(input_y, len(prompt) + 1, display_text)

        except curses.error:
            pass

    def draw_status_bar(self, w, h):
        """Draw status bar."""
        try:
            status_y = h - 1
            status_parts = []

            if self.is_scanning:
                status_parts.append("SCANNING")

            if self.capabilities["has_colors"]:
                status_parts.append(f"Colors:{self.capabilities['color_count']}")

            if self.capabilities["has_mouse"]:
                status_parts.append("Mouse:ON")

            status_parts.append(f"Theme:{self.settings.get('theme', 'Default')}")

            status_text = " | ".join(status_parts)
            status_text = status_text[: w - 1]  # Truncate if too long

            if self.capabilities["has_colors"]:
                self.stdscr.attron(curses.color_pair(6))  # Status bar color
            self.stdscr.addstr(status_y, 0, status_text.ljust(w))
            if self.capabilities["has_colors"]:
                self.stdscr.attroff(curses.color_pair(6))

        except curses.error:
            pass
