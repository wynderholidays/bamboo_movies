-- Run this script in your PostgreSQL database to create all tables

-- 1. Bookings table
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
);

-- 2. OTP Storage table
CREATE TABLE otp_storage (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    otp VARCHAR(6) NOT NULL,
    booking_id INTEGER REFERENCES bookings(id),
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Admin Sessions table
CREATE TABLE admin_sessions (
    id SERIAL PRIMARY KEY,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);

-- 4. Seat Reservations table
CREATE TABLE seat_reservations (
    id SERIAL PRIMARY KEY,
    seat_id VARCHAR(10) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Theater Configuration table
CREATE TABLE theater_config (
    id SERIAL PRIMARY KEY,
    movie_name VARCHAR(255) NOT NULL,
    theater_name VARCHAR(255) NOT NULL,
    showtime VARCHAR(50) NOT NULL,
    price INTEGER NOT NULL,
    rows INTEGER NOT NULL,
    left_cols INTEGER NOT NULL,
    right_cols INTEGER NOT NULL,
    non_selectable_seats TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default theater configuration
INSERT INTO theater_config (
    movie_name, theater_name, showtime, price, 
    rows, left_cols, right_cols, non_selectable_seats
) VALUES (
    'Avengers: Endgame',
    'PVR Cinemas', 
    '7:00 PM',
    200,
    11,
    8,
    6,
    ARRAY['C1', 'C2', 'D1', 'D2', 'E1', 'E2', 'F1', 'F2', 'G1', 'G2', 'H1', 'H2', 'I1', 'I2', 'J1', 'J2', 'K1', 'K2']
);

-- Create indexes
CREATE INDEX idx_bookings_status ON bookings(status);
CREATE INDEX idx_bookings_email ON bookings(customer_email);
CREATE INDEX idx_otp_email ON otp_storage(email);
CREATE INDEX idx_reservations_seat ON seat_reservations(seat_id);