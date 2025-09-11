import os, json
from flask import Flask, request, jsonify, render_template
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

app = Flask(__name__)

# Initialize Firebase
if "FIREBASE_KEY" in os.environ:
    cred_dict = json.loads(os.environ["FIREBASE_KEY"])
    cred = credentials.Certificate(cred_dict)
else:
    cred = credentials.Certificate("C:/Users/charu/Downloads/rover-b01fb-firebase-adminsdk-fbsvc-95614c61b5.json")

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()
rover = db.collection("rover")
rover_logs = db.collection("rover_logs")  # Collection for storing all logs

# Home route
@app.route("/")
def home():
    return render_template("index.html")

# Debug route
@app.route("/debug")
def debug():
    return jsonify({
        "FIREBASE_KEY_EXISTS": "FIREBASE_KEY" in os.environ,
        "DB_INIT": "yes" if 'db' in globals() else "no"
    })

# Get latest rover data
@app.route("/rover/latest", methods=["GET"])
def get_latest_rover():
    doc_ref = rover.document("rover1")
    doc = doc_ref.get()
    if doc.exists:
        return jsonify({"success": True, "data": doc.to_dict()}), 200
    return jsonify({"success": False, "error": "Rover data not found"}), 404

# Create or update rover data (POST from rover)
@app.route("/rover", methods=["POST"])
def create_or_update_rover():
    data = request.get_json()
    if not data or not data.get("id"):
        return jsonify({"success": False, "error": "JSON with 'id' field required"}), 400

    rover_id = data["id"].strip()
    timestamp = datetime.utcnow()

    # Add timestamp in Firestore
    data["timestamp"] = timestamp

    # Update latest rover data
    rover.document(rover_id).set(data)

    # Log the data in rover_logs
    log_id = f"{rover_id}_{timestamp.isoformat()}"
    rover_logs.document(log_id).set(data)

    return jsonify({"success": True, "message": "Rover data updated and logged"}), 200

# Delete rover (if needed)
@app.route("/delete-rover", methods=["POST"])
def delete_rover():
    data = request.get_json()
    if not data or not data.get("id"):
        return jsonify({"error": "JSON with 'id' field required"}), 400

    rover_id = data["id"].strip()
    doc_ref = rover.document(rover_id)

    if not doc_ref.get().exists:
        return jsonify({"error": "Rover data not found"}), 404

    deleted = doc_ref.get().to_dict()
    doc_ref.delete()
    return jsonify({"message": "Rover data deleted", "data": deleted}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
