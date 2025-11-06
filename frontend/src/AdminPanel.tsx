import React, { useState, useEffect } from 'react';
import AdminLogin from './AdminLogin';
import AdminSettings from './AdminSettings';
import AdminManagement from './AdminManagement';
import { authUtils } from './utils/auth';

interface Booking {
  id: number;
  customer_name: string;
  customer_email: string;
  customer_phone: string;
  seats: string[];
  total_amount: number;
  status: string;
  created_at: string;
  payment_proof: string | null;
}

interface Analytics {
  total_bookings: number;
  total_revenue: number;
  confirmed_bookings: number;
  pending_bookings: number;
  occupancy_rate: number;
}

interface Props {
  navigate: (path: string) => void;
}

const AdminPanel: React.FC<Props> = ({ navigate }) => {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState<string | null>(authUtils.getToken());
  const [selectedProof, setSelectedProof] = useState<string | null>(null);
  const [currentTab, setCurrentTab] = useState<'dashboard' | 'management' | 'settings'>('dashboard');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [bookingStats, setBookingStats] = useState<Record<string, number>>({});

  useEffect(() => {
    // Check authentication on component mount
    if (!authUtils.isAuthenticated()) {
      setToken(null);
      setLoading(false);
      return;
    }
    
    // Verify token is still valid and fetch data
    authUtils.apiCall('/api/admin/me')
      .then(response => {
        if (response.ok) {
          fetchBookings('all');
        } else {
          setToken(null);
          setLoading(false);
        }
      })
      .catch(() => {
        setToken(null);
        setLoading(false);
      });
  }, [token]);

  const fetchBookings = async (status?: string) => {
    try {
      const bookingsUrl = status && status !== 'all' ? `/api/bookings?status=${status}` : '/api/bookings';
      const [bookingsResponse, analyticsResponse, statsResponse] = await Promise.all([
        authUtils.apiCall(bookingsUrl),
        authUtils.apiCall('/api/analytics'),
        authUtils.apiCall('/api/bookings/stats')
      ]);
      
      const bookingsData = await bookingsResponse.json();
      const analyticsData = await analyticsResponse.json();
      const statsData = await statsResponse.json();
      
      // Add showtime info to bookings
      const bookingsWithShowtime = await Promise.all(
        bookingsData.map(async (booking: any) => {
          if (booking.showtime_id) {
            try {
              const showtimeResponse = await authUtils.apiCall(`/api/showtime/${booking.showtime_id}`);
              const showtimeData = await showtimeResponse.json();
              return {
                ...booking,
                movie_title: showtimeData.movie,
                theater_name: showtimeData.theater,
                show_date: showtimeData.show_date,
                show_time: showtimeData.showtime
              };
            } catch {
              return booking;
            }
          }
          return booking;
        })
      );
      
      setBookings(bookingsWithShowtime);
      setAnalytics(analyticsData);
      setBookingStats(statsData);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateBookingStatus = async (bookingId: number, status: string) => {
    try {
      const response = await authUtils.apiCall(`/api/booking/${bookingId}/status?status=${status}`, {
        method: 'PUT'
      });
      
      if (response.ok) {
        fetchBookings();
        alert(`Booking ${bookingId} ${status} successfully`);
      } else {
        alert('Failed to update booking status');
      }
    } catch (error) {
      console.error('Error updating booking:', error);
      alert('Failed to update booking status');
    }
  };

  const viewPaymentProof = async (bookingId: number) => {
    try {
      const response = await fetch(`/api/payment-proof/${bookingId}`);
      
      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        setSelectedProof(url);
      } else {
        alert('Payment proof not found');
      }
    } catch (error) {
      console.error('Error fetching payment proof:', error);
      alert('Failed to load payment proof');
    }
  };

  const logout = () => {
    authUtils.logout();
    setToken(null);
    navigate('/admin');
  };

  if (!token) {
    return <AdminLogin onLogin={(newToken) => {
      setToken(newToken);
      setLoading(true);
    }} />;
  }

  if (loading) return <div>Loading bookings...</div>;

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <nav style={{ marginBottom: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button onClick={() => navigate('/booking')} style={{ padding: '10px 20px' }}>
            ← Back to Booking
          </button>
          <button 
            onClick={() => setCurrentTab('dashboard')} 
            style={{ 
              padding: '10px 20px', 
              background: currentTab === 'dashboard' ? '#2196F3' : '#f0f0f0',
              color: currentTab === 'dashboard' ? 'white' : 'black',
              border: 'none', 
              borderRadius: '5px' 
            }}
          >
            📊 Dashboard
          </button>
          <button 
            onClick={() => setCurrentTab('management')} 
            style={{ 
              padding: '10px 20px', 
              background: currentTab === 'management' ? '#2196F3' : '#f0f0f0',
              color: currentTab === 'management' ? 'white' : 'black',
              border: 'none', 
              borderRadius: '5px' 
            }}
          >
            🎬 Management
          </button>
          <button 
            onClick={() => setCurrentTab('settings')} 
            style={{ 
              padding: '10px 20px', 
              background: currentTab === 'settings' ? '#2196F3' : '#f0f0f0',
              color: currentTab === 'settings' ? 'white' : 'black',
              border: 'none', 
              borderRadius: '5px' 
            }}
          >
            ⚙️ Settings
          </button>
        </div>
        <button onClick={logout} style={{ padding: '10px 20px', background: '#f44336', color: 'white', border: 'none', borderRadius: '5px' }}>
          Logout
        </button>
      </nav>
      {currentTab === 'settings' ? (
        <AdminSettings />
      ) : currentTab === 'management' ? (
        <AdminManagement />
      ) : (
        <div>
          <h1>Admin Panel - Movie Booking Dashboard</h1>
      
      {analytics && (
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
          gap: '20px', 
          marginBottom: '30px' 
        }}>
          <div style={{ background: '#e3f2fd', padding: '20px', borderRadius: '10px', textAlign: 'center' }}>
            <h3 style={{ margin: '0 0 10px 0', color: '#1976d2' }}>Total Bookings</h3>
            <p style={{ fontSize: '24px', fontWeight: 'bold', margin: 0 }}>{analytics.total_bookings}</p>
          </div>
          <div style={{ background: '#e8f5e8', padding: '20px', borderRadius: '10px', textAlign: 'center' }}>
            <h3 style={{ margin: '0 0 10px 0', color: '#2e7d32' }}>Total Revenue</h3>
            <p style={{ fontSize: '24px', fontWeight: 'bold', margin: 0 }}>Rp {analytics.total_revenue.toLocaleString()}</p>
          </div>
          <div style={{ background: '#fff3e0', padding: '20px', borderRadius: '10px', textAlign: 'center' }}>
            <h3 style={{ margin: '0 0 10px 0', color: '#f57c00' }}>Confirmed</h3>
            <p style={{ fontSize: '24px', fontWeight: 'bold', margin: 0 }}>{analytics.confirmed_bookings}</p>
          </div>
          <div style={{ background: '#fce4ec', padding: '20px', borderRadius: '10px', textAlign: 'center' }}>
            <h3 style={{ margin: '0 0 10px 0', color: '#c2185b' }}>Pending</h3>
            <p style={{ fontSize: '24px', fontWeight: 'bold', margin: 0 }}>{analytics.pending_bookings}</p>
          </div>
          <div style={{ background: '#f3e5f5', padding: '20px', borderRadius: '10px', textAlign: 'center' }}>
            <h3 style={{ margin: '0 0 10px 0', color: '#7b1fa2' }}>Occupancy</h3>
            <p style={{ fontSize: '24px', fontWeight: 'bold', margin: 0 }}>{analytics.occupancy_rate.toFixed(1)}%</p>
          </div>
        </div>
      )}
      
      <div style={{ marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '15px', flexWrap: 'wrap' }}>
        <button onClick={() => fetchBookings(statusFilter)} style={{ padding: '10px 20px' }}>
          Refresh Data
        </button>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '16px', fontWeight: 'bold' }}>Filter by Status:</span>
          <select 
            value={statusFilter} 
            onChange={(e) => {
              setStatusFilter(e.target.value);
              fetchBookings(e.target.value);
            }}
            style={{ padding: '8px 12px', borderRadius: '5px', border: '1px solid #ddd' }}
          >
            <option value="all">All Bookings ({Object.values(bookingStats).reduce((a, b) => a + b, 0)})</option>
            {Object.entries(bookingStats).map(([status, count]) => (
              <option key={status} value={status}>
                {status.replace('_', ' ').toUpperCase()} ({count})
              </option>
            ))}
          </select>
        </div>
        <span style={{ fontSize: '14px', color: '#666' }}>Showing {bookings.length} bookings</span>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', border: '1px solid #ddd' }}>
          <thead>
            <tr style={{ backgroundColor: '#f5f5f5' }}>
              <th style={{ padding: '12px', border: '1px solid #ddd' }}>ID</th>
              <th style={{ padding: '12px', border: '1px solid #ddd' }}>Movie/Theater</th>
              <th style={{ padding: '12px', border: '1px solid #ddd' }}>Customer</th>
              <th style={{ padding: '12px', border: '1px solid #ddd' }}>Contact</th>
              <th style={{ padding: '12px', border: '1px solid #ddd' }}>Seats</th>
              <th style={{ padding: '12px', border: '1px solid #ddd' }}>Amount</th>
              <th style={{ padding: '12px', border: '1px solid #ddd' }}>Status</th>
              <th style={{ padding: '12px', border: '1px solid #ddd' }}>Date</th>
              <th style={{ padding: '12px', border: '1px solid #ddd' }}>Payment Proof</th>
              <th style={{ padding: '12px', border: '1px solid #ddd' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {bookings.map((booking) => (
              <tr key={booking.id}>
                <td style={{ padding: '12px', border: '1px solid #ddd' }}>{booking.id}</td>
                <td style={{ padding: '12px', border: '1px solid #ddd' }}>
                  <div style={{ fontSize: '12px' }}>
                    <div><strong>{(booking as any).movie_title || 'Unknown Movie'}</strong></div>
                    <div>{(booking as any).theater_name || 'Unknown Theater'}</div>
                    <div>{(booking as any).show_date} {(booking as any).show_time}</div>
                  </div>
                </td>
                <td style={{ padding: '12px', border: '1px solid #ddd' }}>{booking.customer_name}</td>
                <td style={{ padding: '12px', border: '1px solid #ddd' }}>
                  <div>{booking.customer_email}</div>
                  <div>{booking.customer_phone}</div>
                </td>
                <td style={{ padding: '12px', border: '1px solid #ddd' }}>{booking.seats.join(', ')}</td>
                <td style={{ padding: '12px', border: '1px solid #ddd' }}>Rp {booking.total_amount.toLocaleString()}</td>
                <td style={{ padding: '12px', border: '1px solid #ddd' }}>
                  <span style={{
                    padding: '4px 8px',
                    borderRadius: '4px',
                    color: 'white',
                    backgroundColor: 
                      booking.status === 'confirmed' ? '#4CAF50' : 
                      booking.status === 'approved' ? '#f44336' : 
                      booking.status === 'pending_approval' ? '#FF9800' : 
                      booking.status === 'pending_payment' ? '#2196F3' : 
                      booking.status === 'admin_rejected' ? '#9E9E9E' : '#666'
                  }}>
                    {booking.status}
                  </span>
                </td>
                <td style={{ padding: '12px', border: '1px solid #ddd' }}>
                  {new Date(booking.created_at).toLocaleString()}
                </td>
                <td style={{ padding: '12px', border: '1px solid #ddd' }}>
                  {booking.payment_proof ? (
                    <button 
                      onClick={() => viewPaymentProof(booking.id)}
                      style={{ padding: '4px 8px', background: '#2196F3', color: 'white', border: 'none', borderRadius: '3px' }}
                    >
                      🔍 View Proof
                    </button>
                  ) : (
                    '❌ Not uploaded'
                  )}
                </td>
                <td style={{ padding: '12px', border: '1px solid #ddd' }}>
                  {booking.status === 'pending_approval' && (
                    <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
                      <button 
                        onClick={() => updateBookingStatus(booking.id, 'approved')}
                        style={{ padding: '4px 8px', background: '#4CAF50', color: 'white', border: 'none', borderRadius: '3px', fontSize: '12px' }}
                      >
                        ✓ Approve
                      </button>
                      <button 
                        onClick={() => updateBookingStatus(booking.id, 'admin_rejected')}
                        style={{ padding: '4px 8px', background: '#f44336', color: 'white', border: 'none', borderRadius: '3px', fontSize: '12px' }}
                      >
                        ✗ Reject
                      </button>
                    </div>
                  )}
                  {booking.status === 'approved' && (
                    <span style={{ color: '#4CAF50', fontWeight: 'bold', fontSize: '12px' }}>✓ Approved</span>
                  )}
                  {booking.status === 'pending_payment' && (
                    <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
                      <button 
                        onClick={() => updateBookingStatus(booking.id, 'cancelled')}
                        style={{ padding: '4px 8px', background: '#f44336', color: 'white', border: 'none', borderRadius: '3px', fontSize: '12px' }}
                      >
                        ✗ Cancel
                      </button>
                    </div>
                  )}
                  {booking.status === 'confirmed' && (
                    <span style={{ color: '#4CAF50', fontWeight: 'bold', fontSize: '12px' }}>✓ Confirmed</span>
                  )}
                  {booking.status === 'cancelled' && (
                    <span style={{ color: '#f44336', fontWeight: 'bold', fontSize: '12px' }}>✗ Cancelled</span>
                  )}
                  {booking.status === 'admin_rejected' && (
                    <span style={{ color: '#9E9E9E', fontWeight: 'bold', fontSize: '12px' }}>✗ Rejected</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {bookings.length === 0 && (
        <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
          No bookings found
        </div>
      )}
      
      {selectedProof && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          background: 'rgba(0,0,0,0.8)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000
        }}>
          <div style={{ position: 'relative', maxWidth: '90%', maxHeight: '90%' }}>
            <button 
              onClick={() => setSelectedProof(null)}
              style={{
                position: 'absolute',
                top: '-40px',
                right: '0',
                background: '#f44336',
                color: 'white',
                border: 'none',
                borderRadius: '50%',
                width: '30px',
                height: '30px',
                cursor: 'pointer'
              }}
            >
              ×
            </button>
            <img 
              src={selectedProof} 
              alt="Payment Proof" 
              style={{ maxWidth: '100%', maxHeight: '100%', borderRadius: '10px' }}
            />
          </div>
        </div>
      )}
        </div>
      )}
    </div>
  );
};

export default AdminPanel;