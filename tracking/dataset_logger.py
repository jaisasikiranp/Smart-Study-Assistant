import json
import os
import csv
from datetime import datetime

class InteractionDatasetLogger:
    def __init__(self, json_path="tracking/interactions_dataset.json", csv_path="tracking/voice_dataset.csv"):
        self.json_path = json_path
        self.csv_path = csv_path
        self.headers = [
            "test_id", "spoken_input", "recognized_text", "mapped_intent", 
            "action_taken", "retry_count", "status", "failure_stage", 
            "root_cause_category", "final_output", "expected_output", "timestamp"
        ]
        # Ensure directories exist
        os.makedirs(os.path.dirname(self.json_path), exist_ok=True)
        self._ensure_files_exist()

    def _ensure_files_exist(self):
        # JSON initialization
        if not os.path.exists(self.json_path) or os.path.getsize(self.json_path) == 0:
            with open(self.json_path, "w") as f:
                json.dump([], f)
        
        # CSV initialization
        if not os.path.exists(self.csv_path) or os.path.getsize(self.csv_path) == 0:
            with open(self.csv_path, "w", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(self.headers)

    def log_interaction(self, **kwargs):
        """
        Logs a single interaction.
        Accepts any of the fields in self.headers.
        """
        # Default values for fields if not provided
        record = {h: kwargs.get(h, "none") for h in self.headers}
        if record["timestamp"] == "none":
            record["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
        # 1. Log to JSON (legacy support)
        try:
            data = []
            if os.path.exists(self.json_path) and os.path.getsize(self.json_path) > 0:
                with open(self.json_path, "r") as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        data = []
            data.append(record)
            with open(self.json_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[Dataset] JSON Log Error: {e}")

        # 2. Log to CSV (new requirement)
        try:
            with open(self.csv_path, "a", newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.headers)
                writer.writerow(record)
            print(f"[Dataset] Logged interaction to CSV: {record['test_id']} ({record['status']})")
        except Exception as e:
            print(f"[Dataset] CSV Log Error: {e}")

    def log_intermediate_failure(self, recognized_text, error_msg, attempt_number, test_id="none", spoken_input="none"):
        """
        Logs an intermediate failure as its own row in the dataset.
        """
        # Determine failure stage
        failure_stage = "speech_recognition" if not recognized_text else "intent_mapping"
        
        self.log_interaction(
            test_id=test_id,
            spoken_input=spoken_input,
            recognized_text=recognized_text,
            status="failure",
            retry_count=attempt_number,
            failure_stage=failure_stage,
            action_taken=f"Retry prompted: {error_msg}",
            final_output="none",
            expected_output="unknown",
            root_cause_category="unknown"
        )

    def get_csv_data(self):
        """Returns the raw CSV data as a string for export."""
        if os.path.exists(self.csv_path):
            with open(self.csv_path, "r") as f:
                return f.read()
        return ""
