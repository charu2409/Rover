import os
import json
from flask import Flask, request, jsonify, render_template
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

app = Flask(__name__)

if "FIREBASE_KEY" in os.environ:
    cred_dict = json.loads(os.environ["FIREBASE_KEY"])
    cred = credentials.Certificate(cred_dict)
else:
    cred = credentials.Certificate("C:/Users/charu/Downloads/rover-b01fb-firebase-adminsdk-fbsvc-95614c61b5.json")

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()
rover = db.collection("rover")

def map_rover_data(data):
    speed_map = {1: "0.5 kmph", 2: "1 kmph", 3: "1.5 kmph", 4: "2 kmph", 5: "2.5 kmph"}
    steering_map = {1: "Home pos mode", 2: "All wheel mode", 3: "Zero turn", 4: "Crab"}
    shearing_map = {0: "Home pos", 1: "Sensing pos"}

    mapped = data.copy()
    mapped["Speed"] = speed_map.get(data.get("Speed", 0), "Unknown")
    mapped["Steering_Mode"] = steering_map.get(data.get("Steering_Mode", 0), "Unknown")
    mapped["Shearing_Arm"] = shearing_map.get(data.get("Shearing_Arm", 0), "Unknown")
    
    if "timestamp" in mapped and mapped["timestamp"]:
        mapped["timestamp"] = mapped["timestamp"].isoformat()
    
    return mapped

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/debug")
def debug():
    return jsonify({
        "FIREBASE_KEY_EXISTS": "FIREBASE_KEY" in os.environ,
        "DB_INIT": "yes" if 'db' in globals() else "no"
    })

@app.route("/rovers", methods=["GET"])
def list_rovers():
    docs = rover.stream()
    all_data = []
    for doc in docs:
        d = doc.to_dict()
        d["id"] = doc.id
        d = map_rover_data(d)
        all_data.append(d)
    # Return the latest rover data only for simplicity
    latest = all_data[-1] if all_data else {}
    return jsonify({"success": True, "data": latest}), 200

@app.route("/rover", methods=["POST"])
def create_rover():
    data = request.get_json()
    if not data or not data.get("id"):
        return jsonify({"success": False, "error": "JSON with 'id' field required"}), 400
    
    doc_id = data["id"].strip()
    doc_ref = rover.document(doc_id)
    
    if doc_ref.get().exists:
        return jsonify({"success": False, "error": "Rover data with this ID already exists"}), 409
    
    doc_ref.set({**data, "timestamp": firestore.SERVER_TIMESTAMP})
    return jsonify({"success": True, "message": "Rover data created"}), 201

@app.route("/rover/<doc_id>", methods=["PUT"])
def update_rover(doc_id):
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "JSON body required"}), 400
    
    doc_ref = rover.document(doc_id.strip())
    if not doc_ref.get().exists:
        return jsonify({"success": False, "error": "Rover data not found"}), 404
    
    doc_ref.set({**data, "timestamp": firestore.SERVER_TIMESTAMP}, merge=True)
    updated = map_rover_data(doc_ref.get().to_dict())
    return jsonify({"success": True, "message": "Rover data updated", "data": updated}), 200

@app.route("/delete-rover", methods=["POST"])
def delete_rover():
    data = request.get_json()
    if not data or not data.get("id"):
        return jsonify({"error": "JSON with 'id' field required"}), 400
    
    rover_id = data["id"].strip()
    doc_ref = rover.document(rover_id)
    
    if not doc_ref.get().exists:
        return jsonify({"error": "Rover data not found"}), 404
    
    deleted = map_rover_data(doc_ref.get().to_dict())
    doc_ref.delete()
    return jsonify({"message": "Rover data deleted", "data": deleted}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
