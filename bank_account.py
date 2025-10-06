import sqlite3

bank_database = sqlite3.connect("bank.db")
bank_cursor = bank_database.cursor()
bank_cursor.execute("DROP TABLE IF EXISTS account")
bank_database.commit()
bank_cursor.execute("CREATE TABLE IF NOT EXISTS account(tc_id INTEGER PRIMARY KEY,name UNIQUE, amount_of_money REAL)")
bank_cursor.execute("DROP TABLE IF EXISTS transactions")
bank_cursor.execute("CREATE TABLE IF NOT EXISTS transactions(account_id INTEGER NOT NULL, transaction_amount TEXT NOT NULL, date TEXT NOT NULL, transaction_name TEXT NOT NULL,FOREIGN KEY (account_id) REFERENCES account(tc_id))")
bank_database.commit()
bank_database.close()





