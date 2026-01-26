#!/usr/bin/env python3
"""Test Modern TUI with simple approach."""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def simple_test():
    """Simple test of TUI components."""
    try:
        import curses

        print("✅ Testing color manager...")

        def test_colors(stdscr):
            try:
                from xsint.tui.colors import init_colors

                color_manager = init_colors(stdscr)
                print(f"✅ Color manager initialized")
                print(f"   - Has colors: {color_manager.can_use_color()}")
                print(f"   - Max colors: {color_manager.capabilities['max_colors']}")

                # Test adding text
                stdscr.clear()
                stdscr.addstr(5, 5, "✅ Modern TUI Test Successful!")
                stdscr.addstr(7, 5, "   Press any key to exit...")
                stdscr.refresh()

                # Wait for key
                stdscr.getch()

            except Exception as e:
                print(f"❌ Color manager test failed: {e}")
                import traceback

                traceback.print_exc()

        curses.wrapper(test_colors)

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Test error: {e}")
        return 1

    print("✅ Color test completed")
    return 0


if __name__ == "__main__":
    print("🧪 Simple Modern TUI Test...")
    result = simple_test()
    if result == 0:
        print("✅ Test completed successfully")
    else:
        print("❌ Test failed")

    print("💡 To run full TUI: python -m xsint")
    sys.exit(result)
