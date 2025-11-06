import React, { useState, useEffect } from 'react';
import './App.css';

interface TheaterInfo {
  rows: number;
  left_cols: number;
  right_cols: number;
  movie: string;
  movie_poster?: string;
  theater: string;
  show_date?: string;
  showtime: string;
  price: number;
  pending_approval_seats: string[];
  approved_seats: string[];
  confirmed_seats: string[];
  reserved_seats: string[];
  non_selectable: string[];
}

interface BookingResponse {
  booking_id: number;
  total_amount: number;
  payment_details: {
    upi_id: string;
    account_number: string;
    ifsc: string;
    account_name: string;
  };
}

interface Props {
  navigate: (path: string) => void;
  currentRoute: string;
  selectedShowtimeId: number | null;
}

const BookingApp: React.FC<Props> = ({ navigate, currentRoute, selectedShowtimeId }) => {
  const [theaterInfo, setTheaterInfo] = useState<TheaterInfo | null>(null);
  const [selectedSeats, setSelectedSeats] = useState<string[]>([]);
  const [customerInfo, setCustomerInfo] = useState({
    name: '',
    email: '',
    phone: ''
  });
  const [bookingResponse, setBookingResponse] = useState<BookingResponse | null>(null);
  const [paymentFile, setPaymentFile] = useState<File | null>(null);
  const [showPaymentOTP, setShowPaymentOTP] = useState(false);
  const [paymentOtp, setPaymentOtp] = useState('');
  const [isBooking, setIsBooking] = useState(false);
  const [userId] = useState(() => Math.random().toString(36).substr(2, 9));

  useEffect(() => {
    if (selectedShowtimeId) {
      fetchTheaterInfo();
    }
  }, [selectedShowtimeId]);

  const fetchTheaterInfo = async () => {
    if (!selectedShowtimeId) return;
    
    try {
      const response = await fetch(`/api/showtime/${selectedShowtimeId}`);
      const data = await response.json();
      setTheaterInfo(data);
    } catch (error) {
      console.error('Error fetching showtime info:', error);
    }
  };

  const generateSeatId = (row: number, col: number) => {
    return `${String.fromCharCode(65 + row)}${col}`;
  };

  const toggleSeat = (seatId: string) => {
    console.log(`Toggling seat ${seatId}`);
    
    // Check if seat is unavailable
    const isUnavailable = theaterInfo?.pending_approval_seats?.includes(seatId) ||
                         theaterInfo?.approved_seats?.includes(seatId) ||
                         theaterInfo?.confirmed_seats?.includes(seatId) ||
                         theaterInfo?.non_selectable?.includes(seatId);
    
    if (isUnavailable) {
      console.log(`Seat ${seatId} is unavailable`);
      return;
    }
    
    const isCurrentlySelected = selectedSeats.includes(seatId);
    
    if (isCurrentlySelected) {
      console.log(`Deselecting seat ${seatId}`);
      setSelectedSeats(prev => prev.filter(s => s !== seatId));
    } else {
      console.log(`Selecting seat ${seatId}`);
      setSelectedSeats(prev => [...prev, seatId]);
    }
  };

  const createBooking = async () => {
    if (isBooking) {
      console.log('Booking already in progress, ignoring click');
      return;
    }
    
    console.log('Starting booking process...');
    console.log('Selected seats:', selectedSeats);
    console.log('Customer info:', customerInfo);
    
    setIsBooking(true);
    try {
      const bookingData = {
        showtime_id: selectedShowtimeId,
        customer_name: customerInfo.name,
        customer_email: customerInfo.email,
        customer_phone: customerInfo.phone,
        selected_seats: selectedSeats
      };
      
      console.log('Sending booking request:', bookingData);
      
      const response = await fetch('/api/book', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(bookingData)
      });

      console.log('Booking response status:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('Booking successful:', data);
        setBookingResponse(data);
        console.log('Navigating to payment page...');
        navigate(`/payment/${selectedShowtimeId}`);
      } else {
        const error = await response.json();
        console.error('Booking failed:', error);
        alert(error.detail || 'Booking failed');
        fetchTheaterInfo();
      }
    } catch (error) {
      console.error('Booking error:', error);
      alert('Booking failed - please try again');
    } finally {
      setIsBooking(false);
      console.log('Booking process completed');
    }
  };

  const handleConfirmBooking = async () => {
    if (!customerInfo.name || !customerInfo.email || !customerInfo.phone || selectedSeats.length === 0) {
      alert('Please fill all details and select seats');
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(customerInfo.email)) {
      alert('Please enter a valid email address');
      return;
    }
    
    const phoneRegex = /^\+?[1-9]\d{1,14}$/;
    if (!phoneRegex.test(customerInfo.phone)) {
      alert('Please enter a valid phone number with country code (e.g., +1234567890)');
      return;
    }

    await createBooking();
  };

  const handlePaymentUpload = async () => {
    if (!paymentFile || !bookingResponse) return;

    const formData = new FormData();
    formData.append('file', paymentFile);

    try {
      const response = await fetch(`/api/upload-payment/${bookingResponse.booking_id}`, {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        if (data.requires_otp) {
          setShowPaymentOTP(true);
          alert(data.message);
        } else {
          navigate('/success');
        }
      } else {
        alert('Upload failed');
      }
    } catch (error) {
      console.error('Upload error:', error);
      alert('Upload failed');
    }
  };

  const verifyPaymentOTP = async () => {
    try {
      const response = await fetch('/api/verify-payment-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone: customerInfo.email, otp: paymentOtp })
      });
      
      if (response.ok) {
        setShowPaymentOTP(false);
        navigate('/success');
      } else {
        const error = await response.json();
        alert(error.detail);
      }
    } catch (error) {
      console.error('OTP verification error:', error);
      alert('OTP verification failed');
    }
  };

  if (!selectedShowtimeId) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <h2>No showtime selected</h2>
        <button onClick={() => navigate('/')} style={{ padding: '10px 20px', background: '#2196F3', color: 'white', border: 'none', borderRadius: '5px' }}>
          Select Showtime
        </button>
      </div>
    );
  }
  
  if (!theaterInfo) return <div>Loading showtime info...</div>;

  return (
    <div className="App">
      <header>
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px', marginBottom: '20px' }}>
          {theaterInfo.movie_poster && (
            <img 
              src={theaterInfo.movie_poster} 
              alt={theaterInfo.movie}
              style={{ 
                width: '120px', 
                height: '180px', 
                objectFit: 'cover', 
                borderRadius: '10px',
                border: '2px solid rgba(255,255,255,0.3)'
              }}
            />
          )}
          <div style={{ flex: 1 }}>
            <h1 style={{ margin: '0 0 10px 0' }}>{theaterInfo.movie}</h1>
            <p style={{ margin: '5px 0', fontSize: '18px' }}>{theaterInfo.theater}</p>
            {theaterInfo.show_date && (
              <p style={{ margin: '5px 0', fontSize: '16px' }}>📅 {new Date(theaterInfo.show_date).toLocaleDateString()}</p>
            )}
            <p style={{ margin: '5px 0', fontSize: '16px' }}>🕐 {theaterInfo.showtime}</p>
            <p style={{ margin: '5px 0', fontSize: '18px', fontWeight: 'bold' }}>💰 Rp {theaterInfo.price.toLocaleString()} per seat</p>
          </div>
        </div>
        {currentRoute === '/' && (
          <nav style={{ marginTop: '15px' }}>
            <button 
              onClick={() => navigate('/admin')} 
              style={{ 
                padding: '8px 16px', 
                background: 'rgba(255,255,255,0.2)', 
                color: 'white', 
                border: '1px solid white', 
                borderRadius: '5px',
                cursor: 'pointer'
              }}
            >
              Admin Panel
            </button>
          </nav>
        )}
      </header>

      {currentRoute.startsWith('/booking') || currentRoute === '/' ? (
        <div className="seat-selection">
          <h2>Select Seats</h2>
          <div className="theater-layout">
            {Array.from({ length: theaterInfo.rows }, (_, row) => (
              <div key={row} className="theater-row">
                <span className="row-label">{String.fromCharCode(65 + row)}</span>
                <div className="left-section">
                  {Array.from({ length: theaterInfo.left_cols }, (_, col) => {
                    const seatId = generateSeatId(row, col + 1);
                    const isSelected = selectedSeats.includes(seatId);
                    const isNonSelectable = theaterInfo.non_selectable?.includes(seatId);
                    const isPendingApproval = theaterInfo.pending_approval_seats?.includes(seatId);
                    const isApproved = theaterInfo.approved_seats?.includes(seatId);
                    const isConfirmed = theaterInfo.confirmed_seats?.includes(seatId);
                    
                    let seatClass = '';
                    if (isNonSelectable) seatClass = 'non-selectable';
                    else if (isPendingApproval) seatClass = 'pending-approval';
                    else if (isApproved || isConfirmed) seatClass = 'confirmed';
                    else if (isSelected) seatClass = 'selected';
                    
                    return (
                      <div
                        key={seatId}
                        className={`seat ${seatClass}`}
                        onClick={() => toggleSeat(seatId)}
                      >
                        {seatId}
                      </div>
                    );
                  })}
                </div>
                <div className="aisle"></div>
                <div className="right-section">
                  {Array.from({ length: theaterInfo.right_cols }, (_, col) => {
                    const seatId = generateSeatId(row, col + theaterInfo.left_cols + 1);
                    const isSelected = selectedSeats.includes(seatId);
                    const isNonSelectable = theaterInfo.non_selectable?.includes(seatId);
                    const isPendingApproval = theaterInfo.pending_approval_seats?.includes(seatId);
                    const isApproved = theaterInfo.approved_seats?.includes(seatId);
                    const isConfirmed = theaterInfo.confirmed_seats?.includes(seatId);
                    
                    let seatClass = '';
                    if (isNonSelectable) seatClass = 'non-selectable';
                    else if (isPendingApproval) seatClass = 'pending-approval';
                    else if (isApproved || isConfirmed) seatClass = 'confirmed';
                    else if (isSelected) seatClass = 'selected';
                    
                    return (
                      <div
                        key={seatId}
                        className={`seat ${seatClass}`}
                        onClick={() => toggleSeat(seatId)}
                      >
                        {seatId}
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
          <div className="screen">SCREEN</div>
          
          <div className="legend">
            <span className="available">Available</span>
            <span className="selected">Selected</span>
            <span className="pending-approval">Pending Approval</span>
            <span className="confirmed">Confirmed</span>
            <span className="non-selectable">Not Available</span>
          </div>

          {selectedSeats.length > 0 && (
            <div className="booking-form">
              <h3>Customer Details</h3>
              <input
                type="text"
                placeholder="Name"
                value={customerInfo.name}
                onChange={(e) => setCustomerInfo({...customerInfo, name: e.target.value})}
              />
              <input
                type="email"
                placeholder="Email"
                value={customerInfo.email}
                onChange={(e) => setCustomerInfo({...customerInfo, email: e.target.value})}
              />
              <input
                type="tel"
                placeholder="Phone"
                value={customerInfo.phone}
                onChange={(e) => setCustomerInfo({...customerInfo, phone: e.target.value})}
              />
              
              <div className="summary">
                <p>Selected Seats: {selectedSeats.join(', ')}</p>
                <p>Total Amount: Rp {(selectedSeats.length * theaterInfo.price).toLocaleString()}</p>
              </div>
              
              <button 
                onClick={handleConfirmBooking} 
                disabled={isBooking}
                style={{
                  opacity: isBooking ? 0.6 : 1,
                  cursor: isBooking ? 'not-allowed' : 'pointer'
                }}
              >
                {isBooking ? 'Processing...' : 'Confirm Booking'}
              </button>
            </div>
          )}
        </div>
      ) : currentRoute.includes('/payment') ? (
        <div className="payment-section">
          <h2>💳 Payment Required</h2>
          <p>Please complete payment and upload proof.</p>
          
          <div className="booking-summary">
            <p>Booking ID: {bookingResponse?.booking_id}</p>
            <p>Total Amount: Rp {bookingResponse?.total_amount?.toLocaleString()}</p>
          </div>
          
          <div className="payment-methods">
            <div className="bank-transfer">
              <h3>Bank Transfer</h3>
              <p>Name: Harikumar Maruthur</p>
              <p>Bank: BCA</p>
              <p>Account Number: 3350229476</p>
            </div>
          </div>

          <div className="upload-section">
            <h3>Upload Payment Proof (Required)</h3>
            <input
              type="file"
              accept="image/*"
              onChange={(e) => setPaymentFile(e.target.files?.[0] || null)}
              required
            />
            <button onClick={handlePaymentUpload} disabled={!paymentFile}>
              Upload Proof & Submit
            </button>
          </div>
          
          {showPaymentOTP && (
            <div style={{ marginTop: '20px', padding: '15px', border: '1px solid #ddd', borderRadius: '5px', background: '#f9f9f9' }}>
              <h4>Email Verification Required</h4>
              <p>Enter the OTP sent to your email: {customerInfo.email}</p>
              <input
                type="text"
                placeholder="Enter 6-digit OTP"
                value={paymentOtp}
                onChange={(e) => setPaymentOtp(e.target.value)}
                maxLength={6}
                style={{ marginRight: '10px', padding: '8px' }}
              />
              <button onClick={verifyPaymentOTP} style={{ padding: '8px 16px', background: '#4CAF50', color: 'white', border: 'none', borderRadius: '5px' }}>
                Verify & Submit
              </button>
            </div>
          )}
        </div>
      ) : currentRoute.includes('/success') ? (
        <div className="success-section">
          <h2>🎬 Booking Submitted!</h2>
          <div style={{ background: '#e3f2fd', padding: '20px', borderRadius: '10px', margin: '20px 0' }}>
            <p><strong>Booking ID:</strong> {bookingResponse?.booking_id}</p>
            <p><strong>Total Amount:</strong> Rp {bookingResponse?.total_amount?.toLocaleString()}</p>
            <p><strong>Status:</strong> Pending Admin Approval</p>
          </div>
          
          <div style={{ background: '#fff3e0', padding: '20px', borderRadius: '10px', margin: '20px 0' }}>
            <h3>📱 What's Next?</h3>
            <ol style={{ textAlign: 'left', margin: '10px 0' }}>
              <li>Admin will review your booking</li>
              <li>You'll get email notification when approved</li>
              <li>Your tickets will be confirmed</li>
              <li>Enjoy the movie!</li>
            </ol>
          </div>
          
          <p style={{ color: '#666', fontSize: '14px' }}>
            📧 You'll receive updates on email: {customerInfo.email}
          </p>
          <button 
            onClick={() => {
              navigate('/');
              setSelectedSeats([]);
              setCustomerInfo({ name: '', email: '', phone: '' });
              setBookingResponse(null);
              setPaymentFile(null);
            }}
            style={{
              marginTop: '20px',
              padding: '12px 24px',
              background: '#667eea',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer'
            }}
          >
            Book Another Ticket
          </button>
        </div>
      ) : (
        <div>Page not found</div>
      )}
    </div>
  );
};

export default BookingApp;