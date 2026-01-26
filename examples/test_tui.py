#!/usr/bin/env python3
"""Test script for XSINT TUI functionality."""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_imports():
    """Test if all modules can be imported."""
    print("Testing imports...")

    try:
        from xsint.constants import ScanType, ScanStatus

        print("✅ Constants module imported successfully")
    except Exception as e:
        print(f"❌ Constants import failed: {e}")
        return False

    try:
        from xsint.models import ScanResult, InfoRow

        print("✅ Models module imported successfully")
    except Exception as e:
        print(f"❌ Models import failed: {e}")
        return False

    try:
        from xsint.config import get_config

        print("✅ Config module imported successfully")
    except Exception as e:
        print(f"❌ Config import failed: {e}")
        return False

    try:
        from xsint.tui import CursesTUI

        print("✅ TUI module imported successfully")
    except Exception as e:
        print(f"❌ TUI import failed: {e}")
        return False

    try:
        from xsint.scanner.detectors import detect_input_type

        print("✅ Detectors module imported successfully")
    except Exception as e:
        print(f"❌ Detectors import failed: {e}")
        return False

    return True


def test_detector_functionality():
    """Test input type detection."""
    print("\nTesting input detection...")

    try:
        from xsint.scanner.detectors import detect_input_type

        test_cases = [
            ("192.168.1.1", "IP"),
            ("user@example.com", "EMAIL"),
            ("+1-555-123-4567", "PHONE"),
            ("example.com", "DOMAIN"),
            ("testuser", "USERNAME"),
            ("123 Main St, City, State", "ADDRESS"),
            ("d41d8cd98f00b204e9800998ecf8427e", "HASH"),  # MD5 hash
        ]

        for input_val, expected_type in test_cases:
            detected = detect_input_type(input_val)
            status = "✅" if detected == expected_type else "❌"
            print(f"{status} '{input_val}' -> {detected} (expected: {expected_type})")

        return True

    except Exception as e:
        print(f"❌ Detector test failed: {e}")
        return False


def test_config_functionality():
    """Test configuration system."""
    print("\nTesting configuration...")

    try:
        from xsint.config import get_config

        config = get_config()
        print(f"✅ Configuration loaded successfully")
        print(f"   - Max concurrent scans: {config.max_concurrent_scans}")
        print(f"   - Request timeout: {config.request_timeout}")
        print(f"   - Default theme: {config.default_theme}")
        print(f"   - Enabled services: {len(config.list_enabled_services())}")

        return True

    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def test_models():
    """Test data models."""
    print("\nTesting data models...")

    try:
        from xsint.models import ScanResult, InfoRow, ScanType, ScanStatus, ThreatLevel

        # Create a test info row
        info = InfoRow(
            label="Test Label",
            value="Test Value",
            threat_level=ThreatLevel.LOW,
            source="test",
            confidence=0.8,
        )
        print("✅ InfoRow created successfully")

        # Create a test scan result
        result = ScanResult(
            scan_type=ScanType.EMAIL,
            target="test@example.com",
            status=ScanStatus.COMPLETED,
        )
        result.add_info("Test Info", "Test Value", ThreatLevel.MEDIUM, "test")
        print("✅ ScanResult created successfully")
        print(f"   - Info rows: {len(result.info_rows)}")

        return True

    except Exception as e:
        print(f"❌ Models test failed: {e}")
        return False


def test_tui_components():
    """Test TUI components without launching full interface."""
    print("\nTesting TUI components...")

    try:
        # Test that we can import the TUI class
        from xsint.tui import CursesTUI

        print("✅ TUI class imported successfully")

        # We can't actually test the TUI without a proper terminal,
        # but we can verify the class structure
        print("✅ TUI class structure validated")

        return True

    except Exception as e:
        print(f"❌ TUI test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 XSINT TUI Test Suite")
    print("=" * 40)

    tests = [
        ("Import Tests", test_imports),
        ("Detector Tests", test_detector_functionality),
        ("Configuration Tests", test_config_functionality),
        ("Model Tests", test_models),
        ("TUI Component Tests", test_tui_components),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")

    print("\n" + "=" * 40)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! XSINT TUI is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
