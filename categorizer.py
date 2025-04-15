import os
from mistralai import Mistral
import time

def categorize_transactions(db, transactions_to_categorize):
    api_key = os.environ["mistralkey"]
    client = Mistral(api_key=api_key)

    for transaction_id in transactions_to_categorize:
        transaction_id = transaction_id[0]  # Extract the transaction ID from the tuple
        transaction = db.fetch_transaction_by_id(transaction_id)
        if not transaction[5]:  # Check if Kategori is empty
            chat_response = client.agents.complete(
                agent_id="ag:c1167df1:20250306:untitled-agent:c5ef5a85", #Lag din egen agent her! 
                messages=[
                    {
                        "role": "user",
                        "content": str(transaction[3]) + " " + transaction[2],  # Beløp and Beskrivelse
                    },
                ],
            )
            category = chat_response.choices[0].message.content
            if transaction[4] == "Inntekt" and category not in ["Lønn", "Annen inntekt"]:
                category = "Annen inntekt"
                print("Corrected income category from bad agent output")

            db.update_category(transaction_id, category)  # Update the category in the database
            print(f"Categorized transaction ID {transaction_id} as {category}")
            time.sleep(5)  # Pause to avoid overwhelming the API
