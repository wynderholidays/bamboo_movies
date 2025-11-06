#!/usr/bin/env python3
"""Test database connection and create tables if needed"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

def test_connection():
    try:
        print("Testing database connection...")
        print(f"Host: {DB_CONFIG['host']}")
        print(f"Database: {DB_CONFIG['database']}")
        print(f"User: {DB_CONFIG['user']}")
        
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        
        # Test query
        cursor.execute("SELECT version()")
        version = cursor.fetchone()
        print(f"✅ Connected to PostgreSQL: {version['version']}")
        
        # Check if tables exist
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()
        print(f"✅ Tables found: {[t['table_name'] for t in tables]}")
        
        # Test insert
        cursor.execute("""
            INSERT INTO bookings (customer_name, customer_email, customer_phone, seats, total_amount)
            VALUES ('Test User', 'test@example.com', '+1234567890', ARRAY['A1'], 200)
            RETURNING id
        """)
        booking_id = cursor.fetchone()['id']
        print(f"✅ Test booking created with ID: {booking_id}")
        
        # Clean up test data
        cursor.execute("DELETE FROM bookings WHERE id = %s", (booking_id,))
        conn.commit()
        print("✅ Test data cleaned up")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

if __name__ == "__main__":
    test_connection()