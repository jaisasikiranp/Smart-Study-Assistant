import tkinter as tk
from tkinter import scrolledtext
import webbrowser
import speech_recognition as sr
import threading
import time
import io
import re
import requests
import numpy as np
import sounddevice as sd
import soundfile as sf
from database.db_manager import LogDatabase
from tracking.logger import AssistantLogger
from tracking.dataset_logger import InteractionDatasetLogger
from assistant.speech import SpeechProcessor
from assistant.command_parser import IntentMapper
import queue
import os
import uuid

SAMPLE_RATE = 16000
BASE_URL = "http://127.0.0.1:5000"

# Logic moved to assistant.command_parser.IntentMapper and assistant.speech.SpeechProcessor


# ── Main Desktop Tool ─────────────────────────────────────────────────────────
class ScholasticDesktopSiri:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.is_listening = False
        self._flow = None             # Stores multi-step state: {intent, step, data}
        self.session = requests.Session()
        self.session.headers.update({'X-Assistant-Token': 'SMART-STUDY-2026'})
 
        # Root window
        self.root = tk.Tk()
        
        # Performance Tracking
        self.db_logger = LogDatabase()
        self.logger = AssistantLogger(self.db_logger)
        self.dataset_logger = InteractionDatasetLogger()
        
        self.root.title("Smart Study Assistant")
        self.root.geometry("380x560+1060+160")
        self.root.resizable(False, False)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#0f172a")
        self._minimized = False
        
        # TTS Worker Thread
        self.tts_queue = queue.Queue()
        threading.Thread(target=self._tts_worker, daemon=True).start()
 
        self._build_ui()

        # Initial Setup (Greeting then Calibration)
        self.ambient_threshold = 350
        threading.Thread(target=self._initial_setup, daemon=True).start()

        self.root.mainloop()

    def _initial_setup(self):
        self._greet()
        self._calibrate()
        threading.Thread(target=self.autonomous_loop, daemon=True).start()

    def _calibrate(self):
        """One-time calibration to avoid per-command delays."""
        self.root.after(0, self._set_status, "⚖️ Calibrating Mic...", "#94a3b8")
        time.sleep(1.0) # wait for greeting audio to subside
        cal = sd.rec(int(SAMPLE_RATE * 1.0), samplerate=SAMPLE_RATE, channels=1, dtype='int16')
        sd.wait()
        avg_energy = np.abs(cal).mean()
        self.ambient_threshold = max(avg_energy * 2.8, 400)
        print(f"[Mic] Calibrated. Threshold: {self.ambient_threshold:.2f}")
        self.root.after(0, self._set_status, "● Ready", "#22c55e")

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Title bar
        bar = tk.Frame(self.root, bg="#1e293b", height=42)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        self._bar_ref = bar
        tk.Label(bar, text="🎓 Smart Study Assistant", bg="#1e293b", fg="white",
                 font=("Arial", 11, "bold")).pack(side="left", padx=10)
        tk.Button(bar, text="✕", bg="#1e293b", fg="#94a3b8",
                  font=("Arial", 13, "bold"), bd=0,
                  activebackground="#ef4444", activeforeground="white",
                  command=self.root.destroy).pack(side="right", padx=4)
        tk.Button(bar, text="─", bg="#1e293b", fg="#94a3b8",
                  font=("Arial", 13, "bold"), bd=0,
                  activebackground="#334155", activeforeground="white",
                  command=self._minimize).pack(side="right", padx=4)
        bar.bind("<Button-1>", self._start_move)
        bar.bind("<B1-Motion>", self._do_move)

        # Status
        self.status_var = tk.StringVar(value="● Ready")
        self.status_lbl = tk.Label(self.root, textvariable=self.status_var,
                                   bg="#0f172a", fg="#22c55e", font=("Arial", 9))
        self.status_lbl.pack(anchor="w", padx=12, pady=(5, 0))

        # Chat box
        self.chat_box = scrolledtext.ScrolledText(
            self.root, bg="#0f172a", fg="#f8fafc",
            font=("Arial", 10), wrap=tk.WORD,
            state="disabled", bd=0, relief="flat",
            height=20, width=44)
        self.chat_box.pack(padx=10, pady=5, fill="both", expand=True)
        self.chat_box.tag_config("user", foreground="#60a5fa", justify="right")
        self.chat_box.tag_config("bot",  foreground="#a3e635", justify="left")
        self.chat_box.tag_config("sys",  foreground="#94a3b8", justify="left")

        # Input row
        row = tk.Frame(self.root, bg="#1e293b", pady=4)
        row.pack(fill="x", padx=10, pady=(0, 8))

        self.input_var = tk.StringVar()
        self.entry = tk.Entry(row, textvariable=self.input_var,
                              bg="#1e293b", fg="white", insertbackground="white",
                              font=("Arial", 11), bd=0, relief="flat")
        self.entry.pack(side="left", fill="x", expand=True, padx=(8, 4), ipady=8)
        self.entry.bind("<Return>", lambda e: self._handle_text_send())

        self.mic_btn = tk.Button(row, text="🎙️", bg="#3b82f6", fg="white",
                                 font=("Arial", 14), bd=0, relief="flat",
                                 width=3, cursor="hand2",
                                 command=self._handle_mic_click)
        self.mic_btn.pack(side="right", padx=(0, 4))

        tk.Button(row, text="➤", bg="#3b82f6", fg="white",
                  font=("Arial", 12, "bold"), bd=0, relief="flat",
                  width=3, cursor="hand2",
                  command=self._handle_text_send).pack(side="right", padx=(0, 4))

    # ── Minimize / Restore ────────────────────────────────────────────────────
    def _minimize(self):
        self._minimized = True
        self._restore_x = self.root.winfo_x()
        self._restore_y = self.root.winfo_y()
        # Shrink to just the title bar (42px tall)
        self.root.geometry(f"380x42+{self._restore_x}+{self._restore_y}")
        # Bind double-click on title bar to restore
        self._bar_ref.bind("<Double-Button-1>", lambda e: self._restore())

    def _restore(self):
        self._minimized = False
        self.root.geometry(f"380x560+{self._restore_x}+{self._restore_y}")
        self._bar_ref.unbind("<Double-Button-1>")

    # ── Backend API calls ─────────────────────────────────────────────────────────
    def api_get(self, path):
        try:
            r = self.session.get(f"{BASE_URL}{path}", timeout=5)
            if r.ok:
                return r.json()
        except Exception:
            pass
        return None

    def api_post_form(self, path, data):
        try:
            r = self.session.post(f"{BASE_URL}{path}", data=data, timeout=5,
                             allow_redirects=True)
            return r.ok
        except Exception:
            return False

    # ── Drag ──────────────────────────────────────────────────────────────────
    def _start_move(self, e):
        self._dx, self._dy = e.x, e.y

    def _do_move(self, e):
        x = self.root.winfo_x() + e.x - self._dx
        y = self.root.winfo_y() + e.y - self._dy
        if self._minimized:
            self._restore_x, self._restore_y = x, y
        self.root.geometry(f"+{x}+{y}")

    # ── Chat helpers ──────────────────────────────────────────────────────────
    def _chat(self, text, tag="sys"):
        self.chat_box.configure(state="normal")
        prefix = "You: " if tag == "user" else ("🤖 " if tag == "bot" else "")
        self.chat_box.insert("end", f"{prefix}{text}\n\n", tag)
        self.chat_box.configure(state="disabled")
        self.chat_box.see("end")

    def _set_status(self, text, color="#22c55e"):
        self.status_var.set(text)
        self.status_lbl.configure(fg=color)

    # ── TTS ───────────────────────────────────────────────────────────────────
    def _tts_worker(self):
        """Dedicated thread to handle speech synthesis using native Windows SAPI."""
        import win32com.client
        import pythoncom
        
        # Initialize COM for this thread
        pythoncom.CoInitialize()
        
        try:
            speaker = win32com.client.Dispatch("SAPI.SpVoice")
            print("[TTS] SAPI Voice Engine initialized.")
        except Exception as e:
            print(f"[TTS] SAPI Initialization error: {e}")
            return
        
        while True:
            text, auto_listen = self.tts_queue.get()
            if text:
                print(f"[TTS] Speaking (SAPI): {text[:40]}...")
                try:
                    # Speak synchronously in this worker thread
                    speaker.Speak(text)
                    print("[TTS] Finished speaking.")
                    if auto_listen:
                        time.sleep(0.4)
                        self.root.after(0, self._handle_mic_click)
                except Exception as e:
                    print(f"[TTS] SAPI Speech error: {e}")
            self.tts_queue.task_done()

    def _say(self, text, auto_listen=False):
        """Display in chat and queue for speech."""
        self.root.after(0, self._chat, text, "bot")
        self.tts_queue.put((text, auto_listen))

    def speak(self, text):
        """Directly queue text for speech without chat box log."""
        self.tts_queue.put((text, False))

    # ── Greeting ──────────────────────────────────────────────────────────────
    def _greet(self):
        time.sleep(0.8)
        msg = ("Smart Study Assistant ready! I can add tasks, complete tasks, add notes, "
               "list your tasks, open any page, and more. "
               "Say 'Alexa' or click the mic to start.")
        self.root.after(0, self._chat, msg, "sys")
        self.speak(msg)

    # ── Input handlers ────────────────────────────────────────────────────────
    def _handle_text_send(self):
        text = self.input_var.get().strip()
        if not text:
            return
        self.input_var.set("")
        self.root.after(0, self._chat, text, "user")
        threading.Thread(target=self._process_text_input, args=(text,), daemon=True).start()

    def _process_text_input(self, text):
        """Process text input and log to dataset."""
        if self._flow:
            self._execute_flow_step(text, audio_path="text_input")
            return
            
        intent, payload = IntentMapper.parse_intent(text)
        action_desc = self._execute(intent, payload, text)
        
        status = "success" if intent != "unknown" and not str(action_desc).startswith("Error:") else "failure"
        
        self.dataset_logger.log_interaction(
            spoken_input="text_input",
            recognized_text=text,
            mapped_intent=intent,
            action_taken=action_desc,
            retry_count=0,
            status=status
        )

    def _handle_mic_click(self):
        if not self.is_listening:
            threading.Thread(target=self._listen_once, daemon=True).start()

    def _listen_once(self):
        self.is_listening = True
        self.root.after(0, self._set_status, "🎙️ Listening...", "#f59e0b")
        self.root.after(0, lambda: self.mic_btn.configure(bg="#ef4444"))
        
        max_retries = 2
        retry_count = 0
        audio_path = None
        recognized_text = ""
        test_id = str(uuid.uuid4())[:8]

        try:
            while retry_count <= max_retries:
                # Generate unique path for this audio snippet
                inter_id = str(uuid.uuid4())[:8]
                audio_filename = f"inter_{inter_id}_try{retry_count}.wav"
                audio_path = os.path.join("uploads", "audio", audio_filename)
                
                audio = SpeechProcessor.record_audio(max_duration=10, silence_sec=1.5, 
                                    ambient_threshold=self.ambient_threshold,
                                    save_path=audio_path)
                
                if audio is None:
                    if retry_count < max_retries:
                        self.dataset_logger.log_intermediate_failure("", "No audio detected", retry_count, test_id=test_id, spoken_input="none")
                        retry_count += 1
                        self._say(f"I didn't hear anything. Try again (Attempt {retry_count+1})...", auto_listen=True)
                        continue
                    else:
                        self._say("I didn't hear anything. Interaction timed out.")
                        self.dataset_logger.log_interaction(
                            test_id=test_id,
                            spoken_input="None", recognized_text="", mapped_intent="none",
                            action_taken="none", retry_count=retry_count, status="failure",
                            failure_stage="speech_recognition"
                        )
                        return

                try:
                    recognized_text, confidence = SpeechProcessor.recognize(audio, self.recognizer)
                    if not recognized_text:
                        raise sr.UnknownValueError()
                    
                    print(f"Heard (Confidence {confidence:.2f}): {recognized_text}")
                    self.root.after(0, self._chat, recognized_text, "user")
                    
                    # Process and log
                    self._process_and_log(recognized_text, audio_path, retry_count, confidence, test_id=test_id)
                    break

                except sr.UnknownValueError:
                    if retry_count < max_retries:
                        self.dataset_logger.log_intermediate_failure("", "UnknownValue", retry_count, test_id=test_id, spoken_input=audio_path)
                        retry_count += 1
                        self._say("I didn't catch that. Could you repeat?", auto_listen=True)
                    else:
                        self._say("I'm having trouble understanding. Let's try again later.")
                        self.dataset_logger.log_interaction(
                            test_id=test_id,
                            spoken_input=audio_path, recognized_text="", mapped_intent="unknown",
                            action_taken="none", retry_count=retry_count, status="failure",
                            failure_stage="speech_recognition"
                        )
                except sr.RequestError:
                    self._say("Speech service unavailable.")
                    break
        except Exception as e:
            self._say(f"Mic error: {e}")
        finally:
            self.is_listening = False
            self.root.after(0, self._set_status, "● Ready", "#22c55e")
            self.root.after(0, lambda: self.mic_btn.configure(bg="#3b82f6"))

    def _process_and_log(self, text, audio_path, retry_count, confidence=None, test_id="none"):
        """Helper to process intent and log to structured dataset."""
        if self._flow:
            self._execute_flow_step(text, audio_path=audio_path, retry_count=retry_count, test_id=test_id)
            return

        intent, payload = IntentMapper.parse_intent(text)
        
        # We'll pass the info to _execute which will now return action description
        action_desc = self._execute(intent, payload, text)
        
        status = "success" if intent != "unknown" and not str(action_desc).startswith("Error:") else "failure"
        if intent == "cancel": status = "success"

        failure_stage = "none"
        if status == "failure":
            if intent == "unknown": failure_stage = "intent_mapping"
            else: failure_stage = "action_execution"

        self.dataset_logger.log_interaction(
            test_id=test_id,
            spoken_input=audio_path,
            recognized_text=text,
            mapped_intent=intent,
            action_taken=action_desc,
            retry_count=retry_count,
            status=status,
            failure_stage=failure_stage,
            final_output=action_desc,
            expected_output="unknown",
            root_cause_category="unknown"
        )

    # ── Wake-word loop ────────────────────────────────────────────────────────
    def autonomous_loop(self):
        """Continuous background loop looking for the wake word."""
        # Expanded phonetic variants for 'Alexa' and 'Smart Study' (including mishearings and accents)
        wake_patterns = [
            "alexa", "hey alexa", "hi alexa", "uh-lexa", "a-lexa", "alexaah",
            "alaxa", "aleksa", "alexo", "alessa", "alisha", "alexa sir", "a lexa",
            "lexa", "hey lexa", "alex", "electra", "a lexer",
            "smart study", "hey study", "study assistant", "hey assistant",
            "scholar", "scholastic", "smart assistant"
        ]
        
        while True:
            if self.is_listening:
                time.sleep(0.5)
                continue
            try:
                # Use slightly more aggressive VAD for wake words to be responsive
                audio = SpeechProcessor.record_audio(max_duration=4, silence_sec=0.7, ambient_threshold=self.ambient_threshold)
                if audio is None:
                    continue
                
                text, conf = SpeechProcessor.recognize(audio, self.recognizer)
                if not text:
                    continue
                text = text.lower()
                
                # Check for wake pattern
                matched_wake = next((wp for wp in wake_patterns if wp in text), None)
                
                if matched_wake:
                    print(f"[Wake] Found pattern '{matched_wake}' in: '{text}'")
                    # Clear status
                    self.root.after(0, self._set_status, "🎙️ Listening...", "#f59e0b")
                    self.root.after(0, self._chat, f"Wake word detected ('{matched_wake}')", "sys")
                    
                    # Logic for "One-Shot" commands
                    parts = text.split(matched_wake, 1)
                    remaining = parts[1].strip() if len(parts) > 1 else ""
                    
                    if len(remaining) > 3: # Likely a command
                        self.speak("Processing...")
                        # Run in thread and log
                        threading.Thread(target=self._process_and_log, 
                                         args=(remaining, "background_capture", 0, 1.0), 
                                         daemon=True).start()
                    else:
                        # Just the wake word
                        self._say("Yes? I'm listening.", auto_listen=True)
                        self.dataset_logger.log_interaction(
                            spoken_input="background_capture",
                            recognized_text=text,
                            mapped_intent="wake_word",
                            action_taken="Activated listener",
                            retry_count=0,
                            status="success"
                        )
                    
                    time.sleep(1.8) # Cool-down
            except Exception:
                pass
            time.sleep(0.1)


    # ── Core command processor ────────────────────────────────────────────────
    def _process(self, text):
        self.root.after(0, self._set_status, "⚙️ Processing...", "#a78bfa")
        
        # Determine intent early
        intent, payload = IntentMapper.parse_intent(text)

        # Global Handlers
        if intent == "cancel":
            self._flow = None
            self._say("Okay, I've stopped what I was doing.")
            self.root.after(0, self._set_status, "● Ready", "#22c55e")
            return

        # Acknowledge what was heard (feedback loop)
        if not self._flow:
            self.speak(f"Heard you say: {text}")

        # Handle active multi-step flow
        if self._flow:
            self._execute_flow_step(text.strip())
            return

        self._execute(intent, payload, text)
        self.root.after(0, self._set_status, "● Ready", "#22c55e")


    def _execute(self, intent, payload, original_text=""):
        start_time = time.time()
        status = "success"
        error_msg = ""
        action_taken = f"Executed {intent}"
        
        try:
            # ── Navigation ────────────────────────────────────────────────────────
            if intent == "nav":
                routes = {
                    "dashboard": "/dashboard",
                    "tasks":     "/tasks",
                    "notes":     "/notes",
                    "calendar":  "/calendar",
                    "courses":   "/courses/manager",
                    "resources": "/resources",
                }
                url = BASE_URL + routes.get(payload, "/dashboard")
                webbrowser.open(url)
                msg = f"Opening your {payload}."
                self._say(msg)
                action_taken = msg
    
            # ── Add task ──────────────────────────────────────────────────────────
            elif intent == "add_task":
                if not payload:
                    self._flow = {"intent": "add_task", "step": "title", "data": {}}
                    self._say("What is the task title?", auto_listen=True)
                    action_taken = "Initiated add_task flow (title)"
                else:
                    self._flow = {"intent": "add_task", "step": "date", "data": {"title": payload}}
                    self._say(f"Adding '{payload}'. When is the deadline date? (e.g. Tomorrow or April 10)", auto_listen=True)
                    action_taken = f"Initiated add_task flow for '{payload}'"

            # ── Add note ──────────────────────────────────────────────────────────
            elif intent == "add_note":
                if not payload:
                    self._flow = {"intent": "add_note", "step": "title", "data": {}}
                    self._say("What is the note about?", auto_listen=True)
                    action_taken = "Initiated add_note flow (title)"
                else:
                    self._flow = {"intent": "add_note", "step": "content", "data": {"title": payload}}
                    self._say(f"Note '{payload}' started. What contents should I include?", auto_listen=True)
                    action_taken = f"Initiated add_note flow for '{payload}'"

            # ── Add resource ──────────────────────────────────────────────────────
            elif intent == "add_resource":
                if not payload:
                    self._flow = {"intent": "add_resource", "step": "title", "data": {}}
                    self._say("What is the resource name?", auto_listen=True)
                    action_taken = "Initiated add_resource flow (title)"
                else:
                    self._flow = {"intent": "add_resource", "step": "url", "data": {"title": payload}}
                    self._say(f"Saving resource '{payload}'. What is the URL?", auto_listen=True)
                    action_taken = f"Initiated add_resource flow for '{payload}'"

            # ── Complete task ─────────────────────────────────────────────────────
            elif intent == "complete_task":
                if not payload:
                    self._pending_intent = "complete_task"
                    self._say("Which task would you like to mark as complete?")
                    action_taken = "Asking for task title to complete"
                    return action_taken
                data = self.api_get("/api/tasks/pending")
                if data is None:
                    status = "failure"
                    error_msg = "API GET failed"
                    self._say("I couldn't reach the server.")
                    action_taken = "Error: API GET failed"
                    return action_taken
                match = next((t for t in data if payload.lower() in t["title"].lower()), None)
                if match:
                    ok = self.api_post_form(f"/tasks/complete/{match['id']}", {})
                    if ok:
                        self._say(f"Great job! Task '{match['title']}' marked as complete.")
                        webbrowser.open(f"{BASE_URL}/tasks")
                        action_taken = f"Completed task '{match['title']}'"
                    else:
                        status = "failure"
                        error_msg = "API POST complete failed"
                        self._say("Something went wrong.")
                        action_taken = "Error: API POST failed"
                else:
                    status = "failure"
                    error_msg = f"No task match for '{payload}'"
                    self._say(f"I couldn't find a pending task matching '{payload}'.")
                    action_taken = f"Failure: No task match for '{payload}'"
    
            # ── List tasks ────────────────────────────────────────────────────────
            elif intent == "list_tasks":
                data = self.api_get("/api/tasks/pending")
                if data is None:
                    status = "failure"
                    self._say("I couldn't reach the server.")
                    return "Error: API connection failed"
                if not data:
                    self._say("You have no pending tasks. Great work!")
                    action_taken = "Listed 0 tasks"
                else:
                    titles = [t["title"] for t in data[:5]]
                    summary = ", ".join(titles)
                    self._say(f"You have {len(data)} pending tasks. Here are the first few: {summary}.")
                    webbrowser.open(f"{BASE_URL}/dashboard")
                    action_taken = f"Listed {len(data)} tasks"
            # ── Today's Schedule ──────────────────────────────────────────────────
            elif intent == "today_schedule":
                data = self.api_get("/api/tasks/today")
                if data is None:
                    status = "failure"
                    self._say("I couldn't fetch your schedule.")
                    return "Error: API connection failed"
                if not data:
                    self._say("Your schedule is clear for today! No urgent tasks.")
                    action_taken = "Read empty schedule"
                else:
                    titles = [t["title"] for t in data]
                    summary = " and ".join([", ".join(titles[:-1]), titles[-1]] if len(titles) > 1 else titles)
                    self._say(f"Today you have: {summary}. Good luck!")
                    webbrowser.open(f"{BASE_URL}/dashboard")
                    action_taken = "Read today's schedule"
    
            # ── Upcoming ──────────────────────────────────────────────────────────
            elif intent == "upcoming_tasks":
                data = self.api_get("/api/tasks/upcoming")
                if data is None:
                    status = "failure"
                    self._say("I couldn't find your deadlines.")
                    return "Error: API connection failed"
                if not data:
                    self._say("You have no upcoming deadlines in the next few days.")
                    action_taken = "Read empty deadlines"
                else:
                    items = ". ".join([f"{t['title']} due {t['deadline']}" for t in data[:3]])
                    self._say(f"Here are your next 3 deadlines: {items}.")
                    webbrowser.open(f"{BASE_URL}/dashboard")
                    action_taken = "Read upcoming deadlines"

            # ── List notes ────────────────────────────────────────────────────────
            elif intent == "list_notes":
                data = self.api_get("/api/notes/all")
                if data is None:
                    status = "failure"
                    self._say("I couldn't reach the server.")
                    return "Error: API connection failed"
                if not data:
                    self._say("You have no notes yet.")
                    action_taken = "Listed 0 notes"
                else:
                    titles = ", ".join([n["title"] for n in data[:5]])
                    self._say(f"You have {len(data)} notes. Recent ones: {titles}.")
                    webbrowser.open(f"{BASE_URL}/notes")
                    action_taken = f"Listed {len(data)} notes"
    
            # ── Help ──────────────────────────────────────────────────────────────
            elif intent == "help":
                msg = "I can add tasks, notes, resources, list goals, or open any study page. Just ask!"
                self._say(msg)
                action_taken = "Showed help message"
    
            # ── Unknown ───────────────────────────────────────────────────────────
            elif intent == "unknown" and original_text:
                status = "failure"
                error_msg = "Unknown intent"
                self._say("I didn't understand that. Say 'help' to see my capabilities.")
                action_taken = "Failed to map intent"

        except Exception as e:
            status = "failure"
            error_msg = str(e)
            self._say(f"An internal error occurred: {e}")
            action_taken = f"Error: {e}"
    
        finally:
            exec_time = time.time() - start_time
            if intent != "unknown" or original_text: # Log only real commands
                self.logger.record_action(original_text, intent, status, exec_time, error_msg)
        
        return action_taken

    def _execute_flow_step(self, text, audio_path="none", retry_count=0, test_id="none"):
        intent = self._flow["intent"]
        step = self._flow["step"]
        data = self._flow["data"]
        action_taken = "Unknown flow step"
        
        # --- GLOBAL CANCEL ---
        if any(w in text.lower() for w in ["cancel", "stop", "nevermind", "quit", "forget"]):
            self._flow = None
            self._say("Okay, I've cancelled the request.")
            action_taken = "Cancelled flow"
            # Log cancel
            self.dataset_logger.log_interaction(
                test_id=test_id,
                spoken_input=audio_path,
                recognized_text=text,
                mapped_intent="cancel_flow",
                action_taken=action_taken,
                retry_count=retry_count,
                status="success"
            )
            return

        # --- ADD TASK FLOW ---
        if intent == "add_task":
            if step == "title":
                data["title"] = text
                self._flow["step"] = "date"
                self._say(f"Title set to '{text}'. When is the deadline date? (e.g. today, tomorrow, or a date)", auto_listen=True)
                action_taken = f"Set task title to {text}"
            elif step == "date":
                processed_date = text.lower()
                if "today" in processed_date:
                    processed_date = time.strftime("%Y-%m-%d")
                elif "tomorrow" in processed_date:
                    from datetime import datetime, timedelta
                    processed_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                
                data["date"] = processed_date
                self._flow["step"] = "time"
                self._say(f"Date set for {processed_date}. What time? (e.g. 10 AM or 3 PM)", auto_listen=True)
                action_taken = f"Set task date to {processed_date}"
            elif step == "time":
                self._flow = None
                dt_str = f"{data['date']} {text}"
                ok = self.api_post_form("/tasks/add", {"title": data["title"], "deadline_date": data["date"], "deadline_time": text})
                if ok:
                    self._say(f"All done! I've successfully added '{data['title']}' for {dt_str}.")
                    webbrowser.open(f"{BASE_URL}/tasks")
                    action_taken = f"Created task: {data['title']} for {dt_str}"
                else:
                    self._say("I encountered an error while saving the task.")
                    action_taken = "Error: API POST failed for add_task"

        # --- ADD NOTE FLOW ---
        elif intent == "add_note":
            if step == "title":
                data["title"] = text
                self._flow["step"] = "content"
                self._say(f"Title set to {text}. What are the contents?", auto_listen=True)
                action_taken = f"Set note title to {text}"
            elif step == "content":
                self._flow = None
                ok = self.api_post_form("/notes/add", {"title": data["title"], "content": text})
                if ok:
                    self._say(f"Note '{data['title']}' has been saved to your library.")
                    webbrowser.open(f"{BASE_URL}/notes")
                    action_taken = f"Saved note: {data['title']}"
                else:
                    self._say("Failed to save the note.")
                    action_taken = "Error: Note save failed"

        # --- ADD RESOURCE FLOW ---
        elif intent == "add_resource":
            if step == "title":
                data["title"] = text
                self._flow["step"] = "url"
                self._say(f"Resource: {text}. What is the URL?", auto_listen=True)
                action_taken = f"Set resource title to {text}"
            elif step == "url":
                self._flow = None
                ok = self.api_post_form("/resources/add", {"title": data["title"], "url": text, "category": "General"})
                if ok:
                    msg = f"Resource saved! I've added {data['title']} to your links."
                    self._say(msg)
                    webbrowser.open(f"{BASE_URL}/resources")
                    action_taken = msg
                else:
                    self._say("Resource couldn't be saved.")
                    action_taken = "Error: Resource save failed"

        # Log flow step
        self.dataset_logger.log_interaction(
            spoken_input="flow_input",
            recognized_text=text,
            mapped_intent=f"{intent}_step_{step}",
            action_taken=action_taken,
            retry_count=0,
            status="success" if not action_taken.startswith("Error:") else "failure"
        )

        self.root.after(0, self._set_status, "● Ready", "#22c55e")


if __name__ == "__main__":
    ScholasticDesktopSiri()
