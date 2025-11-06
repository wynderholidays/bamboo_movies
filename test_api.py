#!/usr/bin/env python3
"""
Simple test script to verify the Movie Booking API is working correctly.
Run this after starting the backend server.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_api():
    print("Testing Movie Booking API...")
    print("=" * 50)
    
    # Test 1: Check API status
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"✅ API Status: {response.json()}")
    except Exception as e:
        print(f"❌ API Status failed: {e}")
        return
    
    # Test 2: Get theater info
    try:
        response = requests.get(f"{BASE_URL}/theater")
        theater_info = response.json()
        print(f"✅ Theater Info: {theater_info['movie']} at {theater_info['theater']}")
        print(f"   Seats: {theater_info['rows']}x{theater_info['cols']}, Price: ₹{theater_info['price']}")
    except Exception as e:
        print(f"❌ Theater info failed: {e}")
        return
    
    # Test 3: Create a test booking
    booking_data = {
        "customer_name": "Test Customer",
        "customer_email": "test@example.com",
        "customer_phone": "9876543210",
        "selected_seats": ["A1", "A2"]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/book", json=booking_data)
        booking_response = response.json()
        booking_id = booking_response["booking_id"]
        print(f"✅ Booking Created: ID {booking_id}, Amount: ₹{booking_response['total_amount']}")
    except Exception as e:
        print(f"❌ Booking creation failed: {e}")
        return
    
    # Test 4: Get booking details
    try:
        response = requests.get(f"{BASE_URL}/booking/{booking_id}")
        booking_details = response.json()
        print(f"✅ Booking Details: {booking_details['customer_name']}, Seats: {booking_details['seats']}")
    except Exception as e:
        print(f"❌ Get booking failed: {e}")
    
    # Test 5: Get all bookings
    try:
        response = requests.get(f"{BASE_URL}/bookings")
        all_bookings = response.json()
        print(f"✅ All Bookings: {len(all_bookings)} total bookings")
    except Exception as e:
        print(f"❌ Get all bookings failed: {e}")
    
    # Test 6: Get analytics
    try:
        response = requests.get(f"{BASE_URL}/analytics")
        analytics = response.json()
        print(f"✅ Analytics: {analytics['total_bookings']} bookings, ₹{analytics['total_revenue']} revenue")
    except Exception as e:
        print(f"❌ Analytics failed: {e}")
    
    # Test 7: Check theater info again (should show booked seats)
    try:
        response = requests.get(f"{BASE_URL}/theater")
        theater_info = response.json()
        print(f"✅ Updated Theater: {len(theater_info['booked_seats'])} seats booked")
    except Exception as e:
        print(f"❌ Updated theater info failed: {e}")
    
    print("=" * 50)
    print("API testing completed!")
    print(f"Visit {BASE_URL}/docs for interactive API documentation")

if __name__ == "__main__":
    test_api()