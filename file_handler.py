import pandas as pd
from datetime import datetime
from tkinter import filedialog

def convert_csv_to_excel(csv_path, excel_path):
    # Load the CSV file
    data = pd.read_csv(csv_path, delimiter=';')

    # Rename columns to match the expected format
    data.rename(columns={
        'Dato': 'Utført dato',
        'Beskrivelse': 'Beskrivelse',
        'Inn': 'Beløp inn',
        'Ut': 'Beløp ut'
    }, inplace=True)

    # Replace commas with dots in the amount columns to handle float conversion
    data['Beløp inn'] = data['Beløp inn'].apply(lambda x: str(x).replace(',', '.') if pd.notnull(x) else x)
    data['Beløp ut'] = data['Beløp ut'].apply(lambda x: str(x).replace(',', '.') if pd.notnull(x) else x)

    # Add any missing columns with default values
    if 'Melding/KID/Fakt.nr' not in data.columns:
        data['Melding/KID/Fakt.nr'] = ''

    # Save the dataframe to an Excel file
    data.to_excel(excel_path, index=False)

def upload_file(db, account_id):
    # Prompt the user to select a file
    file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx;*.xls"), ("CSV files", "*.csv")])
    if not file_path:
        return

    # Check if the file is a CSV and convert it to Excel
    if file_path.endswith('.csv'):
        excel_path = file_path.replace('.csv', '.xlsx')
        convert_csv_to_excel(file_path, excel_path)
        file_path = excel_path

    # Load the Excel file
    data = pd.read_excel(file_path)

    # Initialize an empty list to store the transactions
    transactions = []

    # Iterate over each row in the dataframe
    for index, row in data.iterrows():
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
