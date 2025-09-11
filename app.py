import os, json
from flask import Flask, request, jsonify, render_template
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

# --- Firebase Init ---
if "FIREBASE_KEY" in os.environ:
    cred_dict = json.loads(os.environ["FIREBASE_KEY"])
    cred = credentials.Certificate(cred_dict)
else:
    cred = credentials.Certificate("C:/Users/charu/Downloads/rover-b01fb-firebase-adminsdk-fbsvc-95614c61b5.json")

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()
rover = db.collection("rover")         # Stores latest rover data
rover_logs = db.collection("rover_logs")  # Stores history logs

@app.route("/")
def home():
    return render_template("index.html")

# ---------------- Rover (Latest Data) ----------------
@app.route("/rover/<doc_id>", methods=["GET"])
def get_rover(doc_id):
    doc = rover.document(doc_id.strip()).get()
    if doc.exists:
        return jsonify({"success": True, "data": doc.to_dict()}), 200
    return jsonify({"success": False, "error": "Rover data not found"}), 404

@app.route("/rover", methods=["POST"])
def create_or_update_rover():
    data = request.get_json()
    if not data or not data.get("id"):
        return jsonify({"success": False, "error": "JSON with 'id' field required"}), 400

    doc_id = data["id"].strip()
    timestamp = firestore.SERVER_TIMESTAMP

    # Update latest rover data
    rover.document(doc_id).set({**data, "timestamp": timestamp})

    # Add a new log entry with rover id
    rover_logs.add({**data, "id": doc_id, "timestamp": timestamp})

    return jsonify({"success": True, "message": "Rover data updated and logged"}), 201

# ---------------- Rover Logs CRUD ----------------
@app.route("/rover-logs/<rover_id>", methods=["GET"])
def get_rover_logs(rover_id):
    logs_ref = rover_logs.where("id", "==", rover_id).order_by("timestamp", direction=firestore.Query.DESCENDING)
    docs = logs_ref.stream()
    all_logs = [{"log_id": doc.id, **doc.to_dict()} for doc in docs]
    return jsonify({"success": True, "data": all_logs}), 200

@app.route("/rover-logs", methods=["GET"])
def get_all_logs():
    docs = rover_logs.order_by("timestamp", direction=firestore.Query.DESCENDING).stream()
    all_logs = [{"log_id": doc.id, **doc.to_dict()} for doc in docs]
    return jsonify({"success": True, "data": all_logs}), 200

@app.route("/rover-log/<log_id>", methods=["GET"])
def get_single_log(log_id):
    doc = rover_logs.document(log_id).get()
    if doc.exists:
        return jsonify({"success": True, "data": {"log_id": doc.id, **doc.to_dict()}}), 200
    return jsonify({"success": False, "error": "Log not found"}), 404

@app.route("/rover-log/<log_id>", methods=["PUT"])
def update_log(log_id):
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400
    rover_logs.document(log_id).update(data)
    return jsonify({"success": True, "message": "Log updated"}), 200

@app.route("/rover-log/<log_id>", methods=["POST"])
def delete_log(log_id):
    rover_logs.document(log_id).delete()
    return jsonify({"success": True, "message": "Log deleted"}), 200

# ---------------- Main ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
