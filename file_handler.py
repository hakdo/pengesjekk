import pandas as pd
from datetime import datetime
from tkinter import filedialog

def upload_file(db, account_id):
    # Prompt the user to select an Excel file
    file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx;*.xls")])
    if not file_path:
        return

    # Load the Excel file
    data = pd.read_excel(file_path)

    # Initialize an empty list to store the transactions
    transactions = []

    # Iterate over each row in the dataframe
    for index, row in data.iterrows():
        print(index)
        try:
            # Extract the necessary fields
            dato = row['Utført dato']

            # Check if the date is not null
            if pd.notnull(dato):
                # Ensure the date is in the correct format
                if isinstance(dato, str):
                    try:
                        dato = datetime.strptime(dato, "%Y-%m-%d")
                    except ValueError:
                        dato = datetime.strptime(dato, "%d.%m.%Y")
                beskrivelse = f"{row['Beskrivelse']} {row['Melding/KID/Fakt.nr']}".strip()
                belop_inn = row['Beløp inn']
                belop_ut = row['Beløp ut']

                # Determine the amount and direction
                if pd.notnull(belop_inn):
                    belop = float(belop_inn)
                    retning = "Inntekt"
                elif pd.notnull(belop_ut):
                    belop = float(belop_ut)
                    retning = "Utgift"

                # Create a dictionary for the transaction
                transaction = {
                    "Dato": dato.strftime("%d.%m.%Y"),
                    "Beskrivelse": beskrivelse,
                    "Beløp": belop,
                    "Retning": retning,
                    "Kategori": ""
                }

                # Append the dictionary to the list
                transactions.append(transaction)
            else:
                print(f"Skipped row {index}: Date is null")
        except Exception as e:
            print(f"Error processing row {index}: {e}")

    # Insert transactions into the database for the selected account
    db.insert_transactions(account_id, transactions)
