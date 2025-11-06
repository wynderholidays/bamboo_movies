# Movie Booking System

A modern, responsive movie ticket booking application built with React frontend and FastAPI backend, featuring real-time seat selection, payment processing, and admin management.

## 🎬 Features

### Customer Features
- **Interactive Seat Selection**: Visual theater layout with real-time seat availability
- **Mobile Responsive**: Optimized for both desktop and mobile devices
- **Payment Integration**: Bank transfer with payment proof upload
- **Email Verification**: OTP-based payment verification system
- **Booking Status Tracking**: Real-time updates on booking status
- **Multiple Showtimes**: Support for different movies, theaters, and showtimes

### Admin Features
- **JWT Authentication**: Secure admin login with token-based authentication
- **Booking Management**: Approve, reject, or cancel bookings
- **Status Filtering**: Filter bookings by status (pending, approved, confirmed, etc.)
- **Payment Proof Review**: View and verify customer payment screenshots
- **Analytics Dashboard**: Revenue tracking and occupancy statistics
- **Content Management**: Manage movies, theaters, and showtimes
- **Email Notifications**: Automated notifications for booking status changes

### Technical Features
- **Anti-Abuse Protection**: IP-based rate limiting and seat reservation limits
- **Real-time Updates**: Live seat availability updates
- **File Upload**: AWS S3 integration for payment proof storage
- **Email System**: AWS SES integration for automated notifications
- **Responsive Design**: Mobile-first design with touch-friendly interface
- **Error Handling**: Comprehensive error handling and user feedback

## 🏗️ Architecture

