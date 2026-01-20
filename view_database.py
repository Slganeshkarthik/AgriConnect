"""
Database Viewer Utility for AgriConnect
Run this script to view all tables and data in user_database.db
"""

import sqlite3
import os

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'user_database.db')

def get_all_tables():
    """Get list of all tables in the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables

def get_table_schema(table_name):
    """Get column info for a table"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    conn.close()
    return columns

def get_table_data(table_name, limit=50):
    """Get all data from a table"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
    rows = cursor.fetchall()
    conn.close()
    return rows

def print_table(table_name):
    """Print table schema and data"""
    print(f"\n{'='*60}")
    print(f"📊 TABLE: {table_name}")
    print('='*60)
    
    # Schema
    columns = get_table_schema(table_name)
    col_names = [col[1] for col in columns]
    print(f"Columns: {', '.join(col_names)}")
    print('-'*60)
    
    # Data
    rows = get_table_data(table_name)
    if not rows:
        print("(No data)")
    else:
        print(f"Found {len(rows)} rows:\n")
        for i, row in enumerate(rows, 1):
            print(f"[{i}] ", end="")
            row_dict = dict(row)
            for key, value in row_dict.items():
                # Truncate long values
                str_val = str(value) if value is not None else "NULL"
                if len(str_val) > 50:
                    str_val = str_val[:50] + "..."
                print(f"{key}={str_val} | ", end="")
            print()

def view_specific_table(table_name):
    """View a specific table"""
    tables = get_all_tables()
    if table_name not in tables:
        print(f"❌ Table '{table_name}' not found!")
        print(f"Available tables: {', '.join(tables)}")
        return
    print_table(table_name)

def view_all_tables():
    """View all tables in the database"""
    tables = get_all_tables()
    print(f"\n🗄️  DATABASE: {DB_PATH}")
    print(f"📋 Found {len(tables)} tables: {', '.join(tables)}\n")
    for table in tables:
        print_table(table)

def interactive_menu():
    """Interactive menu to browse database"""
    while True:
        print("\n" + "="*40)
        print("🌾 AgriConnect Database Viewer")
        print("="*40)
        print("1. View all tables")
        print("2. View specific table")
        print("3. View users")
        print("4. View orders")
        print("5. View feedback")
        print("6. View products (farmers)")
        print("7. Run custom SQL query")
        print("0. Exit")
        print("-"*40)
        
        choice = input("Enter choice: ").strip()
        
        if choice == '0':
            print("Goodbye! 👋")
            break
        elif choice == '1':
            view_all_tables()
        elif choice == '2':
            tables = get_all_tables()
            print(f"Available tables: {', '.join(tables)}")
            table = input("Enter table name: ").strip()
            view_specific_table(table)
        elif choice == '3':
            view_specific_table('users')
            view_specific_table('user_details')
        elif choice == '4':
            view_specific_table('orders')
            view_specific_table('order_items')
        elif choice == '5':
            view_specific_table('customer_feedback')
        elif choice == '6':
            view_specific_table('farmer_order_notifications')
        elif choice == '7':
            query = input("Enter SQL query: ").strip()
            try:
                conn = sqlite3.connect(DB_PATH)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query)
                rows = cursor.fetchall()
                conn.close()
                print(f"\nResults ({len(rows)} rows):")
                for row in rows:
                    print(dict(row))
            except Exception as e:
                print(f"❌ Error: {e}")
        else:
            print("Invalid choice!")

if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at: {DB_PATH}")
        print("Make sure to run the Flask app first to create the database.")
    else:
        interactive_menu()
