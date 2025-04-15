import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.font_manager as fm

class ReportingTab:
    def __init__(self, master, db):
        self.master = master
        self.db = db

        # Create a frame for the reporting tab
        self.reporting_frame = ttk.Frame(master)
        self.reporting_frame.pack(fill='both', expand=True)

        # Search field
        self.search_label = tk.Label(self.reporting_frame, text="Søk:")
        self.search_label.pack(pady=5)

        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(self.reporting_frame, textvariable=self.search_var)
        self.search_entry.pack(pady=5)

        # Account selection
        self.account_label = tk.Label(self.reporting_frame, text="Velg konto:")
        self.account_label.pack(pady=5)

        self.account_var = tk.StringVar()
        self.account_menu = ttk.Combobox(self.reporting_frame, textvariable=self.account_var)
        self.account_menu.pack(pady=5)

        # Date range selection
        self.date_frame = tk.Frame(self.reporting_frame)
        self.date_frame.pack(pady=5)

        self.from_label = tk.Label(self.date_frame, text="Fra:")
        self.from_label.pack(side='left', padx=5)
        self.from_entry = DateEntry(self.date_frame, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd.mm.yyyy')
        self.from_entry.pack(side='left', padx=5)

        self.to_label = tk.Label(self.date_frame, text="Til:")
        self.to_label.pack(side='left', padx=5)
        self.to_entry = DateEntry(self.date_frame, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd.mm.yyyy')
        self.to_entry.pack(side='left', padx=5)

        # Set default dates to the current year
        current_year = datetime.now().year
        self.from_entry.set_date(datetime(current_year, 1, 1))
        self.to_entry.set_date(datetime(current_year, 12, 31))

        # Button to generate the report
        self.generate_button = tk.Button(self.reporting_frame, text="Generer rapport", command=self.generate_report)
        self.generate_button.pack(pady=10)

        # Load accounts
        self.load_accounts()

        # Initialize the Matplotlib figure and canvas
        self.initialize_plot()

    def load_accounts(self):
        accounts = self.db.fetch_all_accounts()
        account_names = [f"{name} ({account_number})" for id, name, account_number, notes in accounts]
        self.account_menu['values'] = account_names
        if account_names:
            self.account_var.set(account_names[0])

    def initialize_plot(self):
        # Set global font properties
        fm.FontProperties(family='DejaVu Sans', size=12)

        # Create a Matplotlib figure with a higher DPI for better readability
        self.figure, self.ax = plt.subplots(dpi=120)  # Set DPI to 120 or adjust as needed
        self.canvas = FigureCanvasTkAgg(self.figure, self.reporting_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

    def generate_report(self):
        search_query = self.search_var.get().strip().lower()
        account = self.account_var.get()
        from_date = self.from_entry.get_date()
        to_date = self.to_entry.get_date()

        if not search_query or not account or not from_date or not to_date:
            messagebox.showwarning("Advarsel", "Vennligst fyll ut alle feltene.")
            return

        account_name, account_number = account.split(" (")
        account_number = account_number.rstrip(")")
        account_id = self.db.get_account_id(account_name, account_number)

        transactions = self.db.fetch_all_transactions(account_id)
        filtered_transactions = []

        for transaction in transactions:
            date = datetime.strptime(transaction[1], "%d.%m.%Y").date()
            if from_date <= date <= to_date and (search_query in transaction[2].lower() or search_query in transaction[5].lower()):
                filtered_transactions.append(transaction)

        if not filtered_transactions:
            messagebox.showinfo("Ingen data", "Ingen transaksjoner funnet for søket.")
            return

        # Prepare data for plotting
        months = {}
        for transaction in filtered_transactions:
            date = datetime.strptime(transaction[1], "%d.%m.%Y")
            month_year = date.strftime("%Y-%m")
            if month_year not in months:
                months[month_year] = 0
            months[month_year] += float(transaction[3])

        # Clear the existing plot
        self.ax.clear()

        # Plot the data
        self.ax.bar(months.keys(), months.values(), color='skyblue')
        self.ax.set_xlabel('Måned', fontsize=12)
        self.ax.set_ylabel('Forbruk', fontsize=12)
        self.ax.set_title(f'Forbruk per måned for "{search_query}"', fontsize=14)
        self.ax.tick_params(axis='x', rotation=45, labelsize=10)
        self.ax.tick_params(axis='y', labelsize=10)

        # Redraw the canvas
        self.canvas.draw()
