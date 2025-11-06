-- Movie Booking System Database Schema
-- PostgreSQL Database Structure

-- 1. Movies table
CREATE TABLE IF NOT EXISTS movies (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    poster_url VARCHAR(500),
    duration_minutes INTEGER DEFAULT 120,
    genre VARCHAR(100),
    rating VARCHAR(20),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Theaters table
CREATE TABLE IF NOT EXISTS theaters (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    address TEXT,
    rows INTEGER DEFAULT 11,
    left_cols INTEGER DEFAULT 8,
    right_cols INTEGER DEFAULT 6,
    non_selectable_seats TEXT[],
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Showtimes table
CREATE TABLE IF NOT EXISTS showtimes (
    id SERIAL PRIMARY KEY,
    movie_id INTEGER REFERENCES movies(id),
    theater_id INTEGER REFERENCES theaters(id),
    show_date DATE NOT NULL,
    show_time TIME NOT NULL,
    price INTEGER NOT NULL DEFAULT 200000,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Bookings table
CREATE TABLE IF NOT EXISTS bookings (
    id SERIAL PRIMARY KEY,
    showtime_id INTEGER REFERENCES showtimes(id),
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

-- 5. OTP Storage table
CREATE TABLE IF NOT EXISTS otp_storage (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    otp VARCHAR(6) NOT NULL,
    booking_id INTEGER REFERENCES bookings(id),
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Seat Reservations table
CREATE TABLE IF NOT EXISTS seat_reservations (
    id SERIAL PRIMARY KEY,
    showtime_id INTEGER REFERENCES showtimes(id),
    seat_id VARCHAR(10) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. Admin Settings table
CREATE TABLE IF NOT EXISTS admin_settings (
    id SERIAL PRIMARY KEY,
    admin_name VARCHAR(255) DEFAULT 'Admin',
    admin_email VARCHAR(255) DEFAULT 'admin@bambooholiday.com',
    notification_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample data
INSERT INTO movies (title, poster_url, duration_minutes, genre, rating, description) VALUES 
('Avengers: Endgame', 'https://image.tmdb.org/t/p/w500/or06FN3Dka5tukK1e9sl16pB3iy.jpg', 181, 'Action, Adventure, Drama', 'PG-13', 'The epic conclusion to the Infinity Saga'),
('Spider-Man: No Way Home', 'https://image.tmdb.org/t/p/w500/1g0dhYtq4irTY1GPXvft6k4YLjm.jpg', 148, 'Action, Adventure, Sci-Fi', 'PG-13', 'Spider-Man faces villains from across the multiverse')
ON CONFLICT DO NOTHING;

INSERT INTO theaters (name, address, rows, left_cols, right_cols, non_selectable_seats) VALUES 
('PVR Cinemas Jakarta', 'Grand Indonesia Mall, Jakarta', 11, 8, 6, ARRAY['A1', 'A14', 'K1', 'K14']),
('CGV Blitz Senayan', 'Senayan City Mall, Jakarta', 10, 7, 7, ARRAY['A1', 'A14', 'J1', 'J14'])
ON CONFLICT DO NOTHING;

INSERT INTO showtimes (movie_id, theater_id, show_date, show_time, price) VALUES 
(1, 1, CURRENT_DATE, '19:00', 200000),
(1, 1, CURRENT_DATE, '21:30', 200000),
(2, 1, CURRENT_DATE + 1, '18:00', 200000),
(2, 2, CURRENT_DATE + 1, '20:30', 200000)
ON CONFLICT DO NOTHING;

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