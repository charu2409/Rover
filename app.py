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
    cred = credentials.Certificate("serviceAccountKey.json")  # local fallback
firebase_admin.initialize_app(cred)

db = firestore.client()
logs_ref = db.collection("rover_logs")



# Create new log (POST)
@app.route("/log", methods=["POST"])
def create_log():
    data = request.json
    data["timestamp"] = datetime.datetime.utcnow()
    log_ref = logs_ref.add(data)  # auto-generated ID
    return jsonify({"message": "Log created", "log_id": log_ref[1].id}), 201

# Get all logs (GET)
@app.route("/logs", methods=["GET"])
def get_all_logs():
    docs = logs_ref.order_by("timestamp", direction=firestore.Query.DESCENDING).stream()
    return jsonify([{**doc.to_dict(), "log_id": doc.id} for doc in docs]), 200

# Get one log by ID (GET)
@app.route("/log/<log_id>", methods=["GET"])
def get_log(log_id):
    doc = logs_ref.document(log_id).get()
    if doc.exists:
        return jsonify({**doc.to_dict(), "log_id": doc.id}), 200
    return jsonify({"error": "Log not found"}), 404

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
@app.route("/delete-log/<log_id>", methods=["POST"])
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
