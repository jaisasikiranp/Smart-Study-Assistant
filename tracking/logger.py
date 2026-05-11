from database.db_manager import LogDatabase
import time

class AssistantLogger:
    def __init__(self, db_manager: LogDatabase):
        self.db = db_manager

    def record_action(self, command, intent, status, exec_time, error=""):
        self.db.log_command(command, intent, status, exec_time, error)
        print(f"Logged: {intent} as {status} in {exec_time:.2f}s")

    def get_summary_kpis(self):
        return self.db.get_kpis()

    def generate_smart_insight(self):
        kpis = self.db.get_kpis()
        if not kpis:
            return "Started your study journey! Add your first goal."
            
        latest = kpis[0]
        if latest.get('tasks_added', 0) > 3 and latest.get('tasks_completed', 0) == 0:
            return "You've added several tasks today—try prioritizing one to get started!"
        
        if latest.get('total_commands', 0) > 10:
            return "Great productivity! You're using the assistant frequently—consider shortcuts."
            
        return "System running optimally. Stay focused on your goals!"
