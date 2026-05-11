from playwright.sync_api import sync_playwright
import time

class BrowserController:
    def __init__(self, base_url="http://127.0.0.1:5000"):
        self.base_url = base_url
        self.pw = sync_playwright().start()
        self.browser = self.pw.chromium.launch(headless=False)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        # Fix: The current library version uses the Stealth class
        from playwright_stealth import Stealth
        Stealth().apply_stealth_sync(self.page)
        # Add a timeout to goto to prevent hanging during server startup
        try:
            self.page.goto(f"{base_url}/dashboard", timeout=15000)
        except:
            print("Warning: Initial page load timed out. Continuing...")

    def navigate(self, endpoint):
        target_url = f"{self.base_url}/{endpoint.lstrip('/')}"
        self.page.goto(target_url)
        return f"Navigated to {endpoint}"

    def interact(self, selector, action="click", value=None):
        try:
            if action == "click":
                self.page.click(selector)
            elif action == "type" or action == "fill":
                self.page.fill(selector, value)
            elif action == "press":
                self.page.press(selector, value)
            return True, "Action success"
        except Exception as e:
            return False, str(e)

    def extract(self, selector, type="text"):
        try:
            if type == "text":
                return self.page.inner_text(selector)
            elif type == "count":
                return self.page.locator(selector).count()
        except Exception as e:
            return f"Error extracting: {e}"

    def close(self):
        self.browser.close()
        self.pw.stop()
