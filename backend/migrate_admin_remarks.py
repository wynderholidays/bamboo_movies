#!/usr/bin/env python3
"""
Migration script to add admin_remarks column to bookings table
"""

import psycopg2
from database import get_db_connection

def run_migration():
    """Run the migration to add admin_remarks column"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Add admin_remarks column
        cursor.execute("""
            ALTER TABLE bookings 
            ADD COLUMN IF NOT EXISTS admin_remarks TEXT
        """)
        
        # Add indexes for better performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_bookings_status 
            ON bookings(status)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_bookings_created_at 
            ON bookings(created_at)
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✓ Migration completed successfully")
        print("✓ Added admin_remarks column to bookings table")
        print("✓ Added performance indexes")
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        raise

if __name__ == "__main__":
    run_migration()