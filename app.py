from flask import Flask, request, jsonify, render_template
from flight_tracker import FlightTracker
import threading
import time
from datetime import datetime
import re

app = Flask(__name__)
tracker = FlightTracker()
alerts = {}

def validate_inputs(origin, destination, depart_date, email):
    if not re.match(r'^[A-Z]{3}$', origin) or not re.match(r'^[A-Z]{3}$', destination):
        return False, "Invalid IATA codes"

    try:
        if datetime.strptime(depart_date, '%Y-%m-%d') < datetime.now():
            return False, "Departure date must be in the future"
    except ValueError:
        return False, "Departure date must be in YYYY-MM-DD format"

    if email and not re.match(r'^[\w.-]+@[\w.-]+\.\w+$', email):
        return False, "Invalid email address"
    
    return True, ""

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/flights', methods=['POST'])
def get_flights():
    data = request.get_json()
    origin = data.get('origin', '').upper()
    destination = data.get('destination', '').upper()
    depart_date = data.get('depart_date', '')
    adults = int(data.get('adults', 1))
    cabin_class = data.get('cabin_class', 'ECONOMY')

    valid, error = validate_inputs(origin, destination, depart_date, "")
    if not valid:
        return jsonify({"error": error}), 400

    try:
        flights = tracker.fetch_flights(origin, destination, depart_date, adults, cabin_class)
        if not flights:
            return jsonify({"error": "No flights found, using mock data"}), 200
        return jsonify(flights)
    except Exception as e:
        return jsonify({"error": f"Failed to fetch flights: {str(e)}"}), 500

@app.route('/api/history', methods=['POST'])
def get_history():
    data = request.get_json()
    origin = data.get('origin', '').upper()
    destination = data.get('destination', '').upper()
    depart_date = data.get('depart_date', '')

    try:
        history = tracker.get_historical_data(origin, destination, depart_date)
        return jsonify(history.to_dict(orient='records'))
    except Exception as e:
        return jsonify({"error": f"Failed to fetch history: {str(e)}"}), 500

@app.route('/api/set_alert', methods=['POST'])
def set_alert():
    data = request.get_json()
    origin = data.get('origin', '').upper()
    destination = data.get('destination', '').upper()
    depart_date = data.get('depart_date', '')
    email = data.get('email', '')

    valid, error = validate_inputs(origin, destination, depart_date, email)
    if not valid:
        return jsonify({"error": error}), 400

    if not email:
        return jsonify({"error": "Email is required for alerts"}), 400

    route = f"{origin}-{destination}-{depart_date}"
    alerts[route] = {
        "email": email,
        "last_checked": 0,
        "active": True
    }

    if not any(t.name == "price_checker" for t in threading.enumerate()):
        threading.Thread(target=check_prices_periodically, name="price_checker", daemon=True).start()

    return jsonify({"message": "Price alert set successfully"})

def check_prices_periodically():
    while True:
        for route, alert in list(alerts.items()):
            if not alert["active"]:
                continue

            current_time = time.time()
            if current_time - alert["last_checked"] < 3600:
                continue

            origin, destination, depart_date = route.split('-')
            try:
                current_price, historical_min = tracker.check_price_drop(origin, destination, depart_date)
                if current_price is not None and historical_min is not None:
                    message = (
                        f"Price drop detected!\n"
                        f"Route: {origin} → {destination}\n"
                        f"Departure Date: {depart_date}\n"
                        f"New Price: ${current_price:.2f} (Previous min: ${historical_min:.2f})"
                    )
                    tracker.send_email(alert["email"], message)
                    alerts[route]["active"] = False
            except Exception as e:
                print(f"Price check failed for {route}: {str(e)}")

            alerts[route]["last_checked"] = current_time
        time.sleep(60)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)