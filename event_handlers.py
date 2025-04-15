import tkinter as tk
from tkinter import messagebox, simpledialog
from datetime import datetime
from file_handler import upload_file
from categorizer import categorize_transactions

class EventHandler:
    def __init__(self, app, db):
        self.app = app
        self.db = db

    def load_accounts(self):
        accounts = self.db.fetch_all_accounts()
        account_names = [f"{name} ({account_number})" for id, name, account_number, notes in accounts]
        self.app.account_menu['values'] = account_names
        if accounts:
            self.app.account_var.set(account_names[0])
            self.app.current_account_id = accounts[0][0]
        else:
            self.app.account_var.set("")
            self.app.current_account_id = None

    def on_account_select(self, event):
        selected_account = self.app.account_var.get()
        if selected_account:
            account_name, account_number = selected_account.split(" (")
            account_number = account_number.rstrip(")")
            accounts = self.db.fetch_all_accounts()
            for account in accounts:
                if account[1] == account_name and account[2] == account_number:
                    self.app.current_account_id = account[0]
                    self.app.current_page = 1
                    self.display_transactions()
                    break

    def add_account(self):
        account_name = simpledialog.askstring("Legg til Konto", "Navn:")
        if account_name:
            account_number = simpledialog.askstring("Legg til Konto", "Kontonummer:")
            notes = simpledialog.askstring("Legg til Konto", "Notater:")
            self.db.insert_account(account_name, account_number, notes)
            self.load_accounts()

    def handle_upload(self):
        if self.app.current_account_id is None:
            messagebox.showwarning("Advarsel", "Velg en konto først.")
            return
        upload_file(self.db, self.app.current_account_id)
        self.display_transactions()

    def handle_categorize(self):
        selected_items = self.app.tree.selection()
        if selected_items:
            transactions_to_categorize = [(self.app.tree.item(item, 'values')[0],) for item in selected_items if not self.app.tree.item(item, 'values')[5]]
        else:
            transactions_to_categorize = self.db.fetch_all_transactions(self.app.current_account_id)
            transactions_to_categorize = [(t[0],) for t in transactions_to_categorize if not t[5]]

        if transactions_to_categorize:
            categorize_transactions(self.db, transactions_to_categorize)
            self.display_transactions()
        else:
            messagebox.showinfo("Ingen Transaksjoner", "Ingen transaksjoner å kategorisere.")

    def filter_transactions(self):
        filter_type = self.app.filter_var.get()
        from_date = self.app.from_entry.get_date()
        to_date = self.app.to_entry.get_date()
        search_query = self.app.search_var.get().strip().lower()

        if not from_date or not to_date:
            current_year = datetime.now().year
            from_date = datetime(current_year, 1, 1)
            to_date = datetime(current_year, 12, 31)

        transactions = self.db.fetch_all_transactions(self.app.current_account_id)

        if search_query:
            transactions = self.apply_search_filter(transactions, search_query)

        transactions = self.apply_date_filter(transactions, from_date, to_date)
        transactions = self.apply_type_filter(transactions, filter_type)

        self.app.all_transactions = transactions
        self.app.current_page = 1
        self.update_treeview()

    def apply_search_filter(self, transactions, search_query):
        if search_query.startswith("kat:"):
            return [t for t in transactions if search_query[4:] in t[5].lower()]
        else:
            return [t for t in transactions if search_query in t[2].lower()]

    def apply_date_filter(self, transactions, from_date, to_date):
        return [t for t in transactions if from_date <= datetime.strptime(t[1], "%d.%m.%Y").date() <= to_date]

    def apply_type_filter(self, transactions, filter_type):
        if filter_type != "Alle":
            return [t for t in transactions if t[4] == filter_type]
        return transactions

    def display_transactions(self):
        transactions = self.db.fetch_all_transactions(self.app.current_account_id)
        transactions.sort(key=lambda x: x[1], reverse=True)
        self.app.all_transactions = transactions
        self.app.current_page = 1
        self.update_treeview()

    def update_treeview(self):
        self.clear_treeview()
        paginated_transactions = self.get_paginated_transactions()
        self.populate_treeview(paginated_transactions)
        self.update_pagination_controls()
        self.update_status_line()

    def clear_treeview(self):
        for row in self.app.tree.get_children():
            self.app.tree.delete(row)

    def get_paginated_transactions(self):
        start_index = (self.app.current_page - 1) * self.app.page_size
        end_index = start_index + self.app.page_size
        return self.app.all_transactions[start_index:end_index]

    def populate_treeview(self, transactions):
        for row in transactions:
            amount = self.format_amount(row[3])
            self.app.tree.insert("", "end", values=(row[0], row[1], row[2], amount, row[4], row[5]), iid=str(row[0]))

    def format_amount(self, amount):
        try:
            return f"{float(amount):.2f}"
        except ValueError:
            return amount

    def update_pagination_controls(self):
        self.app.page_label.config(text=f"Side {self.app.current_page}")
        self.app.prev_button.config(state=tk.NORMAL if self.app.current_page > 1 else tk.DISABLED)
        self.app.next_button.config(state=tk.NORMAL if self.app.current_page * self.app.page_size < len(self.app.all_transactions) else tk.DISABLED)

    def update_status_line(self):
        total_income = sum(float(t[3]) for t in self.app.all_transactions if t[4] == "Inntekt")
        total_expenses = sum(float(t[3]) for t in self.app.all_transactions if t[4] == "Utgift")
        transaction_count = len(self.app.all_transactions)
        self.app.status_label.config(text=f"Status: {transaction_count} transaksjoner, Inntekt: {total_income:.2f}, Utgifter: {total_expenses:.2f}")

    def prev_page(self):
        if self.app.current_page > 1:
            self.app.current_page -= 1
            self.update_treeview()

    def next_page(self):
        if (self.app.current_page * self.app.page_size) < len(self.app.all_transactions):
            self.app.current_page += 1
            self.update_treeview()

    def sort_treeview(self, col, reverse):
        data = [(self.app.tree.set(child, col), child) for child in self.app.tree.get_children('')]
        data.sort(reverse=reverse, key=lambda x: x[0])
        for index, (val, child) in enumerate(data):
            self.app.tree.move(child, '', index)
        self.app.tree.heading(col, command=lambda: self.sort_treeview(col, not reverse))

    def delete_transaction(self):
        selected_item = self.app.tree.selection()
        if selected_item:
            transaction_id = self.app.tree.item(selected_item, 'values')[0]
            self.db.delete_transaction(transaction_id)
            self.display_transactions()
        else:
            messagebox.showwarning("Advarsel", "Velg en transaksjon å slette.")

    def edit_transaction(self, event):
        selected_item = self.app.tree.selection()
        if selected_item:
            values = self.app.tree.item(selected_item, 'values')
            transaction_id = values[0]
            new_category = simpledialog.askstring("Rediger", "Oppdater kategori:", initialvalue=values[5])
            if new_category is not None:
                self.db.update_category(transaction_id, new_category)
                self.display_transactions()
        else:
            messagebox.showwarning("Advarsel", "Velg en transaksjon å redigere.")

    def edit_account(self):
        if self.app.current_account_id is None:
            messagebox.showwarning("Advarsel", "Velg en konto først.")
            return

        account = self.db.fetch_all_accounts()[self.app.current_account_id - 1]
        account_dialog = simpledialog.askstring("Rediger Konto", "Navn:", initialvalue=account[1])
        if account_dialog is not None:
            account_number = simpledialog.askstring("Rediger Konto", "Kontonummer:", initialvalue=account[2])
            notes = simpledialog.askstring("Rediger Konto", "Notater:", initialvalue=account[3])
            self.db.update_account(self.app.current_account_id, account_dialog, account_number, notes)
            self.load_accounts()

    def analyze_transactions(self):
        from_date = self.app.from_entry.get_date()
        to_date = self.app.to_entry.get_date()
        if not from_date or not to_date:
            messagebox.showwarning("Advarsel", "Velg en gyldig dato-periode.")
            return

        transactions = self.db.fetch_all_transactions(self.app.current_account_id)
        transactions = [t for t in transactions if from_date <= datetime.strptime(t[1], "%d.%m.%Y").date() <= to_date]

        expense_summary = self.calculate_expense_summary(transactions)
        total_expenses = sum(expense_summary.values())

        self.app.all_transactions = transactions
        self.app.current_page = 1
        self.update_treeview()

        self.show_analysis_report(expense_summary, total_expenses, from_date, to_date)

    def calculate_expense_summary(self, transactions):
        expense_summary = {}
        for transaction in transactions:
            if transaction[4] == "Utgift":
                amount = self.get_transaction_amount(transaction)
                if transaction[5] in expense_summary:
                    expense_summary[transaction[5]] += amount
                else:
                    expense_summary[transaction[5]] = amount
        return expense_summary

    def get_transaction_amount(self, transaction):
        try:
            return float(transaction[3])
        except ValueError:
            return 0

    def show_analysis_report(self, expense_summary, total_expenses, from_date, to_date):
        report_window = tk.Toplevel(self.app.root)
        report_window.title(f"Forbruksanalyse ({from_date.strftime('%d.%m.%Y')} - {to_date.strftime('%d.%m.%Y')})")

        report_tree = ttk.Treeview(report_window, columns=("Kategori", "Beløp"), show="headings")
        report_tree.heading("Kategori", text="Kategori")
        report_tree.heading("Beløp", text="Beløp")
        report_tree.pack(pady=10, padx=10)

        for category, amount in expense_summary.items():
            formatted_amount = f"{amount:.2f}"
            report_tree.insert("", "end", values=(category, formatted_amount))

        report_tree.insert("", "end", values=("TOTAL", f"{total_expenses:.2f}"))

        close_button = tk.Button(report_window, text="Lukk", command=report_window.destroy)
        close_button.pack(pady=5)

    def on_row_select(self, event):
        selected_rows = self.app.row_var.get()
        if selected_rows == "All":
            self.app.page_size = len(self.app.all_transactions)
        else:
            self.app.page_size = int(selected_rows)
        self.app.current_page = 1
        self.update_treeview()

    def clear_search_filter(self):
        self.app.search_var.set("")
        self.app.filter_var.set("Alle")
        self.display_transactions()

    def show_context_menu(self, event):
        try:
            self.app.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.app.context_menu.grab_release()

    def add_category_to_selected(self):
        selected_items = self.app.tree.selection()
        if selected_items:
            new_category = simpledialog.askstring("Legg til Kategori", "Kategori:")
            if new_category:
                for item in selected_items:
                    transaction_id = self.app.tree.item(item, 'values')[0]
                    self.db.update_category(transaction_id, new_category)
                self.display_transactions()
        else:
            messagebox.showwarning("Advarsel", "Velg minst en transaksjon.")

    def select_all_rows(self, event):
        self.app.tree.selection_set(self.app.tree.get_children())

    def set_default_dates(self):
        default_from_date = datetime(datetime.now().year, 1, 1)
        self.app.from_entry.set_date(default_from_date)
        default_to_date = datetime(datetime.now().year, 12, 31)
        self.app.to_entry.set_date(default_to_date)
