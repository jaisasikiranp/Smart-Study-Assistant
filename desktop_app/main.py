import sys
import os
import threading
import time
from queue import Queue

# --- IMPORTANT PATH FIX ---
# Ensure the root directory is in sys.path so modules like 'automation' are found
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread, pyqtSignal, QObject

# Now import our modules from the root
try:
    from automation.browser_controller import BrowserController
    from automation.planner_actions import PlannerActions
    from database.db_manager import LogDatabase
    from assistant.speech import SpeechAssistant
    from assistant.command_parser import StudyCommandParser
    from tracking.logger import AssistantLogger
except ImportError as e:
    print(f"IMPORT ERROR: {e}. Check if __init__.py exists in subdirectories.")
    sys.exit(1)

class AutomationWorker(QObject):
    finished = pyqtSignal(str, str, str) # intent, result_msg, status
    status_msg = pyqtSignal(str)
    
    def __init__(self, parser, logger):
        super().__init__()
        self.parser = parser
        self.logger = logger
        self.browser = None
        self.planner = None
        self.queue = Queue()
        self.running = True

    def run(self):
        print("AutomationWorker: Thread started.")
        self.status_msg.emit("Connecting to Browser...")
        try:
            # Playwright ONLY works in the same thread it was started in
            self.browser = BrowserController()
            self.planner = PlannerActions(self.browser)
            self.status_msg.emit("System Ready")
            print("AutomationWorker: Browser controller initialized successfully.")
        except Exception as e:
            print(f"CRITICAL ERROR in AutomationWorker: {e}")
            self.status_msg.emit(f"Initialization Failed: {e}")
            return

        while self.running:
            if not self.queue.empty():
                text, intent, payload, start_time = self.queue.get()
                print(f"AutomationWorker: Processing command: {intent}")
                self.status_msg.emit(f"Running {intent}...")
                try:
                    result_msg = ""
                    if intent == "navigate":
                        result_msg = self.planner.controller.navigate(payload["page"])
                    elif intent == "add_task":
                        result_msg = self.planner.add_task(payload["title"])
                    elif intent == "show_tasks":
                        result_msg = self.planner.show_tasks()
                    elif intent == "show_schedule":
                        result_msg = self.planner.show_schedule()
                    elif intent == "show_deadlines":
                        result_msg = self.planner.show_deadlines()
                    elif intent == "complete_task":
                        result_msg = self.planner.complete_task(payload["title"])
                    elif intent == "add_note":
                        result_msg = self.planner.add_note(payload["title"])
                    
                    self.logger.record_action(text, intent, "success", time.time() - start_time)
                    self.finished.emit(intent, result_msg, "success")
                except Exception as e:
                    err_msg = f"Action failed: {str(e)}"
                    print(f"AutomationWorker: {err_msg}")
                    self.logger.record_action(text, intent, "failure", time.time() - start_time, str(e))
                    self.finished.emit(intent, err_msg, "failure")
                finally:
                    self.status_msg.emit("System Ready")
            time.sleep(0.1)

    def add_command(self, text, intent, payload, start_time):
        self.queue.put((text, intent, payload, start_time))

class SmartAssistantController:
    def __init__(self, ui_instance):
        self.ui = ui_instance
        self.db = LogDatabase()
        self.logger = AssistantLogger(self.db)
        self.parser = StudyCommandParser()
        self.speech = SpeechAssistant()
        
        # Background Worker Thread for Playwright (Thread-bound)
        self.worker_thread = QThread()
        self.worker = AutomationWorker(self.parser, self.logger)
        self.worker.moveToThread(self.worker_thread)
        
        # Connect Worker Signals
        self.worker.finished.connect(self.on_command_finished)
        self.worker.status_msg.connect(self.ui.signals.status_updated.emit)
        self.worker_thread.started.connect(self.worker.run)
        self.worker_thread.start()

    def process_command(self, text):
        start_time = time.time()
        intent, payload = self.parser.parse(text)
        
        if intent == "invalid":
            response = payload.get("msg", "I only support planner tasks.")
            self.ui.signals.message_received.emit(response, "bot")
            threading.Thread(target=self.speech.speak, args=(response,), daemon=True).start()
            return

        if intent == "unknown":
            response = "I'm not sure how to do that. Try 'add task'."
            self.ui.signals.message_received.emit(response, "bot")
            threading.Thread(target=self.speech.speak, args=(response,), daemon=True).start()
            return

        # Hand off to background worker
        self.ui.signals.status_updated.emit(f"Processing {intent}...")
        self.worker.add_command(text, intent, payload, start_time)

    def on_command_finished(self, intent, result_msg, status):
        self.ui.signals.message_received.emit(result_msg, "bot")
        threading.Thread(target=self.speech.speak, args=(result_msg,), daemon=True).start()
        
        # Insights
        if status == "success" and intent in ["add_task", "complete_task"]:
            insight = self.logger.generate_smart_insight()
            if insight:
                self.ui.signals.message_received.emit(f"💡 Suggestion: {insight}", "bot")
        
        self.ui.signals.status_updated.emit("System Ready")

    def handle_voice(self):
        def voice_thread():
            self.ui.signals.status_updated.emit("🎙️ Listening... (speak now)")
            self.ui.signals.mic_active.emit(True)
            text = self.speech.listen()
            self.ui.signals.mic_active.emit(False)
            if text:
                self.ui.signals.voice_text_ready.emit(text)
                self.ui.signals.message_received.emit(text, "user")
                self.process_command(text)
            else:
                self.ui.signals.status_updated.emit("System Ready (No voice heard)")
        
        threading.Thread(target=voice_thread, daemon=True).start()

if __name__ == "__main__":
    print("Desktop AI Assistant starting up...")
    qt_app = QApplication(sys.argv)
    
    # Import UI locally to avoid circular dependencies
    from desktop_app.ui import DesktopAssistantUI
    ui = DesktopAssistantUI(None, None)
    
    # Initialize controller
    controller = SmartAssistantController(ui)
    
    # Connect UI callbacks
    ui.on_input = controller.process_command
    ui.on_voice = controller.handle_voice
    
    print("UI Instance created. Showing window...")
    ui.show()
    print("Entering Qt event loop...")
    sys.exit(qt_app.exec())
