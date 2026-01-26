#!/usr/bin/env python3
"""
Demo script to showcase enhanced phone number analysis capabilities.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "xsint"))

from xsint.engine import get_engine
from xsint.constants import ScanType


def demo_enhanced_phone_analysis():
"""Demonstrate enhanced phone analysis using phonenumbers library."""

print("🔍 KISS Enhanced Phone Number Analysis Demo")
print("=" * 60)
    print()

    # Test phone numbers with different characteristics
    test_numbers = [
        {
            "number": "+1-650-253-0000",
            "description": "Google HQ (US Business Landline)",
        },
        {
            "number": "+44-20-7946-0000",
            "description": "London Office (UK Business Landline)",
        },
        {"number": "+1-555-123-4567", "description": "US Mobile Number (Valid Format)"},
        {"number": "+1-800-555-1234", "description": "US Toll-Free Number"},
        {
            "number": "+1-555-CARRIER",
            "description": "Invalid Format (Testing Error Handling)",
        },
    ]

    engine = get_engine()

    for i, test_case in enumerate(test_numbers, 1):
        print(f"📞 Test {i}: {test_case['description']}")
        print(f"   Target: {test_case['number']}")
        print("-" * 40)

        try:
            # Progress callback for demonstration
            def progress(val):
                if val == 0.1:
                    print("   🔍 Parsing and validating...")
                elif val == 0.5:
                    print("   📡 Extracting phone intelligence...")
                elif val == 0.8:
                    print("   🔍 Checking stealer logs...")
                elif val == 1.0:
                    print("   ✅ Analysis complete!")

            result = engine.scan_phone(test_case["number"], progress)

            print(f"   Status: {result.status.value}")
            print(f"   Duration: {result.scan_duration:.2f}s")
            print(f"   Results: {len(result.info_rows)} data points")
            print()

            # Display key findings
            for row in result.info_rows[:6]:  # Show first 6 results for brevity
                threat_indicator = ""
                if row.threat_level:
                    if row.threat_level.value in ["high", "critical"]:
                        threat_indicator = "🚨"
                    elif row.threat_level.value == "medium":
                        threat_indicator = "⚠️"
                    else:
                        threat_indicator = "ℹ️"

                print(f"   {threat_indicator} {row.label}: {row.value}")

            if len(result.info_rows) > 6:
                print(f"   ... and {len(result.info_rows) - 6} more data points")

            if result.error_message:
                print(f"   ❌ Error: {result.error_message}")

        except Exception as e:
            print(f"   ❌ Scan failed: {e}")

        print("\n" + "=" * 60 + "\n")

    print("🎯 Enhanced Phone Intelligence Features:")
    print("   • Carrier Information (when available)")
    print("   • Line Type Detection (Mobile, Landline, VoIP, Toll-Free)")
    print("   • Geographic Location (Country, Region/City)")
    print("   • Timezone Information")
    print("   • Multiple Format Display (International, National, E.164)")
    print("   • Country Code Detection")
    print("   • Stealer Malware Check (Hudson Rock)")
    print("   • Threat Level Assessment")
    print("   • Real-time Progress Tracking")
    print("\n✨ Using only phonenumbers Python library - no external APIs!")


if __name__ == "__main__":
    demo_enhanced_phone_analysis()
