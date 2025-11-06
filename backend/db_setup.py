#!/usr/bin/env python3
"""
Database setup script for Movie Booking System
Run this to create the database structure
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'booking_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'password')
}

def create_database():
    """Create the database if it doesn't exist"""
    try:
        # Connect to PostgreSQL server (not specific database)
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database='postgres'  # Connect to default postgres database
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_CONFIG['database']}'")
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(f"CREATE DATABASE {DB_CONFIG['database']}")
            print(f"✅ Database '{DB_CONFIG['database']}' created successfully")
        else:
            print(f"✅ Database '{DB_CONFIG['database']}' already exists")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False
    
    return True

def setup_tables():
    """Create all tables and initial data"""
    try:
        # Read SQL file
        with open('database.sql', 'r') as file:
            sql_content = file.read()
        
        # Connect to the movie_booking database
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Execute SQL commands (skip CREATE DATABASE line)
        sql_commands = sql_content.split(';')
        for command in sql_commands:
            command = command.strip()
            if command and not command.startswith('--') and 'CREATE DATABASE' not in command:
                try:
                    cursor.execute(command)
                    conn.commit()
                except Exception as e:
                    if "already exists" not in str(e):
                        print(f"Warning: {e}")
        
        print("✅ Database tables created successfully")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error setting up tables: {e}")
        return False
    
    return True

def test_connection():
    """Test database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        
        # Test query
        cursor.execute("SELECT COUNT(*) as count FROM bookings")
        result = cursor.fetchone()
        
        print(f"✅ Database connection successful. Bookings count: {result['count']}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def main():
    print("🚀 Setting up Movie Booking Database...")
    print("=" * 50)
    
    # Step 1: Create database
    if not create_database():
        return
    
    # Step 2: Setup tables
    if not setup_tables():
        return
    
    # Step 3: Test connection
    if not test_connection():
        return
    
    print("=" * 50)
    print("🎉 Database setup completed successfully!")
    print("\nNext steps:")
    print("1. Update your .env file with database credentials")
    print("2. Install psycopg2: pip install psycopg2-binary")
    print("3. Restart your FastAPI server")

if __name__ == "__main__":
    main()