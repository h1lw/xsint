#!/usr/bin/env python3
"""Test the new Modern TUI."""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_modern_tui():
    """Test the modern TUI implementation."""
    try:
        import curses

        print("✅ Testing import...")
        from xsint.tui import ModernTUI

        print("✅ ModernTUI imported successfully")

        def run_modern(stdscr):
            try:
                print("✅ Creating ModernTUI instance...")
                tui = ModernTUI(stdscr)
                print("✅ Starting TUI loop...")
                tui.loop()
            except Exception as e:
                print(f"Error in modern TUI: {e}")
                import traceback

                traceback.print_exc()

        # Run the modern TUI
        print("✅ Starting curses wrapper...")
        curses.wrapper(run_modern)
        print("✅ Curses wrapper completed")

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Modern TUI error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    print("🧪 Testing Modern XSINT TUI...")
    result = test_modern_tui()
    if result == 0:
        print("✅ Modern TUI test completed")
    else:
        print("❌ Modern TUI test failed")

    print("💡 To run the normal TUI: python -m xsint")
    sys.exit(result)
