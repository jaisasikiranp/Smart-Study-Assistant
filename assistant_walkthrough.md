# 🎓 Student Smart Planner Desktop Assistant

I have transformed your website-based assistant into a robust **Standalone Desktop Application** that controls your website externally using elite-level automation (Playwright) and provides deep insights via a KPI analytics engine.

## 🚀 Key Features

-   **Standalone Desktop UI**: A sleek, dark-themed, and draggable interface built with **PyQt6**, decoupled from the website's UI.
-   **Programmatic Website Control**: No more manual browser navigating. The assistant uses **Playwright Chromium** to literally "drive" the website, fill forms, and click buttons.
-   **Speech & Intent Parsing**: Built-in **Speech-to-Text** and **Text-to-Speech** coupled with a dedicated study-intent command parser.
-   **Logging & KPI Engine**: Every command is logged into a local SQLite database (`assistant_logs.db`), tracking execution speed and success rates.
-   **Live Analytics Dashboard**: A secondary Flask-based dashboard showing usage trends, command distributions, and user productivity metrics.
-   **Smart Insights 🔥**: The AI proactively suggests productivity improvements based on your task history (e.g., "You've added several tasks today—try prioritizing one to get started!").

---

## 📂 Architecture Overview

```text
/desktop_app
   ├── main.py (Main Controller)
   └── ui.py (PyQt6 Premium Interface)

/automation
   ├── browser_controller.py (Playwright Manager)
   └── planner_actions.py (Website-specific logic)

/assistant
   ├── speech.py (STT/TTS Layer)
   └── command_parser.py (Intent/Logic Router)

/tracking
   ├── logger.py (Execution tracking & insights)
   ├── dashboard.py (Analytics Flask server)
   └── templates/ (Dashboard UI)

/database
   └── assistant_logs.db (SQLite persistent storage)
```

## 🛠️ How to Launch

1.  **Start the Ecosystem**:
    Run `launch_app.bat` to launch the Website Backend, Analytics Dashboard, and Desktop App simultaneously.
2.  **Using the Assistant**:
    -   Type a command like **"Add task 'Mathematics Study'"** and watch the browser execute it.
    -   Click the 🎙️ **Microphone icon** and say **"Navigate to dashboard"**.
3.  **View Your Performance**:
    Open [http://127.0.0.1:5050](http://127.0.0.1:5050) to see your **KPI Analytics Dashboard**, including command reliability and productivity trends.

---

### 🛡️ Restrictions
-   The assistant is hard-coded to only interact with the **Student Smart Planner** (`localhost:5000`).
-   Any unrelated commands (e.g., "What's the weather?") will be rejected with: *"This assistant only supports Smart Planner operations."*

---

> [!TIP]
> **Proactive Insight**: The assistant will automatically suggest a productivity check if it detects more than 3 tasks added in a single session without completions!
