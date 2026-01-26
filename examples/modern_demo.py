#!/usr/bin/env python3
"""Working Modern TUI Demo.

Bypasses Python 3.14 curses issues and provides working demonstration.
"""

import sys
import os
import time
import curses

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class WorkingModernTUI:
    """Working modern TUI demonstration with OpenCode design."""

    def __init__(self):
        """Initialize the working TUI."""
        self.running = True
        self.input_buffer = ""
        self.log_messages = []
        self.stdscr = None

        # OpenCode color palette
        self.colors = {
            "background": 236,
            "surface": 240,
            "primary": 39,
            "accent": 51,
            "text": 251,
            "text_muted": 245,
            "success": 46,
            "error": 196,
            "warning": 226,
            "border": 241,
        }

        # Add welcome messages
        self.add_log("🚀 XSINT Intelligence Platform v2.0", "primary")
        self.add_log("✨ Modern TUI with OpenCode-inspired design", "accent")
        self.add_log("🎨 Clean interface with professional appearance", "text")
        self.add_log("", "text")
        self.add_log("🔍 OpenCode Design System:", "primary")
        self.add_log(
            "   • Dark theme optimized for low-light environments", "text_muted"
        )
        self.add_log("   • High contrast for excellent readability", "text_muted")
        self.add_log("   • Professional color palette", "text_muted")
        self.add_log("   • Clean visual hierarchy", "text_muted")
        self.add_log("   • Responsive layout system", "text_muted")
        self.add_log("", "text")
        self.add_log("💡 Interactive Features:", "success")
        self.add_log("   • Real-time scan progress tracking", "text_muted")
        self.add_log("   • Contextual status indicators", "text_muted")
        self.add_log("   • Keyboard navigation with visual feedback", "text_muted")
        self.add_log("   • Component-based architecture", "text_muted")
        self.add_log("", "text")
        self.add_log("🎯 Ready for OSINT operations!", "accent")
        self.add_log("", "text")

    def _safe_color_init(self):
        """Safe color initialization."""
        try:
            if curses.has_colors():
                curses.start_color()
                curses.use_default_colors()

                # Initialize color pairs
                for i, (name, fg) in enumerate(
                    list(self.colors.items())[:10]
                ):  # Limit pairs
                    if i + 1 < curses.COLOR_PAIRS:
                        try:
                            curses.init_pair(i + 1, fg, -1)
                            self.colors[name] = i + 1
                        except:
                            pass
        except:
            pass

    def _get_color_pair(self, color_name: str) -> int:
        """Get color pair safely."""
        return self.colors.get(color_name, 0)

    def add_log(self, message: str, color: str = "text"):
        """Add a log message."""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.log_messages.append((log_entry, color))

        # Keep only last 30 messages
        if len(self.log_messages) > 30:
            self.log_messages = self.log_messages[-30:]

    def _draw_frame(self):
        """Draw the main frame and content."""
        if not self.stdscr:
            return

        h, w = self.stdscr.getmaxyx()

        try:
            self.stdscr.clear()

            # Draw background
            bg_pair = self._get_color_pair("background")
            if curses.has_colors():
                self.stdscr.attron(curses.color_pair(bg_pair))

            # Fill background
            for y in range(h):
                for x in range(w):
                    try:
                        self.stdscr.addch(y, x, " ")
                    except:
                        pass

            if curses.has_colors():
                self.stdscr.attroff(curses.color_pair(bg_pair))

            # Draw title area
            self._draw_title(w)

            # Draw content area
            self._draw_content(h, w)

            # Draw input area
            self._draw_input(h, w)

            # Draw status bar
            self._draw_status(h, w)

            self.stdscr.refresh()

        except Exception:
            pass

    def _draw_title(self, w):
        """Draw title bar."""
        title = "🔍 XSINT INTELLIGENCE"
        title_pair = self._get_color_pair("primary")

        try:
            if curses.has_colors():
                self.stdscr.attron(curses.A_BOLD | curses.color_pair(title_pair))

            title_x = max(0, (w - len(title)) // 2)
            self.stdscr.addstr(0, title_x, title)

            if curses.has_colors():
                self.stdscr.attroff(curses.A_BOLD | curses.color_pair(title_pair))

            # Draw separator
            border_pair = self._get_color_pair("border")
            if curses.has_colors():
                self.stdscr.attron(curses.color_pair(border_pair))

            separator = "─" * w
            self.stdscr.addstr(1, 0, separator)

            if curses.has_colors():
                self.stdscr.attroff(curses.color_pair(border_pair))

        except:
            pass

    def _draw_content(self, h, w):
        """Draw content area with logs."""
        content_height = h - 6  # Title + input + status + margin
        content_width = w - 6  # Margins

        start_idx = max(0, len(self.log_messages) - content_height)

        for i in range(
            start_idx, min(len(self.log_messages), start_idx + content_height)
        ):
            if i - start_idx >= content_height:
                break

            y = 2 + (i - start_idx)
            message, color = self.log_messages[i]

            # Truncate long messages
            display_msg = message
            if len(message) > content_width - 2:
                display_msg = message[: content_width - 5] + "..."

            # Draw message
            color_pair = self._get_color_pair(color)
            try:
                if curses.has_colors():
                    self.stdscr.attron(curses.color_pair(color_pair))
                self.stdscr.addstr(y, 3, display_msg.ljust(content_width))
                if curses.has_colors():
                    self.stdscr.attroff(curses.color_pair(color_pair))
            except:
                pass

    def _draw_input(self, h, w):
        """Draw input area."""
        input_y = h - 3

        # Input box borders
        border_pair = self._get_color_pair("border")
        input_bg_pair = self._get_color_pair("surface")

        try:
            # Draw input background
            if curses.has_colors():
                self.stdscr.attron(curses.color_pair(input_bg_pair))

            for y in range(input_y, h - 2):
                for x in range(3, w - 3):
                    try:
                        self.stdscr.addch(y, x, " ")
                    except:
                        pass

            if curses.has_colors():
                self.stdscr.attroff(curses.color_pair(input_bg_pair))

            # Draw borders
            if curses.has_colors():
                self.stdscr.attron(curses.color_pair(border_pair))

            # Top and bottom borders
            for x in range(3, w - 3):
                try:
                    self.stdscr.addch(input_y - 1, x, "─")
                    self.stdscr.addch(input_y + 1, x, "─")
                except:
                    pass

            # Side borders
            for y in range(input_y, h - 2):
                try:
                    self.stdscr.addch(y, 2, "│")
                    self.stdscr.addch(y, w - 3, "│")
                except:
                    pass

            if curses.has_colors():
                self.stdscr.attroff(curses.color_pair(border_pair))

            # Draw input text
            text_pair = self._get_color_pair("text")
            if curses.has_colors():
                self.stdscr.attron(curses.color_pair(text_pair))

            input_text = (
                self.input_buffer if self.input_buffer else "Enter target to scan..."
            )
            display_input = f"> {input_text}"

            self.stdscr.addstr(input_y, 4, display_input.ljust(w - 7))

            if curses.has_colors():
                self.stdscr.attroff(curses.color_pair(text_pair))

        except:
            pass

    def _draw_status(self, h, w):
        """Draw status bar."""
        status_y = h - 1

        # Status background
        status_bg_pair = self._get_color_pair("surface")
        border_pair = self._get_color_pair("border")

        try:
            # Draw background
            if curses.has_colors():
                self.stdscr.attron(curses.color_pair(status_bg_pair))

            for x in range(w):
                try:
                    self.stdscr.addch(status_y - 1, x, " ")
                except:
                    pass

            if curses.has_colors():
                self.stdscr.attroff(curses.color_pair(status_bg_pair))

            # Draw separator
            if curses.has_colors():
                self.stdscr.attron(curses.color_pair(border_pair))

            separator = "─" * w
            self.stdscr.addstr(status_y - 2, 0, separator)

            if curses.has_colors():
                self.stdscr.attroff(curses.color_pair(border_pair))

            # Draw status text
            status_pair = self._get_color_pair("accent")
            if curses.has_colors():
                self.stdscr.attron(curses.color_pair(status_pair))

            status_text = "🎯 Ready | Enter target to scan | Ctrl+C: Exit"
            if len(self.input_buffer) > 0:
                status_text = f"🔍 Scanning: {self.input_buffer}"

            self.stdscr.addstr(status_y, 2, status_text.ljust(w - 4))

            if curses.has_colors():
                self.stdscr.attroff(curses.color_pair(status_pair))

        except:
            pass

    def handle_input(self, key):
        """Handle keyboard input."""
        if key in (27, 3):  # Escape or Ctrl+C
            self.running = False
            return

        if key in (curses.KEY_BACKSPACE, 127, 8):
            self.input_buffer = self.input_buffer[:-1]
        elif key == 10:  # Enter
            if self.input_buffer.strip():
                self.add_log(f"🔍 Scanning: {self.input_buffer.strip()}", "accent")
                self._simulate_scan(self.input_buffer.strip())
                self.input_buffer = ""
        elif 32 <= key <= 126:  # Printable characters
            if len(self.input_buffer) < 50:
                self.input_buffer += chr(key)

    def _simulate_scan(self, target: str):
        """Simulate scan with proper feedback."""
        import threading

        def scan_worker():
            time.sleep(0.5)  # Initial delay

            # Different scan types based on input
            if "." in target and target.count(".") >= 3:
                self.add_log("📧 Detected: IP Address", "success")
                for i in range(10):
                    time.sleep(0.2)
                    self.add_log(
                        f"   Querying geolocation service {i + 1}/10...", "text"
                    )
                self.add_log("✅ IP geolocation completed", "success")
            elif "@" in target:
                self.add_log("📧 Detected: Email Address", "success")
                for i in range(8):
                    time.sleep(0.2)
                    self.add_log(f"   Checking breach databases {i + 1}/8...", "text")
                self.add_log("✅ Email breach analysis completed", "success")
            elif any(c.isdigit() for c in target):
                self.add_log("📧 Detected: Phone Number", "success")
                for i in range(6):
                    time.sleep(0.2)
                    self.add_log(f"   Validating format {i + 1}/6...", "text")
                self.add_log("✅ Phone validation completed", "success")
            else:
                self.add_log("👤 Detected: Domain/Username", "success")
                for i in range(5):
                    time.sleep(0.2)
                    self.add_log(f"   Checking social platforms {i + 1}/5...", "text")
                self.add_log("✅ Domain/Username enumeration completed", "success")

            self.add_log(f"🎉 Scan completed for: {target}", "accent")

        # Run in background thread
        thread = threading.Thread(target=scan_worker, daemon=True)
        thread.start()

    def run(self):
        """Run the TUI without curses.wrapper (bypass Python 3.14 issues)."""
        try:
            # Manual curses setup
            self.stdscr = curses.initscr()
            if not self.stdscr:
                print("❌ Failed to initialize curses")
                return

            curses.noecho()
            curses.cbreak()
            self.stdscr.keypad(True)

            # Initialize colors
            self._safe_color_init()

            # Show cursor
            curses.curs_set(1)

            # Main loop
            while self.running:
                self._draw_frame()
                key = self.stdscr.getch()
                if key != -1:
                    self.handle_input(key)
                time.sleep(0.05)

        except KeyboardInterrupt:
            self.running = False
        finally:
            # Cleanup
            if self.stdscr:
                curses.nocbreak()
                curses.echo()
                curses.endwin()


def main():
    """Main function with proper error handling."""
    try:
        print("🚀 Starting XSINT Modern TUI Demo...")
        print("✨ Bypassing Python 3.14 curses issues...")

        tui = WorkingModernTUI()
        tui.run()

        print("👋 Demo completed successfully")

    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
