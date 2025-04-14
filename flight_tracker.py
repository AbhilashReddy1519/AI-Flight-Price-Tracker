import http.client
import json
import os
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
import random

load_dotenv()

class FlightTracker:
    def __init__(self):
        self.conn = http.client.HTTPSConnection("booking-com15.p.rapidapi.com")
        self.headers = {
            'x-rapidapi-key': os.getenv("RAPIDAPI_KEY", "4ca67c45e8msh550d34947a5a148p1718abjsnfed5a3b51096"),
            'x-rapidapi-host': "booking-com15.p.rapidapi.com"
        }
        self.history_file = "data/history.csv"
        self.sender_email = os.getenv("EMAIL_USER")
        self.sender_password = os.getenv("EMAIL_PASS")
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)

    def fetch_flights(self, origin, destination, depart_date, adults=1, cabin_class="ECONOMY"):
        try:
            origin_id = f"{origin}.AIRPORT"
            destination_id = f"{destination}.AIRPORT"

            endpoint = (
                f"/api/v1/flights/searchFlights?"
                f"fromId={origin_id}&toId={destination_id}&"
                f"departDate={depart_date}&adults={adults}&children=0&"
                f"cabinClass={cabin_class.upper()}¤cy_code=USD"
            )

            self.conn.request("GET", endpoint, headers=self.headers)
            res = self.conn.getresponse()
            data = res.read().decode("utf-8")
            print(f"[Flight Fetch] Raw API Response: {data}")

            if res.status != 200:
                print(f"[Flight Fetch] API request failed with status {res.status}")
                return self._fetch_mock_flights(origin, destination, depart_date)

            parsed_data = json.loads(data)
            if 'data' not in parsed_data or not parsed_data['data']:
                print(f"[Flight Fetch] No 'data' key or empty data in response")
                return self._fetch_mock_flights(origin, destination, depart_date)

            flights = self._parse_response(parsed_data, origin, destination, depart_date)
            if flights:
                self._save_to_history(flights)
            return flights

        except Exception as e:
            print(f"[Flight Fetch] Error: {str(e)}")
            return self._fetch_mock_flights(origin, destination, depart_date)

    def _fetch_mock_flights(self, origin, destination, depart_date):
        print("[Flight Fetch] Using mock data as fallback")
        airlines = ["Delta", "United", "American", "British Airways"]
        flights = []
        for _ in range(3):  # Return multiple mock flights
            flights.append({
                "airline": random.choice(airlines),
                "price": random.uniform(50, 500),
                "departure_time": "10:00 AM",  # Mock departure time
                "date_checked": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "origin": origin,
                "destination": destination,
                "depart_date": depart_date
            })
        self._save_to_history(flights)
        return flights

    def _parse_response(self, data, origin, destination, depart_date):
        flights = []
        for flight in data.get('data', []):
            price = float(flight.get('price', {}).get('amount', 0)) if flight.get('price') else 0.0
            airline = flight.get('segments', [{}])[0].get('marketingCarrier', {}).get('name', 'Unknown')
            departure_time = flight.get('segments', [{}])[0].get('departureTime', 'N/A')

            flights.append({
                "airline": airline,
                "price": price,
                "departure_time": departure_time,
                "date_checked": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "origin": origin,
                "destination": destination,
                "depart_date": depart_date
            })
        return flights

    def _save_to_history(self, flights):
        try:
            df = pd.DataFrame(flights)
            if os.path.exists(self.history_file):
                history = pd.read_csv(self.history_file)
                df = pd.concat([history, df], ignore_index=True)
            df.to_csv(self.history_file, index=False)
        except Exception as e:
            print(f"[Save History] Error: {str(e)}")

    def get_historical_data(self, origin, destination, depart_date):
        try:
            if not os.path.exists(self.history_file):
                return pd.DataFrame(columns=['airline', 'price', 'departure_time', 'date_checked', 'origin', 'destination', 'depart_date'])
            history = pd.read_csv(self.history_file)
            return history[
                (history["origin"] == origin) &
                (history["destination"] == destination) &
                (history["depart_date"] == depart_date)
            ]
        except Exception as e:
            print(f"[Get History] Error: {str(e)}")
            return pd.DataFrame(columns=['airline', 'price', 'departure_time', 'date_checked', 'origin', 'destination', 'depart_date'])

    def check_price_drop(self, origin, destination, depart_date):
        try:
            current_flights = self.fetch_flights(origin, destination, depart_date)
            if not current_flights:
                return None, None

            historical_data = self.get_historical_data(origin, destination, depart_date)
            current_price = min(f["price"] for f in current_flights)

            if historical_data.empty:
                return current_price, None

            historical_min = historical_data["price"].min()
            return current_price, historical_min if current_price < historical_min else None
        except Exception as e:
            print(f"[Check Price Drop] Error: {str(e)}")
            return None, None

    def send_email(self, recipient, message):
        try:
            msg = MIMEText(message)
            msg['Subject'] = "✈️ Flight Price Drop Alert!"
            msg['From'] = self.sender_email
            msg['To'] = recipient

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, recipient, msg.as_string())
            return True
        except Exception as e:
            print(f"[Send Email] Error: {str(e)}")
            raise Exception(f"Email sending failed: {str(e)}")