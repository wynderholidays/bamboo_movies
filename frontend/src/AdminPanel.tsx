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
  const [toast, setToast] = useState<{message: string, type: 'success'|'error'|'info'} | null>(null);
  const [actionModal, setActionModal] = useState<{bookingId: number, currentStatus: string} | null>(null);
  const [actionStatus, setActionStatus] = useState<string>('');
  const [adminRemarks, setAdminRemarks] = useState<string>('');

  const showToast = (message: string, type: 'success'|'error'|'info' = 'info') => {
    setToast({message, type});
    setTimeout(() => setToast(null), 4000);
  };

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

  const updateBookingStatus = async (bookingId: number, status: string, remarks?: string) => {
    try {
      const response = await authUtils.apiCall(`/api/booking/${bookingId}/action`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status, admin_remarks: remarks })
      });
      
      if (response.ok) {
        fetchBookings();
        showToast(`Booking ${bookingId} ${status} successfully`, 'success');
        setActionModal(null);
        setAdminRemarks('');
      } else {
        showToast('Failed to update booking status', 'error');
      }
    } catch (error) {
      console.error('Error updating booking:', error);
      showToast('Failed to update booking status', 'error');
    }
  };

  const openActionModal = (bookingId: number, currentStatus: string) => {
    setActionModal({bookingId, currentStatus});
    setActionStatus('');
    setAdminRemarks('');
  };

  const handleActionSubmit = () => {
    if (!actionStatus) {
      showToast('Please select an action', 'error');
      return;
    }
    updateBookingStatus(actionModal!.bookingId, actionStatus, adminRemarks);
  };

  const resendConfirmationEmail = async (bookingId: number) => {
    try {
      const response = await authUtils.apiCall(`/api/booking/${bookingId}/resend-email`, {
        method: 'POST'
      });
      
      if (response.ok) {
        const result = await response.json();
        showToast(result.message, 'success');
      } else {
        const error = await response.json();
        showToast(error.detail || 'Failed to resend email', 'error');
      }
    } catch (error) {
      console.error('Error resending email:', error);
      showToast('Failed to resend email', 'error');
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
        showToast('Payment proof not found', 'error');
      }
    } catch (error) {
      console.error('Error fetching payment proof:', error);
      showToast('Failed to load payment proof', 'error');
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
    <div style={{ padding: '20px', maxWidth: '95vw', margin: '0 auto' }}>
      {toast && (
        <div style={{
          position: 'fixed',
          top: '20px',
          left: '50%',
          transform: 'translateX(-50%)',
          padding: '12px 20px',
          borderRadius: '8px',
          color: 'white',
          background: toast.type === 'error' ? '#f44336' : toast.type === 'success' ? '#4caf50' : '#2196f3',
          zIndex: 1000,
          boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
          maxWidth: 'calc(100vw - 40px)',
          fontSize: '14px',
          textAlign: 'center'
        }}>
          {toast.message}
        </div>
      )}
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
            <h3 style={{ margin: '0 0 10px 0', color: '#1976d2' }}>Approved Seats</h3>
            <p style={{ fontSize: '24px', fontWeight: 'bold', margin: 0 }}>{analytics.total_bookings || 0}</p>
          </div>
          <div style={{ background: '#e8f5e8', padding: '20px', borderRadius: '10px', textAlign: 'center' }}>
            <h3 style={{ margin: '0 0 10px 0', color: '#2e7d32' }}>Total Revenue</h3>
            <p style={{ fontSize: '24px', fontWeight: 'bold', margin: 0 }}>Rp {(analytics.total_revenue || 0).toLocaleString()}</p>
          </div>
          <div style={{ background: '#f3e5f5', padding: '20px', borderRadius: '10px', textAlign: 'center' }}>
            <h3 style={{ margin: '0 0 10px 0', color: '#7b1fa2' }}>Occupancy Rate</h3>
            <p style={{ fontSize: '24px', fontWeight: 'bold', margin: 0 }}>{(analytics.occupancy_rate || 0).toFixed(1)}%</p>
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
        <table style={{ width: '100%', minWidth: '1400px', borderCollapse: 'collapse', border: '1px solid #ddd' }}>
          <thead>
            <tr style={{ backgroundColor: '#f5f5f5' }}>
              <th style={{ padding: '12px', border: '1px solid #ddd', width: '60px' }}>ID</th>
              <th style={{ padding: '12px', border: '1px solid #ddd', width: '200px' }}>Movie/Theater</th>
              <th style={{ padding: '12px', border: '1px solid #ddd', width: '150px' }}>Customer</th>
              <th style={{ padding: '12px', border: '1px solid #ddd', width: '180px' }}>Contact</th>
              <th style={{ padding: '12px', border: '1px solid #ddd', width: '120px' }}>Seats</th>
              <th style={{ padding: '12px', border: '1px solid #ddd', width: '100px' }}>Amount</th>
              <th style={{ padding: '12px', border: '1px solid #ddd', width: '120px' }}>Status</th>
              <th style={{ padding: '12px', border: '1px solid #ddd', width: '140px' }}>Date</th>
              <th style={{ padding: '12px', border: '1px solid #ddd', width: '120px' }}>Payment Proof</th>
              <th style={{ padding: '12px', border: '1px solid #ddd', width: '150px' }}>Actions</th>
              <th style={{ padding: '12px', border: '1px solid #ddd', width: '120px' }}>Resend Email</th>
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
                  <button 
                    onClick={() => openActionModal(booking.id, booking.status)}
                    style={{ 
                      padding: '6px 12px', 
                      background: '#2196F3', 
                      color: 'white', 
                      border: 'none', 
                      borderRadius: '4px', 
                      fontSize: '12px',
                      cursor: 'pointer'
                    }}
                  >
                    ⚡ Actions
                  </button>
                  {(booking as any).admin_remarks && (
                    <div style={{ 
                      marginTop: '5px', 
                      fontSize: '11px', 
                      color: '#666', 
                      fontStyle: 'italic',
                      maxWidth: '150px',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis'
                    }}>
                      💬 {(booking as any).admin_remarks}
                    </div>
                  )}
                </td>
                <td style={{ padding: '12px', border: '1px solid #ddd' }}>
                  {booking.status === 'approved' ? (
                    <button 
                      onClick={() => resendConfirmationEmail(booking.id)}
                      style={{ 
                        padding: '6px 12px', 
                        background: '#4CAF50', 
                        color: 'white', 
                        border: 'none', 
                        borderRadius: '4px', 
                        fontSize: '12px',
                        cursor: 'pointer'
                      }}
                    >
                      📧 Resend
                    </button>
                  ) : (
                    <span style={{ color: '#999', fontSize: '12px' }}>N/A</span>
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

      {actionModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          background: 'rgba(0,0,0,0.5)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000
        }}>
          <div style={{
            background: 'white',
            padding: '30px',
            borderRadius: '10px',
            maxWidth: '500px',
            width: '90%',
            maxHeight: '80vh',
            overflow: 'auto'
          }}>
            <h3 style={{ marginTop: 0 }}>Update Booking #{actionModal.bookingId}</h3>
            <p><strong>Current Status:</strong> {actionModal.currentStatus}</p>
            
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '10px', fontWeight: 'bold' }}>New Status:</label>
              <select 
                value={actionStatus} 
                onChange={(e) => setActionStatus(e.target.value)}
                style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ddd' }}
              >
                <option value="">Select Action...</option>
                <option value="pending_payment">Set to Pending Payment</option>
                <option value="pending_verification">Set to Pending Verification</option>
                <option value="pending_approval">Set to Pending Approval</option>
                <option value="approved">Approve Booking</option>
                <option value="confirmed">Confirm Booking</option>
                <option value="admin_rejected">Reject Booking</option>
                <option value="cancelled">Cancel Booking</option>
              </select>
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '10px', fontWeight: 'bold' }}>Admin Remarks (Optional):</label>
              <textarea 
                value={adminRemarks}
                onChange={(e) => setAdminRemarks(e.target.value)}
                placeholder="Add any notes or reasons for this action..."
                style={{ 
                  width: '100%', 
                  height: '80px', 
                  padding: '8px', 
                  borderRadius: '4px', 
                  border: '1px solid #ddd',
                  resize: 'vertical'
                }}
              />
            </div>

            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button 
                onClick={() => setActionModal(null)}
                style={{ 
                  padding: '10px 20px', 
                  background: '#f0f0f0', 
                  border: 'none', 
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                Cancel
              </button>
              <button 
                onClick={handleActionSubmit}
                style={{ 
                  padding: '10px 20px', 
                  background: '#2196F3', 
                  color: 'white', 
                  border: 'none', 
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                Update Booking
              </button>
            </div>
          </div>
        </div>
      )}
        </div>
      )}
    </div>
  );
};

export default AdminPanel;