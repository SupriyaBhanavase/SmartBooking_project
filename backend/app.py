from flask import Flask, request, jsonify
import sqlite3
import os
import urllib.request
import urllib.error
import json
from datetime import datetime
from uuid import uuid4

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), "smartbooking.db")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma3:1b")

VEHICLES = {
    "Bike": {"base": 20, "per_km": 8},
    "Mini": {"base": 50, "per_km": 12},
    "Sedan": {"base": 80, "per_km": 16},
    "SUV": {"base": 120, "per_km": 22},
}
DRIVERS = [
    {"name": "Aarav Patil", "vehicle": "Bike"},
    {"name": "Sana Shaikh", "vehicle": "Mini"},
    {"name": "Rohan Jadhav", "vehicle": "Sedan"},
    {"name": "Meera Kulkarni", "vehicle": "SUV"},
]

def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with connect_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id TEXT PRIMARY KEY,
                customer TEXT NOT NULL,
                pickup TEXT NOT NULL,
                destination TEXT NOT NULL,
                distance REAL NOT NULL,
                vehicle TEXT NOT NULL,
                fare REAL NOT NULL,
                commission REAL NOT NULL,
                driver TEXT NOT NULL,
                payment_status TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

def booking_dict(row):
    return {key: row[key] for key in row.keys()}

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response

@app.route("/api/<path:path>", methods=["OPTIONS"])
def options_handler(path):
    return ("", 204)

@app.get("/api/health")
def health():
    return jsonify({"ok": True, "message": "SmartBooking API is running", "ai_model": OLLAMA_MODEL})

@app.get("/api/pricing")
def pricing():
    return jsonify(VEHICLES)

@app.get("/api/bookings")
def list_bookings():
    with connect_db() as conn:
        rows = conn.execute("SELECT * FROM bookings ORDER BY created_at DESC LIMIT 100").fetchall()
    return jsonify([booking_dict(row) for row in rows])

@app.get("/api/bookings/<booking_id>")
def get_booking(booking_id):
    with connect_db() as conn:
        row = conn.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()
    if not row:
        return jsonify({"error": "Booking not found"}), 404
    return jsonify(booking_dict(row))

@app.post("/api/bookings")
def create_booking():
    data = request.get_json(silent=True) or {}
    customer = str(data.get("customer", "")).strip()
    pickup = str(data.get("pickup", "")).strip()
    destination = str(data.get("destination", "")).strip()
    vehicle = str(data.get("vehicle", "Mini")).strip()
    try:
        distance = float(data.get("distance", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "Distance must be a number."}), 400

    if not customer or not pickup or not destination:
        return jsonify({"error": "Please enter customer name, pickup and destination."}), 400
    if vehicle not in VEHICLES:
        return jsonify({"error": "Please select a valid vehicle."}), 400
    if distance <= 0 or distance > 1000:
        return jsonify({"error": "Distance must be between 0 and 1000 km."}), 400

    fare = round(VEHICLES[vehicle]["base"] + distance * VEHICLES[vehicle]["per_km"], 2)
    commission = round(fare * 0.10, 2)
    driver = next((d["name"] for d in DRIVERS if d["vehicle"] == vehicle), "Demo Driver")
    booking_id = "SB-" + uuid4().hex[:8].upper()
    created_at = datetime.now().astimezone().isoformat(timespec="seconds")
    booking = {
        "id": booking_id, "customer": customer, "pickup": pickup,
        "destination": destination, "distance": distance, "vehicle": vehicle,
        "fare": fare, "commission": commission, "driver": driver,
        "payment_status": "Demo payment pending", "status": "Confirmed",
        "created_at": created_at
    }
    with connect_db() as conn:
        conn.execute("""
            INSERT INTO bookings
            (id, customer, pickup, destination, distance, vehicle, fare, commission,
             driver, payment_status, status, created_at)
            VALUES (:id, :customer, :pickup, :destination, :distance, :vehicle,
                    :fare, :commission, :driver, :payment_status, :status, :created_at)
        """, booking)
    return jsonify(booking), 201

@app.post("/api/ai")
def ai_assistant():
    data = request.get_json(silent=True) or {}
    question = str(data.get("question", "")).strip()
    if not question:
        return jsonify({"error": "Type a question first."}), 400

    prompt = (
        "You are SmartBooking's helpful booking assistant. Answer in simple English, "
        "briefly and safely. You can explain booking steps, demo fares, receipts, "
        "drivers, and booking history. Do not claim that real payments or live maps "
        "are connected. This is a student demo project.\\n"
        f"User question: {question}\\nAnswer:"
    )
    payload = json.dumps({
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_URL, data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            result = json.loads(response.read().decode("utf-8"))
        return jsonify({"answer": result.get("response", "").strip(), "model": OLLAMA_MODEL})
    except urllib.error.URLError:
        return jsonify({
            "error": "Ollama is not responding. Start Ollama and check the model name.",
            "hint": "Run `ollama list`, then set OLLAMA_MODEL to the exact Gemma model name."
        }), 503
    except Exception as exc:
        return jsonify({"error": "AI request failed.", "details": str(exc)}), 500

init_db()

if __name__ == "__main__":
  app.run(host="127.0.0.1", port=8000, debug=False)
