"""KISS - Keep It Simple, Stupid

Main entry point for KISS application with enhanced TUI support.
"""

import sys
import curses
from pathlib import Path

from kiss.utils.logging import get_logger
from kiss.config import get_config
from kiss.engine import get_engine

logger = get_logger(__name__)


def run_curses_tui():
    """Run enhanced curses TUI with robust error handling."""
    try:
        # Initialize curses with proper error handling
        curses.wrapper(lambda stdscr: run_curses_app(stdscr))
    except KeyboardInterrupt:
        print("\nKISS interrupted by user. Goodbye!")
        return 0
    except Exception as e:
        logger.error(f"TUI Error: {e}")
        print(f"Failed to start enhanced TUI: {e}")
        print("Falling back to simple mode...")
        return run_simple_tui()


def run_curses_app(stdscr):
    """Initialize and run curses application."""
    try:
        from kiss.tui import ModernTUI

        # Create modern TUI
        tui = ModernTUI(stdscr)

        # Get the real OSINT engine
        engine = get_engine()

        # Set the engine
        tui.set_engine(engine)

        # Show welcome message
        tui.log_callback("KISS - Keep It Simple, Stupid v2.0", "primary")
        tui.log_callback("Real OSINT Engine loaded with live API integration", "accent")
        tui.log_callback("", "text")
        tui.log_callback("Available Scan Types:", "primary")
        tui.log_callback(
            "   - IP Address: Geolocation, Organization, Stealer Malware", "text_muted"
        )
        tui.log_callback(
            "   - Email: Breach Detection, Gravatar, Stealer Logs", "text_muted"
        )
        tui.log_callback("   - Phone: Format Analysis, Stealer Check", "text_muted")
        tui.log_callback("   - Username: Platform Enumeration", "text_muted")
        tui.log_callback("   - Address: Geocoding via Nominatim", "text_muted")
        tui.log_callback("", "text")

        # Show configured services
        config = get_config()
        services = config.list_enabled_services()
        tui.log_callback(f"Enabled Services: {len(services)}", "info")
        tui.log_callback(
            f"   {', '.join(services[:5])}{'...' if len(services) > 5 else ''}",
            "text_muted",
        )
        tui.log_callback("", "text")

        tui.log_callback(
            "Enter a target (IP, email, phone, username, or address) to scan", "accent"
        )
        tui.log_callback("Type 'exit' or press Ctrl+C to quit", "text")
        tui.log_callback("", "text")

        # Start main loop
        tui.loop()

    except Exception as e:
        logger.exception(f"Error in curses application: {e}")
        raise


def run_simple_tui():
    """Run a simple TUI fallback without curses."""
    from kiss.scanner.detectors import detect_input_type

    print("=" * 60)
    print("  KISS - Keep It Simple, Stupid v2.0")
    print("  Simple Mode (no curses)")
    print("=" * 60)
    print()
    print("Supported Scan Types:")
    print("  - IP Address     : Geolocation, ISP, Stealer Malware Check")
    print("  - Email Address  : Breach Detection, Gravatar, Stealer Logs")
    print("  - Phone Number   : Enhanced Analysis with phonenumbers, Stealer Check")
    print("  - Username       : Platform Enumeration")
    print("  - Physical Addr  : Geocoding via OpenStreetMap")
    print()

    # Get engine
    engine = get_engine()

    while True:
        try:
            target = input("\nEnter target (or 'exit' to quit): ").strip()

            if not target:
                continue

            if target.lower() in ["exit", "quit", "q"]:
                print("\nGoodbye!")
                break

            # Detect input type
            scan_type = detect_input_type(target)
            if not scan_type:
                print(f"Could not detect input type for: {target}")
                print("Try: IP, email, phone number, domain, @username, or address")
                continue

            print(f"\nDetected: {scan_type}")
            print(f"Scanning: {target}")
            print("-" * 40)

            # Run appropriate scan
            def progress(val):
                pass  # Simple mode doesn't show progress

            if scan_type == "IP":
                result = engine.scan_ip(target, progress)
            elif scan_type == "EMAIL":
                result = engine.scan_email(target, progress)
            elif scan_type == "PHONE":
                result = engine.scan_phone(target, progress)
            elif scan_type == "USERNAME":
                result = engine.scan_username(target, progress)
            elif scan_type == "ADDRESS":
                result = engine.scan_address(target, progress)
            elif scan_type == "HASH":
                result = engine.scan_hash(target, progress)
            else:
                print(f"Unsupported scan type: {scan_type}")
                continue

            # Display results
            print(f"\nStatus: {result.status.value}")
            print(f"Duration: {result.scan_duration:.2f}s")
            print()

            if result.info_rows:
                print("Results:")
                for row in result.info_rows:
                    threat_marker = ""
                    if row.threat_level:
                        if row.threat_level.value in ["high", "critical"]:
                            threat_marker = " [!]"
                    print(f"  {row.label}: {row.value}{threat_marker}")
                    if row.source:
                        print(f"    (Source: {row.source})")
            else:
                print("No results found.")

            if result.error_message:
                print(f"\nError: {result.error_message}")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

    return 0


def check_dependencies():
    """Check if required dependencies are available."""
    missing_deps = []

    try:
        import curses
    except ImportError:
        missing_deps.append("curses")

    try:
        import requests
    except ImportError:
        missing_deps.append("requests")

    if missing_deps:
        print(f"Missing dependencies: {', '.join(missing_deps)}")
        print("Install with: pip install -r requirements.txt")
        return False

    return True


def main():
    """Main entry point with mode selection."""
    # Check dependencies
    if not check_dependencies():
        return 1

    # Try to determine best mode to run
    try:
        # Check if we're in a terminal that supports curses
        if sys.stdout.isatty():
            return run_curses_tui()
        else:
            print("Not a terminal, using simple mode")
            return run_simple_tui()
    except Exception as e:
        logger.error(f"Startup error: {e}")
        print("Failed to determine display mode, using simple mode")
        return run_simple_tui()


if __name__ == "__main__":
    sys.exit(main())
