#!/usr/bin/env python3
"""Simple table creation script"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

def create_tables():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Drop existing tables if they exist
    cursor.execute("DROP TABLE IF EXISTS otp_storage CASCADE")
    cursor.execute("DROP TABLE IF EXISTS seat_reservations CASCADE")
    cursor.execute("DROP TABLE IF EXISTS admin_sessions CASCADE")
    cursor.execute("DROP TABLE IF EXISTS bookings CASCADE")
    cursor.execute("DROP TABLE IF EXISTS theater_config CASCADE")
    
    # Create bookings table
    cursor.execute("""
        CREATE TABLE bookings (
            id SERIAL PRIMARY KEY,
            customer_name VARCHAR(255) NOT NULL,
            customer_email VARCHAR(255) NOT NULL,
            customer_phone VARCHAR(20) NOT NULL,
            seats TEXT[] NOT NULL,
            total_amount INTEGER NOT NULL,
            status VARCHAR(50) NOT NULL DEFAULT 'pending_payment',
            payment_proof VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create OTP storage table
    cursor.execute("""
        CREATE TABLE otp_storage (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) NOT NULL,
            otp VARCHAR(6) NOT NULL,
            booking_id INTEGER REFERENCES bookings(id),
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create seat reservations table
    cursor.execute("""
        CREATE TABLE seat_reservations (
            id SERIAL PRIMARY KEY,
            seat_id VARCHAR(10) NOT NULL,
            user_id VARCHAR(255) NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create admin sessions table
    cursor.execute("""
        CREATE TABLE admin_sessions (
            id SERIAL PRIMARY KEY,
            session_token VARCHAR(255) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL
        )
    """)
    
    # Create theater config table
    cursor.execute("""
        CREATE TABLE theater_config (
            id SERIAL PRIMARY KEY,
            movie_name VARCHAR(255) NOT NULL,
            movie_poster VARCHAR(500),
            theater_name VARCHAR(255) NOT NULL,
            show_date DATE,
            showtime VARCHAR(50) NOT NULL,
            price INTEGER NOT NULL,
            rows INTEGER NOT NULL,
            left_cols INTEGER NOT NULL,
            right_cols INTEGER NOT NULL,
            non_selectable_seats TEXT[],
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create admin settings table
    cursor.execute("""
        CREATE TABLE admin_settings (
            id SERIAL PRIMARY KEY,
            admin_email VARCHAR(255) NOT NULL,
            admin_name VARCHAR(255) NOT NULL DEFAULT 'Admin',
            notification_enabled BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Insert default theater configuration
    cursor.execute("""
        INSERT INTO theater_config (
            movie_name, movie_poster, theater_name, show_date, showtime, price, 
            rows, left_cols, right_cols, non_selectable_seats
        ) VALUES (
            'Avengers: Endgame',
            'https://m.media-amazon.com/images/M/MV5BMTc5MDE2ODcwNV5BMl5BanBnXkFtZTgwMzI2NzQ2NzM@._V1_.jpg',
            'PVR Cinemas',
            '2024-12-25', 
            '19:00',
            200,
            11,
            8,
            6,
            ARRAY['C1', 'C2', 'D1', 'D2', 'E1', 'E2', 'F1', 'F2', 'G1', 'G2', 'H1', 'H2', 'I1', 'I2', 'J1', 'J2', 'K1', 'K2']
        )
    """)
    
    # Insert default admin settings
    cursor.execute("""
        INSERT INTO admin_settings (admin_email, admin_name, notification_enabled)
        VALUES ('admin@bambooholiday.com', 'Admin', TRUE)
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX idx_bookings_status ON bookings(status)")
    cursor.execute("CREATE INDEX idx_bookings_email ON bookings(customer_email)")
    cursor.execute("CREATE INDEX idx_otp_email ON otp_storage(email)")
    cursor.execute("CREATE INDEX idx_reservations_seat ON seat_reservations(seat_id)")
    cursor.execute("CREATE INDEX idx_admin_settings_email ON admin_settings(admin_email)")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("✅ All tables created successfully!")

if __name__ == "__main__":
    create_tables()