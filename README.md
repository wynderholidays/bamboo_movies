# Movie Booking App

A simple movie booking system with React frontend and Python FastAPI backend.

## Features

- **Seat Selection**: Interactive 10x10 theater layout
- **Customer Details**: Name, email, phone collection
- **Payment Integration**: Display UPI/Bank details for payment
- **Payment Proof Upload**: Customers upload payment screenshots
- **Booking Management**: Track booking status

## Quick Start

### Backend (Python FastAPI)

```bash
cd backend
pip install -r requirements.txt
python main.py
```

Backend runs on: http://localhost:8000

### Frontend (React)

```bash
cd frontend
npm start
```

Frontend runs on: http://localhost:3000

## API Endpoints

- `GET /theater` - Get theater info and booked seats
- `POST /book` - Create new booking
- `POST /upload-payment/{booking_id}` - Upload payment proof
- `GET /booking/{booking_id}` - Get booking details
- `GET /bookings` - Get all bookings (admin)

## Usage Flow

1. **Select Seats**: Choose available seats from theater layout
2. **Enter Details**: Fill customer information
3. **Book Tickets**: Create booking and get payment details
4. **Make Payment**: Pay via UPI or bank transfer
5. **Upload Proof**: Upload payment screenshot
6. **Confirmation**: Booking submitted for verification

## Configuration

- **Movie**: Avengers: Endgame
- **Theater**: PVR Cinemas  
- **Showtime**: 7:00 PM
- **Price**: ₹200 per seat
- **Layout**: 10x10 seats (A1-J10)

## File Structure

```
booking-app/
├── backend/
│   ├── main.py          # FastAPI application
│   ├── requirements.txt # Python dependencies
│   └── uploads/         # Payment proof storage
└── frontend/
    ├── src/
    │   ├── App.tsx      # Main React component
    │   └── App.css      # Styling
    └── package.json     # Node dependencies
```