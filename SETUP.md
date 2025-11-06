# Movie Booking App - Setup Guide

## Quick Start (Windows)

1. **Run the application**:
   ```bash
   # Double-click start.bat or run in command prompt:
   start.bat
   ```

2. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Manual Setup

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the backend server**:
   ```bash
   python run.py
   ```

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install Node.js dependencies**:
   ```bash
   npm install
   ```

3. **Start the React development server**:
   ```bash
   npm start
   ```

## Features

### User Features
- **Seat Selection**: Interactive 10x10 theater layout
- **Real-time Updates**: See booked seats in real-time
- **Customer Registration**: Name, email, phone collection
- **Payment Integration**: UPI and Bank transfer details
- **Payment Proof Upload**: Upload payment screenshots
- **Booking Confirmation**: Get booking ID and status

### Admin Features
- **Booking Management**: View all bookings
- **Status Updates**: Update booking status
- **Analytics**: View booking statistics
- **Payment Verification**: Check uploaded payment proofs

## API Endpoints

### Public Endpoints
- `GET /` - API status
- `GET /theater` - Get theater info and booked seats
- `POST /book` - Create new booking
- `POST /upload-payment/{booking_id}` - Upload payment proof
- `GET /booking/{booking_id}` - Get booking details

### Admin Endpoints
- `GET /bookings` - Get all bookings
- `PUT /booking/{booking_id}/status` - Update booking status
- `GET /analytics` - Get booking analytics

## Configuration

### Movie Details
- **Movie**: Avengers: Endgame
- **Theater**: PVR Cinemas
- **Showtime**: 7:00 PM
- **Price**: ₹200 per seat
- **Layout**: 10x10 seats (A1-J10)

### Payment Details
- **UPI ID**: moviebooking@paytm
- **Bank Account**: 1234567890
- **IFSC**: HDFC0001234
- **Account Name**: Movie Booking System

## File Structure

```
booking-app/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── run.py               # Server startup script
│   ├── requirements.txt     # Python dependencies
│   └── uploads/             # Payment proof storage
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # Main booking interface
│   │   ├── AdminPanel.tsx   # Admin panel component
│   │   └── App.css          # Styling
│   └── package.json         # Node dependencies
├── start.bat                # Windows startup script
├── README.md                # Project overview
└── SETUP.md                 # This setup guide
```

## Troubleshooting

### Common Issues

1. **Port already in use**:
   - Backend: Change port in `run.py`
   - Frontend: Set PORT environment variable

2. **CORS errors**:
   - Ensure frontend URL is in CORS allowed origins in `main.py`

3. **File upload issues**:
   - Check if `uploads/` directory exists in backend folder
   - Verify file permissions

### Development

- **Backend logs**: Check console output from `python run.py`
- **Frontend logs**: Check browser console for React errors
- **API testing**: Use http://localhost:8000/docs for interactive API testing

## Production Deployment

### Backend
- Use production WSGI server (gunicorn, uvicorn)
- Configure proper file storage (AWS S3, etc.)
- Set up database for persistent storage
- Configure environment variables

### Frontend
- Build production bundle: `npm run build`
- Serve with nginx or similar web server
- Configure API base URL for production

## Next Steps

1. **Database Integration**: Replace in-memory storage with PostgreSQL/MySQL
2. **Authentication**: Add user authentication and authorization
3. **Payment Gateway**: Integrate with actual payment providers
4. **Email Notifications**: Send booking confirmations via email
5. **SMS Integration**: Send booking updates via SMS
6. **Advanced Analytics**: Add more detailed reporting
7. **Mobile App**: Create React Native mobile application