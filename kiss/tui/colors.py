"""XSINT TUI Color System.

OpenCode-inspired color palette and color management for modern terminal interfaces.
"""

import curses
from typing import Dict, Tuple, Optional, Union


class ColorManager:
    """Manages colors and themes for the TUI with OpenCode-inspired design."""

    def __init__(self, stdscr):
        """Initialize color manager with terminal capability detection."""
        self.stdscr = stdscr
        self.capabilities = self._detect_capabilities()
        self.color_pairs = {}
        self.current_theme = "opencode"

        # Initialize color system
        self._initialize_colors()

    def _detect_capabilities(self) -> Dict[str, bool]:
        """Detect terminal color capabilities."""
        capabilities = {
            "has_colors": False,
            "has_256_colors": False,
            "has_true_color": False,
            "max_colors": 8,
            "max_pairs": 8,
        }

        try:
            capabilities["has_colors"] = curses.has_colors()
            if capabilities["has_colors"]:
                capabilities["max_colors"] = curses.COLORS
                capabilities["max_pairs"] = curses.COLOR_PAIRS

                # Detect 256 color support
                capabilities["has_256_colors"] = capabilities["max_colors"] >= 256

                # Detect true color support (24-bit)
                capabilities["has_true_color"] = (
                    capabilities["max_colors"] >= 256 and self._can_change_colors()
                )
        except:
            # Use safe defaults if detection fails
            pass

        return capabilities

    def _can_change_colors(self) -> bool:
        """Check if terminal can change colors (used for true color detection)."""
        try:
            return curses.can_change_color()
        except:
            return False

    def _initialize_colors(self):
        """Initialize color pairs based on terminal capabilities."""
        if not self.capabilities["has_colors"]:
            return

        try:
            curses.start_color()
            curses.use_default_colors()
        except:
            return

        # Initialize theme colors
        self._init_opencode_theme()

    def _init_opencode_theme(self):
        """Initialize OpenCode-inspired theme."""
        # OpenCode color palette (RGB -> nearest curses colors)
        self.opencode_palette = {
            # Core theme colors
            "background": (27, 30, 40),  # #1b1e28 - Dark blue-gray
            "surface": (48, 51, 64),  # #303340 - Panel backgrounds
            "primary": (173, 215, 255),  # #ADD7FF - Light blue
            "accent": (93, 228, 199),  # #5DE4c7 - Mint/turquoise
            "text": (166, 172, 205),  # #a6accd - Light gray
            "text_muted": (118, 124, 157),  # #767c9d - Darker gray
            # Semantic colors
            "success": (0, 206, 209),  # #00CED1 - Strong turquoise
            "warning": (255, 250, 194),  # #fffac2 - Bright yellow
            "error": (208, 103, 157),  # #d0679d - Hot red/pink
            "info": (93, 228, 199),  # #5DE4c7 - Bright mint
            # Border system
            "border": (76, 86, 106),  # #4C566A - Subtle borders
            "border_active": (118, 124, 157),  # #767c9d - Active borders
            "border_focus": (173, 215, 255),  # #ADD7FF - Focus borders
            # Additional UI colors
            "highlight": (93, 228, 199),  # #5DE4c7 - Selection highlight
            "hover": (173, 215, 255),  # #ADD7FF - Hover state
            "disabled": (118, 124, 157),  # #767c9d - Disabled elements
        }

        # Create color pairs for the theme
        self._create_color_pairs()

    def _create_color_pairs(self):
        """Create color pairs for the current theme."""
        pair_id = 1

        for color_name, color_def in self.opencode_palette.items():
            # Map to terminal colors
            fg_color = self._rgb_to_curses_color(color_def)
            bg_color = -1  # Default background for most pairs

            # Special cases for backgrounds
            if color_name in ["background", "surface"]:
                bg_color = fg_color
                fg_color = self._rgb_to_curses_color(self.opencode_palette["text"])

            # Create the color pair if possible
            if pair_id < self.capabilities["max_pairs"]:
                try:
                    curses.init_pair(pair_id, fg_color, bg_color)
                    self.color_pairs[color_name] = pair_id
                    pair_id += 1
                except:
                    # Use fallback pair
                    self.color_pairs[color_name] = 0

    def _rgb_to_curses_color(self, rgb: Tuple[int, int, int]) -> int:
        """Convert RGB color to nearest curses color."""
        if self.capabilities["has_true_color"]:
            # For true color terminals, we'd use extended color init
            # For now, fall back to 256 color mapping
            pass

        if self.capabilities["has_256_colors"]:
            return self._rgb_to_256_color(rgb)
        else:
            return self._rgb_to_16_color(rgb)

    def _rgb_to_256_color(self, rgb: Tuple[int, int, int]) -> int:
        """Convert RGB to 256-color palette."""
        r, g, b = rgb

        # Simple 256-color mapping (optimized for OpenCode colors)
        if r < 50 and g < 50 and b < 50:
            return 16  # Black
        elif r > 200 and g > 200 and b > 200:
            return 231  # White
        elif r > 150 and g < 100 and b < 100:
            return 196  # Red
        elif r < 100 and g > 150 and b < 100:
            return 46  # Green
        elif r < 100 and g < 100 and b > 150:
            return 21  # Blue
        elif r > 150 and g > 150 and b < 100:
            return 226  # Yellow
        elif r > 150 and g < 100 and b > 150:
            return 201  # Magenta
        elif r < 100 and g > 150 and b > 150:
            return 51  # Cyan
        else:
            # Grayscale approximation
            gray = int(0.299 * r + 0.587 * g + 0.114 * b)
            return 16 + int(gray * 24 / 255)

    def _rgb_to_16_color(self, rgb: Tuple[int, int, int]) -> int:
        """Convert RGB to 16-color palette."""
        r, g, b = rgb

        # Simple 16-color mapping
        if r > 128 and g < 64 and b < 64:
            return curses.COLOR_RED
        elif r < 64 and g > 128 and b < 64:
            return curses.COLOR_GREEN
        elif r < 64 and g < 64 and b > 128:
            return curses.COLOR_BLUE
        elif r > 128 and g > 128 and b < 64:
            return curses.COLOR_YELLOW
        elif r > 128 and g < 64 and b > 128:
            return curses.COLOR_MAGENTA
        elif r < 64 and g > 128 and b > 128:
            return curses.COLOR_CYAN
        elif r > 128 and g > 128 and b > 128:
            return curses.COLOR_WHITE
        else:
            # Calculate brightness for grayscale
            brightness = (r + g + b) / 3
            if brightness < 85:
                return curses.COLOR_BLACK
            elif brightness < 170:
                return curses.COLOR_BLUE  # Use blue for mid-tones
            else:
                return curses.COLOR_WHITE

    def get_color_pair(self, color_name: str) -> int:
        """Get color pair ID for a color name."""
        return self.color_pairs.get(color_name, 0)

    def get_color_rgb(self, color_name: str) -> Tuple[int, int, int]:
        """Get RGB values for a color name."""
        return self.opencode_palette.get(color_name, (166, 172, 205))

    def get_text_color(self, text_type: str = "normal") -> int:
        """Get appropriate text color for different text types."""
        color_map = {
            "normal": "text",
            "muted": "text_muted",
            "emphasis": "accent",
            "success": "success",
            "error": "error",
            "warning": "warning",
            "info": "info",
            "title": "primary",
            "highlight": "highlight",
        }
        return self.get_color_pair(color_map.get(text_type, "text"))

    def get_border_color(self, border_type: str = "normal") -> int:
        """Get appropriate border color."""
        border_map = {
            "normal": "border",
            "active": "border_active",
            "focus": "border_focus",
            "primary": "primary",
        }
        return self.get_color_pair(border_map.get(border_type, "border"))

    def can_use_color(self) -> bool:
        """Check if colors are available."""
        return self.capabilities["has_colors"]

    def can_use_256_colors(self) -> bool:
        """Check if 256 colors are available."""
        return self.capabilities["has_256_colors"]

    def can_use_true_color(self) -> bool:
        """Check if true color is available."""
        return self.capabilities["has_true_color"]

    def get_theme_info(self) -> Dict[str, any]:
        """Get information about current theme and capabilities."""
        return {
            "theme_name": self.current_theme,
            "has_colors": self.capabilities["has_colors"],
            "has_256_colors": self.capabilities["has_256_colors"],
            "has_true_color": self.capabilities["has_true_color"],
            "max_colors": self.capabilities["max_colors"],
            "max_pairs": self.capabilities["max_pairs"],
            "available_colors": list(self.opencode_palette.keys()),
        }


