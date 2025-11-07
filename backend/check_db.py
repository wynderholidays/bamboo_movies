#!/usr/bin/env python3
"""
Check database connection and add sample data
"""

from database import get_db_connection

def check_database():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check tables exist
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name IN ('movies', 'theaters', 'showtimes', 'bookings')
        """)
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Tables found: {tables}")
        
        # Check showtimes count
        cursor.execute("SELECT COUNT(*) FROM showtimes WHERE is_active = TRUE")
        showtime_count = cursor.fetchone()[0]
        print(f"Active showtimes: {showtime_count}")
        
        # Check movies count
        cursor.execute("SELECT COUNT(*) FROM movies WHERE is_active = TRUE")
        movie_count = cursor.fetchone()[0]
        print(f"Active movies: {movie_count}")
        
        # Check theaters count
        cursor.execute("SELECT COUNT(*) FROM theaters WHERE is_active = TRUE")
        theater_count = cursor.fetchone()[0]
        print(f"Active theaters: {theater_count}")
        
        if showtime_count == 0:
            print("No showtimes found. Adding sample data...")
            add_sample_data(cursor, conn)
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Database check failed: {e}")

def add_sample_data(cursor, conn):
    # Add sample movie
    cursor.execute("""
        INSERT INTO movies (title, poster_url, duration_minutes, genre, rating, description, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
        RETURNING id
    """, ("Sample Movie", "https://via.placeholder.com/300x450", 120, "Action", "PG-13", "Sample movie description", True))
    
    result = cursor.fetchone()
    if result:
        movie_id = result[0]
    else:
        cursor.execute("SELECT id FROM movies WHERE title = %s LIMIT 1", ("Sample Movie",))
        movie_id = cursor.fetchone()[0]
    
    # Add sample theater
    cursor.execute("""
        INSERT INTO theaters (name, address, rows, left_cols, right_cols, non_selectable_seats, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
        RETURNING id
    """, ("Sample Theater", "123 Movie Street", 11, 8, 6, [], True))
    
    result = cursor.fetchone()
    if result:
        theater_id = result[0]
    else:
        cursor.execute("SELECT id FROM theaters WHERE name = %s LIMIT 1", ("Sample Theater",))
        theater_id = cursor.fetchone()[0]
    
    # Add sample showtime
    cursor.execute("""
        INSERT INTO showtimes (movie_id, theater_id, show_date, show_time, price, is_active)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
    """, (movie_id, theater_id, "2024-12-25", "19:00", 50000, True))
    
    conn.commit()
    print("✓ Sample data added successfully")

if __name__ == "__main__":
    check_database()