import sqlite3
def initialize_database():
    # This automatically creates a file named economy.db
    conn = sqlite3.connect("economy.db")
    cursor = conn.cursor()

    # Read and execute schema.sql
    with open("schema.sql", "r") as f:
        cursor.executescript(f.read())

    # Read and execute seed.sql
    with open("seed.sql", "r") as f:
        cursor.executescript(f.read())

    conn.commit()
    conn.close()
    print("Success: economy.db created and seeded with 1,000,000 fixed tokens!")

if __name__ == "__main__":
    initialize_database()