# Global color manager instance
_color_manager: Optional[ColorManager] = None


def init_colors(stdscr) -> ColorManager:
    """Initialize color system and return manager instance."""
    global _color_manager
    if _color_manager is None:
        _color_manager = ColorManager(stdscr)
    return _color_manager


def get_color_manager() -> Optional[ColorManager]:
    """Get the global color manager instance."""
    return _color_manager


def c(
    text: str, color_name: str = "text", bold: bool = False, underline: bool = False
) -> str:
    """Create colored text (for when not in curses context)."""
    # This is a utility for creating colored text strings
    # mainly used for debugging or outside-curses contexts
    manager = get_color_manager()
    if not manager or not manager.can_use_color():
        return text

    # Get RGB values for color
    rgb = manager.get_color_rgb(color_name)
    r, g, b = rgb

    # Create ANSI escape sequence
    style_codes = []
    if bold:
        style_codes.append("1")
    if underline:
        style_codes.append("4")

    style = ";" + ";".join(style_codes) if style_codes else ""
    color_seq = f"\033[{style}38;2;{r};{g};{b}m"
    reset_seq = "\033[0m"

    return f"{color_seq}{text}{reset_seq}"


# Predefined color combinations for common UI elements
UI_COLORS = {
    "header": "primary",
    "header_text": "text",
    "panel": "surface",
    "panel_border": "border",
    "panel_border_focus": "border_focus",
    "button_normal": "primary",
    "button_focus": "accent",
    "button_disabled": "disabled",
    "input_normal": "surface",
    "input_focus": "primary",
    "status_success": "success",
    "status_error": "error",
    "status_warning": "warning",
    "status_info": "info",
    "text_normal": "text",
    "text_muted": "text_muted",
    "text_highlight": "highlight",
    "progress_bg": "surface",
    "progress_fg": "accent",
    "cursor": "primary",
}
