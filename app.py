import os, json, datetime
from flask import Flask, request, jsonify, render_template
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

# --- Initialize Firebase Admin ---
if "FIREBASE_KEY" in os.environ:
    cred_dict = json.loads(os.environ["FIREBASE_KEY"])
    cred = credentials.Certificate(cred_dict)
else:
    cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()
logs_ref = db.collection("rover_logs")

# ---------------------- CRUD for Logs ----------------------

# Create new log (POST)
@app.route("/log", methods=["POST"])
def create_log():
    data = request.json
    data["timestamp"] = datetime.datetime.utcnow()
    # add rover_id field for UI compatibility
    data["rover_id"] = data.get("rover_id", "rover1")
    log_ref = logs_ref.add(data)
    return jsonify({"message": "Log created", "log_id": log_ref[1].id}), 201

# Get latest data for a rover
@app.route("/rover/<rover_id>", methods=["GET"])
def get_rover(rover_id):
    docs = (
        logs_ref.where("rover_id", "==", rover_id)
        .order_by("timestamp", direction=firestore.Query.DESCENDING)
        .limit(1)
        .stream()
    )
    latest = None
    for d in docs:
        latest = {**d.to_dict(), "log_id": d.id}
    if latest:
        return jsonify({"success": True, "data": latest}), 200
    return jsonify({"success": False, "error": "No data"}), 404

# Get all logs for a rover
@app.route("/rover-logs/<rover_id>", methods=["GET"])
def get_rover_logs(rover_id):
    docs = (
        logs_ref.where("rover_id", "==", rover_id)
        .order_by("timestamp", direction=firestore.Query.DESCENDING)
        .stream()
    )
    all_logs = [{**d.to_dict(), "log_id": d.id} for d in docs]
    return jsonify({"success": True, "data": all_logs}), 200

# Update log by ID (PUT)
@app.route("/log/<log_id>", methods=["PUT"])
def update_log(log_id):
    data = request.json
    log_doc = logs_ref.document(log_id)
    if log_doc.get().exists:
        data["updated_at"] = datetime.datetime.utcnow()
        log_doc.update(data)
        return jsonify({"message": f"Log {log_id} updated"}), 200
    return jsonify({"error": "Log not found"}), 404

# Delete log by ID (DELETE)
@app.route("/log/<log_id>", methods=["POST"])
def delete_log(log_id):
    log_doc = logs_ref.document(log_id)
    if log_doc.get().exists:
        log_doc.delete()
        return jsonify({"message": f"Log {log_id} deleted"}), 200
    return jsonify({"error": "Log not found"}), 404

# ---------------------- UI ----------------------

@app.route("/")
def index():
    return render_template("index.html")

# ---------------------- Run ----------------------

if __name__ == "__main__":
    app.run(debug=True)
