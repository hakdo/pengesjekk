import sqlite3
import hashlib
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class Database:
    def __init__(self, db_name='transactions.db'):
        self.conn = sqlite3.connect(db_name)
        self.create_tables()
        logging.debug("Database initialized and tables created.")

    def create_tables(self):
        with self.conn:
            self.conn.execute('''CREATE TABLE IF NOT EXISTS accounts (
                                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                                 name TEXT NOT NULL,
                                 account_number TEXT,
                                 notes TEXT)''')
            self.conn.execute('''CREATE TABLE IF NOT EXISTS transactions (
                                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                                 account_id INTEGER,
                                 Dato TEXT,
                                 Beskrivelse TEXT,
                                 Beløp REAL,
                                 Retning TEXT,
                                 Kategori TEXT,
                                 hash TEXT,
                                 FOREIGN KEY (account_id) REFERENCES accounts (id))''')

            # Create a default account if none exists
            if not self.fetch_all_accounts():
                self.insert_account("Standardkonto", "", "")
                logging.debug("Default account created.")

            # Create budget table if it doesn't exist
            self.conn.execute('''CREATE TABLE IF NOT EXISTS budget (
                                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                                 account_id INTEGER,
                                 budget_name TEXT,
                                 category TEXT,
                                 budget_amount REAL,
                                 actual_amount REAL,
                                 FOREIGN KEY (account_id) REFERENCES accounts (id))''')

    def insert_account(self, name, account_number, notes):
        with self.conn:
            self.conn.execute("INSERT INTO accounts (name, account_number, notes) VALUES (?, ?, ?)", (name, account_number, notes))
            logging.debug(f"Account inserted: {name}, {account_number}")

    def fetch_all_accounts(self):
        with self.conn:
            cursor = self.conn.execute("SELECT id, name, account_number, notes FROM accounts")
            accounts = cursor.fetchall()
            logging.debug(f"Fetched {len(accounts)} accounts.")
            return accounts

    def update_account(self, account_id, name, account_number, notes):
        with self.conn:
            self.conn.execute("UPDATE accounts SET name = ?, account_number = ?, notes = ? WHERE id = ?", (name, account_number, notes, account_id))
            logging.debug(f"Account updated: {account_id}, {name}")

    def delete_account(self, account_id):
        with self.conn:
            self.conn.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
            logging.debug(f"Account deleted: {account_id}")

    def insert_transactions(self, account_id, transactions):
        with self.conn:
            for transaction in transactions:
                # Calculate the MD5 hash of the description field
                description_hash = hashlib.md5((str(transaction["Dato"])+transaction["Beskrivelse"]+str(transaction["Beløp"])).encode()).hexdigest()
                # Check if the transaction already exists
                cursor = self.conn.execute("SELECT id FROM transactions WHERE hash = ?", (description_hash,))
                existing_transaction = cursor.fetchone()
                if not existing_transaction:
                    self.conn.execute("INSERT INTO transactions (account_id, Dato, Beskrivelse, Beløp, Retning, Kategori, hash) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                       (account_id, transaction["Dato"], transaction["Beskrivelse"], float(transaction["Beløp"]), transaction["Retning"], transaction["Kategori"], description_hash))
                    #logging.debug(f"Transaction inserted: {transaction}")
                else:
                    logging.debug(f"Transaction skipped (already exists): {transaction}")

    def fetch_all_transactions(self, account_id=None):
        with self.conn:
            if account_id:
                cursor = self.conn.execute("SELECT id, Dato, Beskrivelse, Beløp, Retning, Kategori FROM transactions WHERE account_id = ?", (account_id,))
            else:
                cursor = self.conn.execute("SELECT id, Dato, Beskrivelse, Beløp, Retning, Kategori FROM transactions")
            transactions = cursor.fetchall()
            logging.debug(f"Fetched {len(transactions)} transactions.")
            return transactions

    def fetch_transaction_by_id(self, transaction_id):
        with self.conn:
            cursor = self.conn.execute("SELECT id, Dato, Beskrivelse, Beløp, Retning, Kategori FROM transactions WHERE id = ?", (transaction_id,))
            transaction = cursor.fetchone()
            logging.debug(f"Fetched transaction by ID: {transaction_id}")
            return transaction

    def update_category(self, transaction_id, category):
        with self.conn:
            self.conn.execute("UPDATE transactions SET Kategori = ? WHERE id = ?", (category, transaction_id))
            logging.debug(f"Category updated for transaction ID: {transaction_id}")

    def delete_transaction(self, transaction_id):
        with self.conn:
            self.conn.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
            logging.debug(f"Transaction deleted: {transaction_id}")

    def filter_transactions(self, month=None, category=None, account_id=None):
        query = "SELECT id, Dato, Beskrivelse, Beløp, Retning, Kategori FROM transactions WHERE 1=1"
        params = []
        if account_id:
            query += " AND account_id = ?"
            params.append(account_id)
        if month:
            query += " AND strftime('%m', Dato) = ?"
            params.append(month)
        if category:
            query += " AND Kategori = ?"
            params.append(category)
        with self.conn:
            cursor = self.conn.execute(query, params)
            transactions = cursor.fetchall()
            logging.debug(f"Filtered transactions: {len(transactions)} results.")
            return transactions

    def bulk_update_categories(self, transaction_ids, category):
        """
        Update the category for multiple transactions at once.

        :param transaction_ids: List of transaction IDs to update.
        :param category: The new category to assign to the transactions.
        """
        with self.conn:
            for transaction_id in transaction_ids:
                self.conn.execute("UPDATE transactions SET Kategori = ? WHERE id = ?", (category, transaction_id))
                logging.debug(f"Category updated for transaction ID: {transaction_id}")

    def save_budget(self, account_id, budget_data, budget_name):
        """
        Save the budget data to the database.

        :param account_id: The ID of the account.
        :param budget_data: List of tuples containing (category, budget_amount, actual_amount).
        :param budget_name: The name of the budget.
        """
        with self.conn:
            # Delete existing budget entries for the account and budget name
            self.conn.execute("DELETE FROM budget WHERE account_id = ? AND budget_name = ?", (account_id, budget_name))
            # Insert new budget entries
            for category, budget_amount, actual_amount in budget_data:
                self.conn.execute("INSERT INTO budget (account_id, budget_name, category, budget_amount, actual_amount) VALUES (?, ?, ?, ?, ?)",
                                  (account_id, budget_name, category, budget_amount, actual_amount))
            logging.debug(f"Budget saved for account ID: {account_id}, Budget Name: {budget_name}")

    def fetch_budgets(self, account_id):
        """
        Fetch all budgets for a given account.

        :param account_id: The ID of the account.
        :return: A list of tuples containing (budget_name, budget_data), where budget_data is a list of tuples (category, budget_amount, actual_amount).
        """
        with self.conn:
            cursor = self.conn.execute("SELECT DISTINCT budget_name FROM budget WHERE account_id = ?", (account_id,))
            budget_names = cursor.fetchall()
            budgets = {}
            for (budget_name,) in budget_names:
                cursor = self.conn.execute("SELECT category, budget_amount, actual_amount FROM budget WHERE account_id = ? AND budget_name = ?", (account_id, budget_name))
                budget_data = cursor.fetchall()
                budgets[budget_name] = budget_data
            logging.debug(f"Fetched budgets for account ID: {account_id}")
            return list(budgets.items())

    def get_account_id(self, account_name, account_number):
        # Fetch the account ID based on account name and number
        accounts = self.fetch_all_accounts()
        for account in accounts:
            if account[1] == account_name and account[2] == account_number:
                return account[0]  # Return the account ID
        return None  # Return None if no matching account is found