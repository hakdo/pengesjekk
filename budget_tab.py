import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkcalendar import DateEntry
from datetime import datetime

class BudgetTab:
    def __init__(self, parent, db):
        self.parent = parent
        self.db = db
        self.current_account_id = None
        self.budgets = {}

        # Account selection
        self.budget_account_var = tk.StringVar()
        account_frame = tk.Frame(self.parent)
        account_frame.pack(fill='x', pady=5)

        account_label = tk.Label(account_frame, text="Velg konto:")
        account_label.pack(side='left', padx=5)

        self.budget_account_menu = ttk.Combobox(account_frame, textvariable=self.budget_account_var)
        self.budget_account_menu.pack(side='left', padx=5)
        self.budget_account_menu.bind("<<ComboboxSelected>>", self.on_budget_account_select)

        # Budget selection
        self.budget_name_var = tk.StringVar()
        budget_name_frame = tk.Frame(self.parent)
        budget_name_frame.pack(fill='x', pady=5)

        budget_name_label = tk.Label(budget_name_frame, text="Velg budsjett:")
        budget_name_label.pack(side='left', padx=5)

        self.budget_name_menu = ttk.Combobox(budget_name_frame, textvariable=self.budget_name_var)
        self.budget_name_menu.pack(side='left', padx=5)
        self.budget_name_menu.bind("<<ComboboxSelected>>", self.on_budget_name_select)

        self.save_budget_button = tk.Button(budget_name_frame, text="Lagre Budsjett", command=self.save_budget)
        self.save_budget_button.pack(side='left', padx=5)

        self.new_budget_button = tk.Button(budget_name_frame, text="Nytt Budsjett", command=self.new_budget)
        self.new_budget_button.pack(side='left', padx=5)

        # Date range filter
        date_frame = tk.Frame(self.parent)
        date_frame.pack(fill='x', pady=5)

        self.budget_from_label = tk.Label(date_frame, text="Fra:")
        self.budget_from_label.pack(side='left', padx=5)
        self.budget_from_entry = DateEntry(date_frame, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd.mm.yyyy')
        self.budget_from_entry.pack(side='left', padx=5)

        self.budget_to_label = tk.Label(date_frame, text="Til:")
        self.budget_to_label.pack(side='left', padx=5)
        self.budget_to_entry = DateEntry(date_frame, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd.mm.yyyy')
        self.budget_to_entry.pack(side='left', padx=5)

        # Set default dates only once during initialization
        default_from_date = datetime(datetime.now().year, 1, 1)
        self.budget_from_entry.set_date(default_from_date)
        default_to_date = datetime(datetime.now().year, 12, 31)
        self.budget_to_entry.set_date(default_to_date)

        self.generate_budget_button = tk.Button(date_frame, text="Generer Budsjett", command=self.generate_budget)
        self.generate_budget_button.pack(side='left', padx=5)

        # Treeview for budget
        budget_tree_frame = tk.Frame(self.parent)
        budget_tree_frame.pack(fill='both', expand=True, pady=10)

        self.budget_tree = ttk.Treeview(budget_tree_frame, columns=("Kategori", "Inntekt", "Utgift"), show="headings")
        self.budget_tree.heading("Kategori", text="Kategori")
        self.budget_tree.heading("Inntekt", text="Inntekt")
        self.budget_tree.heading("Utgift", text="Utgift")
        self.budget_tree.pack(side='left', fill='both', expand=True)
        self.budget_tree.bind("<Double-1>", self.edit_budget_line)

        budget_scrollbar = ttk.Scrollbar(budget_tree_frame, orient="vertical", command=self.budget_tree.yview)
        budget_scrollbar.pack(side='right', fill='y')
        self.budget_tree.configure(yscrollcommand=budget_scrollbar.set)

        # Add and delete buttons
        button_frame = tk.Frame(self.parent)
        button_frame.pack(fill='x', pady=5)

        self.add_budget_line_button = tk.Button(button_frame, text="Legg til Budsjettlinje", command=self.add_budget_line)
        self.add_budget_line_button.pack(side='left', padx=5)

        self.delete_budget_line_button = tk.Button(button_frame, text="Slett Budsjettlinje", command=self.delete_budget_line)
        self.delete_budget_line_button.pack(side='left', padx=5)

        # Status frame
        status_frame = tk.Frame(self.parent, relief='sunken', borderwidth=1)
        status_frame.pack(side='bottom', fill='x')

        self.status_label = tk.Label(status_frame, text="Status: ", anchor='w')
        self.status_label.pack(fill='x', padx=2, pady=1)

        # Load accounts and budgets
        self.load_accounts()

    def load_accounts(self):
        accounts = self.db.fetch_all_accounts()
        account_names = [f"{name} ({account_number})" for id, name, account_number, notes in accounts]
        self.budget_account_menu['values'] = account_names
        if accounts:
            self.budget_account_var.set(account_names[0])
            self.current_account_id = accounts[0][0]
            self.load_budgets()
        else:
            self.budget_account_var.set("")
            self.current_account_id = None

    def load_budgets(self):
        budgets = self.db.fetch_budgets(self.current_account_id)
        self.budgets = {name: data for name, data in budgets}
        self.budget_name_menu['values'] = list(self.budgets.keys())
        if self.budgets:
            self.budget_name_var.set(list(self.budgets.keys())[0])
            self.load_budget(list(self.budgets.keys())[0])

    def on_budget_account_select(self, event):
        selected_account = self.budget_account_var.get()
        if selected_account:
            account_name, account_number = selected_account.split(" (")
            account_number = account_number.rstrip(")")
            accounts = self.db.fetch_all_accounts()
            for account in accounts:
                if account[1] == account_name and account[2] == account_number:
                    self.current_account_id = account[0]
                    self.load_budgets()
                    break

    def on_budget_name_select(self, event):
        selected_budget = self.budget_name_var.get()
        if selected_budget in self.budgets:
            self.load_budget(selected_budget)
            self.update_status_label()

    def new_budget(self):
        budget_name = simpledialog.askstring("Nytt Budsjett", "Navn på det nye budsjettet:")
        if budget_name:
            self.budgets[budget_name] = []
            self.budget_name_menu['values'] = list(self.budgets.keys())
            self.budget_name_var.set(budget_name)
            self.load_budget(budget_name)
            self.update_status_label()

    def load_budget(self, budget_name):
        for row in self.budget_tree.get_children():
            self.budget_tree.delete(row)
        for category, income_amount, expense_amount in self.budgets[budget_name]:
            self.budget_tree.insert("", "end", values=(category, f"{income_amount:.2f}", f"{expense_amount:.2f}"))
        self.update_total_row()

    def generate_budget(self):
        from_date = self.budget_from_entry.get_date()
        to_date = self.budget_to_entry.get_date()
        if not from_date or not to_date:
            messagebox.showwarning("Advarsel", "Velg en gyldig dato-periode.")
            return

        transactions = self.db.fetch_all_transactions(self.current_account_id)
        transactions = [t for t in transactions if from_date <= datetime.strptime(t[1], "%d.%m.%Y").date() <= to_date]

        # Calculate income and expenses per category
        income_summary = {}
        expense_summary = {}
        total_income = 0
        total_expenses = 0
        for transaction in transactions:
            try:
                amount = float(transaction[3])
            except ValueError:
                amount = 0  # Fallback if conversion fails
            if transaction[4] == "Inntekt":
                if transaction[5] in income_summary:
                    income_summary[transaction[5]] += amount
                else:
                    income_summary[transaction[5]] = amount
                total_income += amount
            elif transaction[4] == "Utgift":
                if transaction[5] in expense_summary:
                    expense_summary[transaction[5]] += amount
                else:
                    expense_summary[transaction[5]] = amount
                total_expenses += amount

        # Clear the treeview
        for row in self.budget_tree.get_children():
            self.budget_tree.delete(row)

        # Insert income and expense data into the correct columns
        for category, amount in income_summary.items():
            self.budget_tree.insert("", "end", values=(category, f"{amount:.2f}", ""))

        for category, amount in expense_summary.items():
            self.budget_tree.insert("", "end", values=(category, "", f"{-amount:.2f}"))

        self.update_total_row()
        self.update_status_label()

    def save_budget(self):
        budget_name = self.budget_name_var.get()
        if not budget_name:
            messagebox.showwarning("Advarsel", "Velg eller opprett et budsjett først.")
            return

        budget_data = []
        for item in self.budget_tree.get_children():
            values = self.budget_tree.item(item, 'values')
            category = values[0]
            income_amount = float(values[1]) if values[1] else 0.0
            expense_amount = float(values[2]) if values[2] else 0.0
            budget_data.append((category, income_amount, expense_amount))

        self.budgets[budget_name] = budget_data
        self.db.save_budget(self.current_account_id, budget_data, budget_name)
        messagebox.showinfo("Budsjett Lagret", "Budsjettet har blitt lagret.")

    def edit_budget_line(self, event):
        selected_item = self.budget_tree.selection()[0]
        values = self.budget_tree.item(selected_item, 'values')
        category = values[0]
        amount = simpledialog.askfloat("Rediger Budsjettlinje", f"Nytt beløp for {category}:", initialvalue=float(values[1]) if values[1] else 0.0)

        if amount is not None:
            if amount < 0:
                self.budget_tree.item(selected_item, values=(category, "", f"{abs(amount):.2f}"))
            else:
                self.budget_tree.item(selected_item, values=(category, f"{amount:.2f}", ""))

            self.update_total_row()
            self.update_status_label()

    def add_budget_line(self):
        category = simpledialog.askstring("Legg til Budsjettlinje", "Kategori:")
        amount = simpledialog.askfloat("Legg til Budsjettlinje", f"Beløp for {category}:")

        if category and amount is not None:
            if amount < 0:
                self.budget_tree.insert("", "end", values=(category, "", f"{abs(amount):.2f}"))
            else:
                self.budget_tree.insert("", "end", values=(category, f"{amount:.2f}", ""))

            self.update_total_row()
            self.update_status_label()

    def delete_budget_line(self):
        selected_item = self.budget_tree.selection()
        if selected_item:
            self.budget_tree.delete(selected_item)
            self.update_total_row()
            self.update_status_label()

    def update_total_row(self):

        # Remove any existing "TOTAL" row
        for item in self.budget_tree.get_children():
            if self.budget_tree.item(item, 'values')[0] == "TOTAL":
                self.budget_tree.delete(item)
        
        total_income = 0
        total_expenses = 0
        
        for item in self.budget_tree.get_children():
            values = self.budget_tree.item(item, 'values')
            income = float(values[1]) if values[1] else 0.0
            expense = float(values[2]) if values[2] else 0.0
            total_income += income
            total_expenses += expense


        # Insert the updated "TOTAL" row
        self.budget_tree.insert("", "end", values=("TOTAL", f"{total_income:.2f}", f"{total_expenses:.2f}"))

    def update_status_label(self):
        budget_name = self.budget_name_var.get()
        total_income = 0
        total_expenses = 0

        # Find the "TOTAL" row in the treeview
        for item in self.budget_tree.get_children():
            values = self.budget_tree.item(item, 'values')
            if values[0] == "TOTAL":
                total_income = float(values[1]) if values[1] else 0.0
                total_expenses = float(values[2]) if values[2] else 0.0
                break

        balance = total_income - total_expenses  # Since expenses are negative in the treeview
        self.status_label.config(text=f"Budsjett: {budget_name}, Balanse: {balance:.2f}")
