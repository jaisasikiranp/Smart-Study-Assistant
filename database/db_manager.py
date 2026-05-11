import sqlite3
import datetime
import os

class LogDatabase:
    def __init__(self, db_path="database/assistant_logs.db"):
        self.db_path = db_path
        self._ensure_db_exists()

    def _ensure_db_exists(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Logs Table: every command interaction
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS assistant_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            command TEXT,
            intent TEXT,
            status TEXT, -- 'success', 'failure', 'rejected'
            execution_time FLOAT,
            error_message TEXT
        )
        """)
        
        # KPIs Table: daily/weekly summaries
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS kpi_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE UNIQUE,
            total_commands INTEGER DEFAULT 0,
            success_count INTEGER DEFAULT 0,
            failure_count INTEGER DEFAULT 0,
            avg_execution_time FLOAT DEFAULT 0,
            tasks_added INTEGER DEFAULT 0,
            tasks_completed INTEGER DEFAULT 0
        )
        """)
        
        conn.commit()
        conn.close()

    def log_command(self, command, intent, status, execution_time, error_msg=""):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO assistant_logs (command, intent, status, execution_time, error_message)
        VALUES (?, ?, ?, ?, ?)
        """, (command, intent, status, execution_time, error_msg))
        conn.commit()
        
        # After logging, update the daily KPI summary (simplified for local use)
        self._update_kpis(status, execution_time, intent)
        conn.close()

    def _update_kpis(self, status, execution_time, intent):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        today = datetime.date.today().isoformat()
        
        # Ensure today's record exists
        cursor.execute("INSERT OR IGNORE INTO kpi_summaries (date) VALUES (?)", (today,))
        
        success_val = 1 if status == 'success' else 0
        failure_val = 1 if status == 'failure' else 0
        
        # Basic command counts
        cursor.execute("""
        UPDATE kpi_summaries SET
        total_commands = total_commands + 1,
        success_count = success_count + ?,
        failure_count = failure_count + ?,
        avg_execution_time = (avg_execution_time * total_commands + ?) / (total_commands + 1)
        WHERE date = ?
        """, (success_val, failure_val, execution_time, today))
        
        # Productivity KPIs
        if intent == "add_task" and status == "success":
            cursor.execute("UPDATE kpi_summaries SET tasks_added = tasks_added + 1 WHERE date = ?", (today,))
        elif intent == "complete_task" and status == "success":
            cursor.execute("UPDATE kpi_summaries SET tasks_completed = tasks_completed + 1 WHERE date = ?", (today,))
            
        conn.commit()
        conn.close()

    def get_kpis(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM kpi_summaries ORDER BY date DESC LIMIT 30")
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows
