from flask import Flask, render_template, jsonify, Response
import sqlite3
import pandas as pd
import os

app = Flask(__name__)
DB_PATH = "database/assistant_logs.db"

def get_stats():
    if not os.path.exists(DB_PATH):
        return {
            "total_commands": 0, "success_rate": "0%", "failure_rate": "0%",
            "avg_execution_time": "0s", "most_used": {}, "kpi_history": []
        }
        
    conn = sqlite3.connect(DB_PATH)
    try:
        # 1. Basic Stats
        df_logs = pd.read_sql_query("SELECT * FROM assistant_logs", conn)
        total_cmds = len(df_logs)
        success_rate = (df_logs['status'] == 'success').mean() * 100 if total_cmds > 0 else 0
        failure_rate = (df_logs['status'] == 'failure').mean() * 100 if total_cmds > 0 else 0
        avg_exec = df_logs['execution_time'].mean() if total_cmds > 0 else 0
        
        # 2. Most Used Commands
        most_used = df_logs['intent'].value_counts().to_dict()
        
        # 3. KPI Summaries
        df_kpi = pd.read_sql_query("SELECT * FROM kpi_summaries ORDER BY date DESC", conn)
    except Exception as e:
        print(f"DB Read Error (Assistant might not have run yet): {e}")
        return {
            "total_commands": 0, "success_rate": "0%", "failure_rate": "0%",
            "avg_execution_time": "0s", "most_used": {}, "kpi_history": []
        }
    finally:
        conn.close()
    
    return {
        "total_commands": total_cmds,
        "success_rate": f"{success_rate:.1f}%",
        "failure_rate": f"{failure_rate:.1f}%",
        "avg_execution_time": f"{avg_exec:.2f}s",
        "most_used": most_used,
        "kpi_history": df_kpi.to_dict(orient='records'),
        "voice_history": df_logs.sort_values('timestamp', ascending=False).to_dict(orient='records')
    }

@app.route("/")
def dashboard():
    stats = get_stats()
    return render_template("assistant_dashboard.html", stats=stats)

@app.route("/api/stats")
def api_stats():
    return jsonify(get_stats())

@app.route("/export/dataset")
def export_dataset():
    CSV_PATH = "tracking/voice_dataset.csv"
    if not os.path.exists(CSV_PATH):
        return "No dataset found", 404
    
    with open(CSV_PATH, "r") as f:
        csv_data = f.read()
    
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=voice_dataset_export.csv"}
    )

if __name__ == "__main__":
    # Ensure template directory exists
    if not os.path.exists("tracking/templates"):
        os.makedirs("tracking/templates")
    app.run(port=5050, debug=True)
