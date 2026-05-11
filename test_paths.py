import sys
import os

print("--- sys.path ---")
for p in sys.path:
    print(p)

print("\n--- Testing Imports ---")
try:
    import playwright_stealth
    print("SUCCESS: playwright_stealth imported.")
except ImportError as e:
    print(f"FAILURE: {e}")

try:
    import automation.browser_controller
    print("SUCCESS: automation.browser_controller imported.")
except ImportError as e:
    print(f"FAILURE: {e}")
