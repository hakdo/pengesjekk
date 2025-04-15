import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkcalendar import DateEntry
from datetime import datetime
from file_handler import upload_file
from database import Database
from categorizer import categorize_transactions
from budget_tab import BudgetTab  # Import the new BudgetTab module

class TransactionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Bank Transaksjoner")
        self.db = Database()
        self.page_size = 25
        self.current_page = 1
        self.current_account_id = None
        self.all_transactions = []  # Store all fetched transactions

        # Create a notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True)

        # Tab for transactions
        self.transactions_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.transactions_tab, text='Transaksjoner')

        # Tab for budget
        self.budget_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.budget_tab, text='Budsjett')

        # Initialize the transactions tab
        self.init_transactions_tab()

        # Initialize the budget tab using the BudgetTab class
        self.budget_tab_instance = BudgetTab(self.budget_tab, self.db)

        # Load accounts after initializing both tabs
        self.load_accounts()

    def init_transactions_tab(self):
        # Upload button, left-aligned
        self.upload_button = tk.Button(self.transactions_tab, text="Last opp Excel-fil", command=self.handle_upload)
        self.upload_button.pack(anchor='w', pady=10)  # Left-align the button

        # Account selection
        self.account_var = tk.StringVar()
        account_frame = tk.Frame(self.transactions_tab)
        account_frame.pack(fill='x', pady=5)

        account_label = tk.Label(account_frame, text="Velg konto:")
        account_label.pack(side='left', padx=5)

        self.account_menu = ttk.Combobox(account_frame, textvariable=self.account_var)
        self.account_menu.pack(side='left', padx=5)
        self.account_menu.bind("<<ComboboxSelected>>", self.on_account_select)

        self.edit_account_button = tk.Button(account_frame, text="Rediger Konto", command=self.edit_account)
        self.edit_account_button.pack(side='left', padx=5)

        self.add_account_button = tk.Button(account_frame, text="Legg til Konto", command=self.add_account)
        self.add_account_button.pack(side='left', padx=5)

        # Radio buttons for filtering transactions
        self.filter_var = tk.StringVar(value="Alle")
        filter_frame = tk.Frame(self.transactions_tab)
        filter_frame.pack(fill='x', pady=5)

        tk.Radiobutton(filter_frame, text="Alle", variable=self.filter_var, value="Alle", command=self.filter_transactions).pack(side='left')
        tk.Radiobutton(filter_frame, text="Inntekter", variable=self.filter_var, value="Inntekt", command=self.filter_transactions).pack(side='left')
        tk.Radiobutton(filter_frame, text="Utgifter", variable=self.filter_var, value="Utgift", command=self.filter_transactions).pack(side='left')

        # Date range filter, row selection dropdown, and search field
        date_frame = tk.Frame(self.transactions_tab)
        date_frame.pack(fill='x', pady=5)

        self.from_label = tk.Label(date_frame, text="Fra:")
        self.from_label.pack(side='left', padx=5)
        self.from_entry = DateEntry(date_frame, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd.mm.yyyy')
        self.from_entry.pack(side='left', padx=5)

        self.to_label = tk.Label(date_frame, text="Til:")
        self.to_label.pack(side='left', padx=5)
        self.to_entry = DateEntry(date_frame, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd.mm.yyyy')
        self.to_entry.pack(side='left', padx=5)

        # Set default dates only once during initialization
        default_from_date = datetime(datetime.now().year, 1, 1)
        self.from_entry.set_date(default_from_date)
        default_to_date = datetime(datetime.now().year, 12, 31)
        self.to_entry.set_date(default_to_date)

        self.filter_button = tk.Button(date_frame, text="Filtrer", command=self.filter_transactions)
        self.filter_button.pack(side='left', padx=5)

        # Dropdown for selecting number of rows to display
        self.row_var = tk.StringVar(value=str(self.page_size))
        self.row_menu = ttk.Combobox(date_frame, textvariable=self.row_var, values=["10", "25", "50", "All"])
        self.row_menu.pack(side='right', padx=5)
        self.row_menu.bind("<<ComboboxSelected>>", self.on_row_select)

        row_label = tk.Label(date_frame, text="Vis antall rader:")
        row_label.pack(side='right', padx=5)

        # Search field
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(date_frame, textvariable=self.search_var)
        self.search_entry.pack(side='right', padx=5)
        self.search_entry.bind("<Return>", lambda event: self.filter_transactions())

        search_label = tk.Label(date_frame, text="Søk:")
        search_label.pack(side='right', padx=5)

        # Clear search/filter button
        self.clear_button = tk.Button(date_frame, text="Fjern søk/filter", command=self.clear_search_filter)
        self.clear_button.pack(side='right', padx=5)

        # Treeview with scrollbar
        tree_frame = tk.Frame(self.transactions_tab)
        tree_frame.pack(fill='both', expand=True, pady=10)

        self.tree = ttk.Treeview(tree_frame, columns=("ID", "Dato", "Beskrivelse", "Beløp", "Retning", "Kategori"), show="headings", selectmode="extended")
        self.tree.heading("ID", text="ID")  # Include ID column
        self.tree.heading("Dato", text="Dato", command=lambda: self.sort_treeview("Dato", False))
        self.tree.heading("Beskrivelse", text="Beskrivelse", command=lambda: self.sort_treeview("Beskrivelse", False))
        self.tree.heading("Beløp", text="Beløp", command=lambda: self.sort_treeview("Beløp", False))
        self.tree.heading("Retning", text="Retning", command=lambda: self.sort_treeview("Retning", False))
        self.tree.heading("Kategori", text="Kategori", command=lambda: self.sort_treeview("Kategori", False))
        self.tree.pack(side='left', fill='both', expand=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Bind double-click event to open edit window
        self.tree.bind("<Double-1>", self.edit_transaction)

        # Context menu for right-click
        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label="Legg til Kategori", command=self.add_category_to_selected)
        self.tree.bind("<Button-3>", self.show_context_menu)

        # Bind Ctrl+A to select all rows
        self.root.bind("<Control-a>", self.select_all_rows)

        # Pagination controls
        pagination_frame = tk.Frame(self.transactions_tab)
        pagination_frame.pack(fill='x', pady=10)

        self.prev_button = tk.Button(pagination_frame, text="Forrige", command=self.prev_page)
        self.prev_button.pack(side='left', padx=5)

        self.next_button = tk.Button(pagination_frame, text="Neste", command=self.next_page)
        self.next_button.pack(side='left', padx=5)

        self.page_label = tk.Label(pagination_frame, text="Side 1")
        self.page_label.pack(side='left', padx=5)

        # Frame to hold buttons and entries, aligned in a row
        control_frame = tk.Frame(self.transactions_tab)
        control_frame.pack(fill='x', pady=10)

        self.categorize_button = tk.Button(control_frame, text="Kategoriser Transaksjoner", command=self.handle_categorize)
        self.categorize_button.pack(side='left', padx=5)

        self.delete_button = tk.Button(control_frame, text="Slett Transaksjon", command=self.delete_transaction)
        self.delete_button.pack(side='left', padx=5)

        self.analyze_button = tk.Button(control_frame, text="Analyser Transaksjoner", command=self.analyze_transactions)
        self.analyze_button.pack(side='left', padx=5)

        # Status frame
        status_frame = tk.Frame(self.transactions_tab, relief='sunken', borderwidth=1)
        status_frame.pack(side='bottom', fill='x')

        self.status_label = tk.Label(status_frame, text="Status: ", anchor='w')
        self.status_label.pack(fill='x', padx=2, pady=1)

        self.display_transactions()

    def load_accounts(self):
        accounts = self.db.fetch_all_accounts()
        account_names = [f"{name} ({account_number})" for id, name, account_number, notes in accounts]
        self.account_menu['values'] = account_names
        self.budget_tab_instance.budget_account_menu['values'] = account_names
        if accounts:
            self.account_var.set(account_names[0])
            self.budget_tab_instance.budget_account_var.set(account_names[0])
            self.current_account_id = accounts[0][0]
        else:
            self.account_var.set("")
            self.budget_tab_instance.budget_account_var.set("")
            self.current_account_id = None

    def on_account_select(self, event):
        selected_account = self.account_var.get()
        if selected_account:
            account_name, account_number = selected_account.split(" (")
            account_number = account_number.rstrip(")")
            accounts = self.db.fetch_all_accounts()
            for account in accounts:
                if account[1] == account_name and account[2] == account_number:
                    self.current_account_id = account[0]
                    self.current_page = 1  # Reset to the first page when switching accounts
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
        if self.current_account_id is None:
            messagebox.showwarning("Advarsel", "Velg en konto først.")
            return
        upload_file(self.db, self.current_account_id)
        self.display_transactions()

    def handle_categorize(self):
        selected_items = self.tree.selection()
        if selected_items:
            # Categorize only selected transactions
            transactions_to_categorize = [(self.tree.item(item, 'values')[0],) for item in selected_items if not self.tree.item(item, 'values')[5]]
        else:
            # Categorize all uncategorized transactions
            transactions_to_categorize = self.db.fetch_all_transactions(self.current_account_id)
            transactions_to_categorize = [(t[0],) for t in transactions_to_categorize if not t[5]]

        if transactions_to_categorize:
            categorize_transactions(self.db, transactions_to_categorize)
            self.display_transactions()
        else:
            messagebox.showinfo("Ingen Transaksjoner", "Ingen transaksjoner å kategorisere.")

    def filter_transactions(self):
        filter_type = self.filter_var.get()
        from_date = self.from_entry.get_date()
        to_date = self.to_entry.get_date()
        search_query = self.search_var.get().strip().lower()

        # Set default filter to all transactions for the current year if no dates are selected
        if not from_date or not to_date:
            current_year = datetime.now().year
            from_date = datetime(current_year, 1, 1)
            to_date = datetime(current_year, 12, 31)

        transactions = self.db.fetch_all_transactions(self.current_account_id)

        if search_query:
            if search_query.startswith("kat:"):
                transactions = [t for t in transactions if search_query[4:] in t[5].lower()]
            else:
                transactions = [t for t in transactions if search_query in t[2].lower()]

        if from_date and to_date:
            transactions = [t for t in transactions if from_date <= datetime.strptime(t[1], "%d.%m.%Y").date() <= to_date]

        if filter_type != "Alle":
            transactions = [t for t in transactions if t[4] == filter_type]

        # Debugging: Print the number of filtered transactions
        print(f"Filtered transactions count: {len(transactions)}")

        self.all_transactions = transactions  # Store filtered transactions
        self.current_page = 1
        self.update_treeview()

    def display_transactions(self):
        transactions = self.db.fetch_all_transactions(self.current_account_id)
        # Sort transactions by date by default
        transactions.sort(key=lambda x: x[1], reverse=True)
        self.all_transactions = transactions  # Store all transactions
        self.filter_transactions()
        self.current_page = 1
        self.update_treeview()

    def update_treeview(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        start_index = (self.current_page - 1) * self.page_size
        end_index = start_index + self.page_size
        paginated_transactions = self.all_transactions[start_index:end_index]

        for row in paginated_transactions:
            # Ensure the amount is treated as a float
            try:
                amount = float(row[3])
                formatted_amount = f"{amount:.2f}"
            except ValueError:
                formatted_amount = row[3]  # Fallback if conversion fails

            self.tree.insert("", "end", values=(row[0], row[1], row[2], formatted_amount, row[4], row[5]), iid=str(row[0]))  # Include ID in values

        self.page_label.config(text=f"Side {self.current_page}")
        self.prev_button.config(state=tk.NORMAL if self.current_page > 1 else tk.DISABLED)
        self.next_button.config(state=tk.NORMAL if end_index < len(self.all_transactions) else tk.DISABLED)

        # Update status line
        self.update_status_line()

    def update_status_line(self):
        total_income = sum(float(t[3]) for t in self.all_transactions if t[4] == "Inntekt")
        total_expenses = sum(float(t[3]) for t in self.all_transactions if t[4] == "Utgift")
        transaction_count = len(self.all_transactions)
        self.status_label.config(text=f"Status: {transaction_count} transaksjoner, Inntekt: {total_income:.2f}, Utgifter: {total_expenses:.2f}")

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.update_treeview()

    def next_page(self):
        if (self.current_page * self.page_size) < len(self.all_transactions):
            self.current_page += 1
            self.update_treeview()

    def sort_treeview(self, col, reverse):
        # Get the data as a list of tuples
        data = [(self.tree.set(child, col), child) for child in self.tree.get_children('')]

        # Sort the data
        if col == "Dato":
            # Convert the date to a datetime object for sorting
            data.sort(reverse=reverse, key=lambda x: datetime.strptime(x[0], "%d.%m.%Y"))
        elif col == "Beløp":
            # Convert the amount to float for sorting
            data.sort(reverse=reverse, key=lambda x: float(x[0].replace(",", ".")))
        else:
            # Default sorting for other columns
            data.sort(reverse=reverse, key=lambda x: x[0])

        # Rearrange the items in the Treeview
        for index, (val, child) in enumerate(data):
            self.tree.move(child, '', index)

        # Reverse the sorting order for the next click
        self.tree.heading(col, command=lambda: self.sort_treeview(col, not reverse))

    def delete_transaction(self):
        selected_item = self.tree.selection()
        if selected_item:
            transaction_id = self.tree.item(selected_item, 'values')[0]  # Get the ID from the values
            self.db.delete_transaction(transaction_id)
            self.display_transactions()  # Refresh the Treeview
        else:
            messagebox.showwarning("Advarsel", "Velg en transaksjon å slette.")

    def edit_transaction(self, event):
        selected_item = self.tree.selection()
        if selected_item:
            values = self.tree.item(selected_item, 'values')
            transaction_id = values[0]  # Get the ID from the values
            new_category = simpledialog.askstring("Rediger", "Oppdater kategori:", initialvalue=values[5])
            if new_category is not None:
                self.db.update_category(transaction_id, new_category)
                self.display_transactions()  # Refresh the Treeview
        else:
            messagebox.showwarning("Advarsel", "Velg en transaksjon å redigere.")

    def edit_account(self):
        if self.current_account_id is None:
            messagebox.showwarning("Advarsel", "Velg en konto først.")
            return

        account = self.db.fetch_all_accounts()[self.current_account_id - 1]
        account_dialog = simpledialog.askstring("Rediger Konto", "Navn:", initialvalue=account[1])
        if account_dialog is not None:
            account_number = simpledialog.askstring("Rediger Konto", "Kontonummer:", initialvalue=account[2])
            notes = simpledialog.askstring("Rediger Konto", "Notater:", initialvalue=account[3])
            self.db.update_account(self.current_account_id, account_dialog, account_number, notes)
            self.load_accounts()

    def analyze_transactions(self):
        from_date = self.from_entry.get_date()
        to_date = self.to_entry.get_date()
        if not from_date or not to_date:
            messagebox.showwarning("Advarsel", "Velg en gyldig dato-periode.")
            return

        transactions = self.db.fetch_all_transactions(self.current_account_id)
        transactions = [t for t in transactions if from_date <= datetime.strptime(t[1], "%d.%m.%Y").date() <= to_date]

        # Calculate expenses per category
        expense_summary = {}
        total_expenses = 0
        for transaction in transactions:
            if transaction[4] == "Utgift":
                try:
                    amount = float(transaction[3])
                except ValueError:
                    amount = 0  # Fallback if conversion fails
                if transaction[5] in expense_summary:
                    expense_summary[transaction[5]] += amount
                else:
                    expense_summary[transaction[5]] = amount
                total_expenses += amount

        self.all_transactions = transactions  # Store the filtered transactions
        self.current_page = 1
        self.update_treeview()

        # Display the analysis in a new window
        self.show_analysis_report(expense_summary, total_expenses, from_date, to_date)

    def show_analysis_report(self, expense_summary, total_expenses, from_date, to_date):
        report_window = tk.Toplevel(self.root)
        report_window.title(f"Forbruksanalyse ({from_date.strftime('%d.%m.%Y')} - {to_date.strftime('%d.%m.%Y')})")

        report_tree = ttk.Treeview(report_window, columns=("Kategori", "Beløp"), show="headings")
        report_tree.heading("Kategori", text="Kategori", command=lambda: self.sort_analysis_treeview(report_tree, "Beløp", False))
        report_tree.heading("Beløp", text="Beløp", command=lambda: self.sort_analysis_treeview(report_tree, "Beløp", False))
        report_tree.pack(pady=10, padx=10)

        for category, amount in expense_summary.items():
            # Format the amount as currency with two decimal places
            formatted_amount = f"{amount:.2f}"
            report_tree.insert("", "end", values=(category, formatted_amount))

        # Add a "TOTAL" row
        report_tree.insert("", "end", values=("TOTAL", f"{total_expenses:.2f}"))

        close_button = tk.Button(report_window, text="Lukk", command=report_window.destroy)
        close_button.pack(pady=5)

    def sort_analysis_treeview(self, treeview, col, reverse):
        # Get the data as a list of tuples
        data = [(treeview.set(child, col), child) for child in treeview.get_children('')]

        # Sort the data
        if col == "Beløp":
            # Convert the amount to float for sorting
            data.sort(reverse=reverse, key=lambda x: float(x[0].replace(",", ".")))
        else:
            # Default sorting for other columns
            data.sort(reverse=reverse, key=lambda x: x[0])

        # Rearrange the items in the Treeview
        for index, (val, child) in enumerate(data):
            treeview.move(child, '', index)

        # Reverse the sorting order for the next click
        treeview.heading(col, command=lambda: self.sort_analysis_treeview(treeview, col, not reverse))

    def on_row_select(self, event):
        selected_rows = self.row_var.get()
        if selected_rows == "All":
            self.page_size = len(self.all_transactions)
        else:
            self.page_size = int(selected_rows)
        self.current_page = 1  # Reset to the first page
        self.update_treeview()

    def clear_search_filter(self):
        self.search_var.set("")
        self.filter_var.set("Alle")
        self.display_transactions()

    def show_context_menu(self, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def add_category_to_selected(self):
        selected_items = self.tree.selection()
        if selected_items:
            new_category = simpledialog.askstring("Legg til Kategori", "Kategori:")
            if new_category:
                for item in selected_items:
                    transaction_id = self.tree.item(item, 'values')[0]
                    self.db.update_category(transaction_id, new_category)
                self.display_transactions()
        else:
            messagebox.showwarning("Advarsel", "Velg minst en transaksjon.")

    def select_all_rows(self, event):
        self.tree.selection_set(self.tree.get_children())