```
booking-app/
├── backend/                 # FastAPI Backend
│   ├── main.py             # Main application file
│   ├── database.py         # Database operations
│   ├── logger_config.py    # Logging configuration
│   ├── requirements.txt    # Python dependencies
│   └── .env               # Environment variables
├── frontend/               # React Frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── utils/         # Utility functions
│   │   ├── App.tsx        # Main app component
│   │   └── index.tsx      # Entry point
│   ├── package.json       # Node dependencies
│   └── public/            # Static assets
└── README.md              # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL database
- AWS account (for S3 and SES)

### Backend Setup

1. **Install Dependencies**
```bash
cd backend
pip install -r requirements.txt
```

2. **Configure Environment**
```bash
# Copy and update .env file
cp .env.example .env
# Update database and AWS credentials
```

3. **Database Setup**
```bash
# Create database tables
python setup_database.py
```

4. **Start Backend**
```bash
python main.py
# API available at: http://localhost:8000
# API docs: http://localhost:8000/docs
```

### Frontend Setup

1. **Install Dependencies**
```bash
cd frontend
npm install
```

2. **Start Development Server**
```bash
npm start
# Frontend available at: http://localhost:3000
```

### Production Deployment

1. **Build Frontend**
```bash
cd frontend
npm run build
```

2. **Deploy with Nginx**
```bash
# Copy build files to nginx directory
sudo cp -r build/* /var/www/html/
# Configure nginx to proxy API calls to backend
```

## 🎯 User Flow

### Customer Booking Flow
1. **Select Showtime** → Choose movie, theater, date, and time
2. **Choose Seats** → Interactive seat selection with real-time availability
3. **Enter Details** → Customer name, email, and phone number
4. **Confirm Booking** → Creates booking with "pending_payment" status
5. **Make Payment** → Bank transfer to provided account details
6. **Upload Proof** → Upload payment screenshot/receipt
7. **Email Verification** → Enter OTP sent to email
8. **Admin Review** → Admin approves/rejects the booking
9. **Confirmation** → Email notification with booking confirmation

### Admin Management Flow
1. **Secure Login** → JWT-based authentication
2. **Dashboard** → View analytics and booking statistics
3. **Review Bookings** → Filter and manage bookings by status
4. **Verify Payments** → View payment proofs and approve/reject
5. **Send Notifications** → Automated email updates to customers
6. **Manage Content** → Add/edit movies, theaters, and showtimes

## 🎨 Seat Selection System

### Visual Indicators
- **White**: Available seats
- **Green**: Selected by current user
- **Orange**: Pending approval (awaiting admin review)
- **Red**: Confirmed bookings
- **Gray**: Not available (blocked seats)

### Seat Naming Convention
- **Format**: `{Row}{Number}` (e.g., A1, A2, B1, B2)
- **Rows**: A-K (11 rows)
- **Layout**: Left section (8 seats) + Aisle + Right section (6 seats)
- **Total**: 154 seats per theater

## 💳 Payment System

### Supported Payment Method
- **Bank Transfer**: BCA Bank account
- **Account Details**:
  - Name: Harikumar Maruthur
  - Bank: BCA
  - Account: 3350229476

### Payment Verification Process
1. Customer uploads payment proof (image)
2. System generates 6-digit OTP
3. OTP sent to customer email
4. Customer enters OTP for verification
5. Booking status changes to "pending_approval"
6. Admin reviews and approves/rejects

## 🔐 Security Features

### Authentication & Authorization
- **JWT Tokens**: Secure admin authentication
- **Password Hashing**: bcrypt for password security
- **Session Management**: Token-based session handling

### Anti-Abuse Protection
- **Rate Limiting**: Max 4 seats per IP address
- **IP Tracking**: Monitor and limit suspicious activity
- **Input Validation**: Comprehensive data validation
- **SQL Injection Protection**: Parameterized queries

### Data Protection
- **Environment Variables**: Sensitive data in .env files
- **CORS Configuration**: Restricted cross-origin requests
- **File Upload Security**: Validated file types and sizes

## 📊 Database Schema

### Core Tables
- **movies**: Movie information and metadata
- **theaters**: Theater details and seating configuration
- **showtimes**: Movie schedules and pricing
- **bookings**: Customer bookings and status tracking
- **seat_reservations**: Temporary seat reservations
- **otps**: Email verification codes
- **admin_settings**: Admin configuration

### Key Relationships
- Showtimes → Movies (many-to-one)
- Showtimes → Theaters (many-to-one)
- Bookings → Showtimes (many-to-one)
- Seat Reservations → Showtimes (many-to-one)

## 🌐 API Endpoints

### Public Endpoints
- `GET /showtimes` - List all available showtimes
- `GET /showtime/{id}` - Get showtime details and seat availability
- `POST /book` - Create new booking
- `POST /upload-payment/{booking_id}` - Upload payment proof
- `POST /verify-payment-otp` - Verify payment with OTP

### Admin Endpoints (Protected)
- `POST /admin/login` - Admin authentication
- `GET /bookings` - List bookings with filtering
- `PUT /booking/{id}/status` - Update booking status
- `GET /analytics` - Get booking analytics
- `POST /admin/movies` - Create/manage movies
- `POST /admin/theaters` - Create/manage theaters
- `POST /admin/showtimes` - Create/manage showtimes

## 🔧 Configuration

### Environment Variables
```bash
# Database
DB_HOST=your-database-host
DB_PORT=5432
DB_NAME=movie_db
DB_USER=movie_app_user
DB_PASSWORD=your-password

# AWS Services
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=ap-southeast-3
S3_BUCKET=your-s3-bucket

# Email
SES_FROM_EMAIL=noreply@yourdomain.com
ADMIN_EMAIL=admin@yourdomain.com

# Security
JWT_SECRET_KEY=your-jwt-secret
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-admin-password
```

### Theater Configuration
```python
# Default theater layout
ROWS = 11                    # A through K
LEFT_COLS = 8               # Left section seats
RIGHT_COLS = 6              # Right section seats
AISLE_WIDTH = 20px          # Space between sections
SEAT_SIZE = 32px            # Desktop seat size
MOBILE_SEAT_SIZE = 26px     # Mobile seat size
```

## 📱 Mobile Optimization

### Responsive Design
- **Breakpoints**: 768px (tablet), 480px (mobile)
- **Touch Targets**: Minimum 44px for touch interaction
- **Scaling**: Proportional scaling for different screen sizes
- **Typography**: Responsive font sizes and spacing

### Mobile-Specific Features
- **Swipe Navigation**: Touch-friendly navigation
- **Optimized Forms**: Large input fields and buttons
- **Compressed Layout**: Efficient use of screen space
- **Fast Loading**: Optimized assets and lazy loading

## 🚨 Error Handling

### Frontend Error Handling
- **Network Errors**: Retry mechanisms and user feedback
- **Validation Errors**: Real-time form validation
- **API Errors**: User-friendly error messages
- **Fallback UI**: Graceful degradation for failures

### Backend Error Handling
- **HTTP Status Codes**: Proper status code usage
- **Error Logging**: Comprehensive error logging
- **Exception Handling**: Graceful error recovery
- **Validation**: Input validation and sanitization

## 📈 Performance Optimization

### Frontend Optimization
- **Code Splitting**: Lazy loading of components
- **Asset Optimization**: Compressed images and fonts
- **Caching**: Browser caching strategies
- **Bundle Size**: Minimized JavaScript bundles

### Backend Optimization
- **Database Indexing**: Optimized database queries
- **Connection Pooling**: Efficient database connections
- **Caching**: Redis caching for frequent queries
- **Async Processing**: Non-blocking I/O operations

## 🔍 Monitoring & Logging

### Application Logging
- **Request Logging**: All API requests and responses
- **Error Logging**: Detailed error tracking
- **Performance Logging**: Response time monitoring
- **Security Logging**: Authentication and authorization events

### Health Monitoring
- **API Health Checks**: Endpoint availability monitoring
- **Database Health**: Connection and query monitoring
- **External Services**: AWS service status monitoring
- **Resource Usage**: CPU, memory, and disk monitoring

## 🧪 Testing

### Frontend Testing
```bash
# Run tests
npm test

# Run with coverage
npm run test:coverage
```

### Backend Testing
```bash
# Run tests
pytest

# Run with coverage
pytest --cov=.
```

### Test Coverage
- **Unit Tests**: Individual component testing
- **Integration Tests**: API endpoint testing
- **E2E Tests**: Complete user flow testing
- **Performance Tests**: Load and stress testing

## 🚀 Deployment

### Production Checklist
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] SSL certificates installed
- [ ] Nginx configuration updated
- [ ] AWS services configured
- [ ] Monitoring tools setup
- [ ] Backup procedures in place
- [ ] Security audit completed

### Scaling Considerations
- **Load Balancing**: Multiple backend instances
- **Database Scaling**: Read replicas and sharding
- **CDN Integration**: Static asset delivery
- **Caching Layer**: Redis for session and data caching

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

### Code Standards
- **Python**: PEP 8 style guide
- **TypeScript**: ESLint configuration
- **Git**: Conventional commit messages
- **Documentation**: Inline code documentation

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### Common Issues
- **Database Connection**: Check PostgreSQL service and credentials
- **AWS Services**: Verify IAM permissions and service configuration
- **Email Delivery**: Check SES configuration and domain verification
- **File Uploads**: Verify S3 bucket permissions and CORS settings

### Getting Help
- **Documentation**: Check API docs at `/docs` endpoint
- **Logs**: Review application logs for error details
- **Issues**: Create GitHub issue with detailed description
- **Contact**: Email support team for urgent issues

## 🔄 Version History

### v1.0.0 (Current)
- Initial release with core booking functionality
- Admin panel with JWT authentication
- Payment processing with OTP verification
- Mobile-responsive design
- AWS integration for file storage and email

### Planned Features
- **v1.1.0**: Real-time notifications with WebSocket
- **v1.2.0**: Multiple payment methods integration
- **v1.3.0**: Advanced analytics and reporting
- **v1.4.0**: Mobile app development
- **v2.0.0**: Multi-tenant architecture