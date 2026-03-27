import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_database():
    try:
        # Connect to default 'postgres' database
        conn = psycopg2.connect(
            user="postgres",
            password="password",
            host="localhost",
            port="5432",
            database="postgres"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Check if database exists
        cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'real_estate_crm_db'")
        exists = cur.fetchone()
        
        if not exists:
            print("Creating database 'real_estate_crm_db'...")
            cur.execute("CREATE DATABASE real_estate_crm_db")
            print("Database created successfully!")
        else:
            print("Database 'real_estate_crm_db' already exists.")
            
        cur.close()
        conn.close()
        return True
        
    except psycopg2.OperationalError as e:
        print(f"Error connecting to PostgreSQL: {e}")
        print("\nPlease ensure:")
        print("1. PostgreSQL is running")
        print("2. The password for user 'postgres' is 'password'")
        print("3. If your password is different, please update settings.py and this script.")
        return False

if __name__ == "__main__":
    create_database()
