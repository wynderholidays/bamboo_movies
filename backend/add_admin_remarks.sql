-- Add admin_remarks column to bookings table
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS admin_remarks TEXT;

-- Add index for better performance
CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(status);
CREATE INDEX IF NOT EXISTS idx_bookings_created_at ON bookings(created_at);