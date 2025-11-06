-- Movie Booking System Database Schema
-- PostgreSQL Database Structure

-- Create database (run this first)
-- CREATE DATABASE movie_booking;

-- Connect to the database and run the following:

-- 1. Bookings table - Main booking records
CREATE TABLE bookings (
    id SERIAL PRIMARY KEY,
    customer_name VARCHAR(255) NOT NULL,
    customer_email VARCHAR(255) NOT NULL,
    customer_phone VARCHAR(20) NOT NULL,
    seats TEXT[] NOT NULL,  -- Array of seat IDs like ['A1', 'A2']
    total_amount INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending_payment',
    payment_proof VARCHAR(500),  -- File path to payment proof
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. OTP Storage table - Email verification codes
CREATE TABLE otp_storage (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    otp VARCHAR(6) NOT NULL,
    booking_id INTEGER REFERENCES bookings(id),
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Admin Sessions table - Admin login sessions
CREATE TABLE admin_sessions (
    id SERIAL PRIMARY KEY,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);

-- 4. Seat Reservations table - Temporary seat holds
CREATE TABLE seat_reservations (
    id SERIAL PRIMARY KEY,
    seat_id VARCHAR(10) NOT NULL,  -- Like 'A1', 'B5'
    user_id VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Theater Configuration table - Theater settings
CREATE TABLE theater_config (
    id SERIAL PRIMARY KEY,
    movie_name VARCHAR(255) NOT NULL,
    theater_name VARCHAR(255) NOT NULL,
    showtime VARCHAR(50) NOT NULL,
    price INTEGER NOT NULL,
    rows INTEGER NOT NULL,
    left_cols INTEGER NOT NULL,
    right_cols INTEGER NOT NULL,
    non_selectable_seats TEXT[],  -- Array of non-selectable seats
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

-- Create indexes for better performance
CREATE INDEX idx_bookings_status ON bookings(status);
CREATE INDEX idx_bookings_email ON bookings(customer_email);
CREATE INDEX idx_bookings_created_at ON bookings(created_at);
CREATE INDEX idx_otp_email ON otp_storage(email);
CREATE INDEX idx_otp_expires ON otp_storage(expires_at);
CREATE INDEX idx_reservations_seat ON seat_reservations(seat_id);
CREATE INDEX idx_reservations_expires ON seat_reservations(expires_at);
CREATE INDEX idx_admin_sessions_token ON admin_sessions(session_token);

-- Create function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for bookings table
CREATE TRIGGER update_bookings_updated_at 
    BEFORE UPDATE ON bookings 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create function to clean expired records
CREATE OR REPLACE FUNCTION cleanup_expired_records()
RETURNS void AS $$
BEGIN
    -- Clean expired OTPs
    DELETE FROM otp_storage WHERE expires_at < CURRENT_TIMESTAMP;
    
    -- Clean expired seat reservations
    DELETE FROM seat_reservations WHERE expires_at < CURRENT_TIMESTAMP;
    
    -- Clean expired admin sessions
    DELETE FROM admin_sessions WHERE expires_at < CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- Optional: Create a scheduled job to run cleanup (requires pg_cron extension)
-- SELECT cron.schedule('cleanup-expired', '*/5 * * * *', 'SELECT cleanup_expired_records();');

-- Grant permissions (adjust username as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_app_user;