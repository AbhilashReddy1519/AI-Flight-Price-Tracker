import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.dates import DateFormatter
from flight_tracker import FlightTracker
import re
from datetime import datetime

class FlightTrackerUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Flight Price Tracker")
        self.root.geometry("1100x700")
        self.tracker = FlightTracker()
        self.alert_active = False

        self.style = ttk.Style()
        self.configure_styles()
        self.create_widgets()

    def configure_styles(self):
        self.style.theme_use('clam')
        self.style.configure('TFrame', background='#1a1a1a')
        self.style.configure('TLabel', background='#1a1a1a', foreground='#ffffff', font=('Helvetica', 12))
        self.style.configure('TButton', background='#00aaff', foreground='#ffffff', font=('Helvetica', 12, 'bold'), padding=10)
        self.style.map('TButton', background=[('active', '#0088cc')])
        self.style.configure('TEntry', fieldbackground='#333333', foreground='#ffffff', font=('Helvetica', 12))
        self.style.configure('Treeview', background='#2a2a2a', foreground='#ffffff', fieldbackground='#2a2a2a', font=('Helvetica', 11))
        self.style.configure('Treeview.Heading', background='#333333', foreground='#ffffff', font=('Helvetica', 12, 'bold'))

    def create_widgets(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        ttk.Label(header_frame, text="✈️ AI Flight Price Tracker", font=('Helvetica', 24, 'bold')).pack()

        # Input Section
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=10)

        self.origin_entry = self.create_input_field(input_frame, "From (IATA):", "JFK")
        self.destination_entry = self.create_input_field(input_frame, "To (IATA):", "LHR")
        self.date_entry = self.create_input_field(input_frame, "Date (YYYY-MM-DD):", "2025-04-15")
        self.email_entry = self.create_input_field(input_frame, "Email:", "your@email.com")

        # Advanced Options
        adv_frame = ttk.Frame(main_frame)
        adv_frame.pack(fill=tk.X, pady=10)
        ttk.Label(adv_frame, text="Passengers:").pack(side=tk.LEFT, padx=5)
        self.adults_spin = ttk.Spinbox(adv_frame, from_=1, to=9, width=5, font=('Helvetica', 12))
        self.adults_spin.pack(side=tk.LEFT, padx=5)
        self.adults_spin.set("1")
        ttk.Label(adv_frame, text="Class:").pack(side=tk.LEFT, padx=5)
        self.class_combo = ttk.Combobox(adv_frame, values=["economy", "premium_economy", "business"], width=15, font=('Helvetica', 12))
        self.class_combo.pack(side=tk.LEFT, padx=5)
        self.class_combo.set("economy")

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=15)
        ttk.Button(button_frame, text="Search Flights", command=self.check_prices).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Set Price Alert", command=self.set_alert).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="View Price History", command=self.show_plot).pack(side=tk.LEFT, padx=10)

        # Results Table
        results_frame = ttk.Frame(main_frame)
        results_frame.pack(fill=tk.BOTH, expand=True)
        columns = ('Airline', 'Price', 'Date Checked', 'Origin', 'Destination', 'Departure Date')
        self.tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor=tk.CENTER)
        
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_input_field(self, parent, label, default):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=5)
        ttk.Label(frame, text=label, width=20).pack(side=tk.LEFT, padx=5)
        entry = ttk.Entry(frame, font=('Helvetica', 12))
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        entry.insert(0, default)
        return entry

    def validate_inputs(self):
        origin = self.origin_entry.get().upper()
        destination = self.destination_entry.get().upper()
        date_str = self.date_entry.get()
        email = self.email_entry.get()

        if not re.match(r'^[A-Z]{3}$', origin) or not re.match(r'^[A-Z]{3}$', destination):
            messagebox.showerror("Error", "Please enter valid 3-letter IATA codes")
            return False
        
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            if datetime.strptime(date_str, '%Y-%m-%d') < datetime.now():
                messagebox.showerror("Error", "Please select a future date")
                return False
        except ValueError:
            messagebox.showerror("Error", "Date must be in YYYY-MM-DD format")
            return False

        if email and not re.match(r'^[\w.-]+@[\w.-]+\.\w+$', email):
            messagebox.showerror("Error", "Please enter a valid email address")
            return False
        
        return True

    def check_prices(self):
        if not self.validate_inputs():
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            flights = self.tracker.fetch_flights(
                self.origin_entry.get(),
                self.destination_entry.get(),
                self.date_entry.get(),
                cabin_class=self.class_combo.get(),
                adults=int(self.adults_spin.get())
            )
            
            if not flights:
                messagebox.showinfo("Info", "No flights found")
                return

            for flight in flights:
                self.tree.insert('', 'end', values=(
                    flight['airline'],
                    f"${flight['price']:.2f}",
                    flight['date_checked'],
                    flight['origin'],
                    flight['destination'],
                    flight['departure_date']
                ))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch flights: {str(e)}")

    def set_alert(self):
        if not self.validate_inputs():
            return
        
        if not self.email_entry.get():
            messagebox.showerror("Error", "Email is required for alerts")
            return
        
        self.alert_active = True
        messagebox.showinfo("Success", "Price alert activated! Checking every hour.")
        self.scheduled_check()

    def scheduled_check(self):
        if not self.alert_active:
            return
        
        try:
            current_price, historical_min = self.tracker.check_price_drop(
                self.origin_entry.get(),
                self.destination_entry.get(),
                self.date_entry.get()
            )
            
            if current_price is not None and historical_min is not None:
                message = (
                    f"Price drop detected!\n"
                    f"Route: {self.origin_entry.get()} → {self.destination_entry.get()}\n"
                    f"Date: {self.date_entry.get()}\n"
                    f"New Price: ${current_price:.2f} (Previous min: ${historical_min:.2f})"
                )
                self.tracker.send_email(self.email_entry.get(), message)
                messagebox.showinfo("Price Drop", "Price drop detected! Email sent.")
        
        except Exception as e:
            print(f"Price check failed: {str(e)}")
        
        self.root.after(3600000, self.scheduled_check)  # Check every hour

    def show_plot(self):
        if not self.validate_inputs():
            return

        try:
            data = self.tracker.get_historical_data(
                self.origin_entry.get(),
                self.destination_entry.get()
            )
            
            if data.empty:
                messagebox.showinfo("Info", "No historical data available")
                return

            plot_window = tk.Toplevel(self.root)
            plot_window.title("Price History")
            plot_window.configure(bg='#1a1a1a')
            fig = plt.Figure(figsize=(8, 4), dpi=100)
            ax = fig.add_subplot(111)

            data['date_checked'] = pd.to_datetime(data['date_checked'])
            ax.plot(data['date_checked'], data['price'], marker='o', linestyle='-', color='#00aaff')
            ax.set_title(f"Price History: {self.origin_entry.get()} → {self.destination_entry.get()}", color='#ffffff')
            ax.set_xlabel("Date Checked", color='#ffffff')
            ax.set_ylabel("Price (USD)", color='#ffffff')
            ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
            fig.autofmt_xdate()
            ax.grid(True, linestyle='--', alpha=0.5)
            ax.set_facecolor('#2a2a2a')
            fig.set_facecolor('#1a1a1a')
            ax.tick_params(colors='#ffffff')

            canvas = FigureCanvasTkAgg(fig, master=plot_window)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show plot: {str(e)}")