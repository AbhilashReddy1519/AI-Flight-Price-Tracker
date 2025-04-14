import tkinter as tk
from ui import FlightTrackerUI

if __name__ == "__main__":
    root = tk.Tk()
    app = FlightTrackerUI(root)
    root.configure(bg='#1a1a1a')
    root.mainloop()