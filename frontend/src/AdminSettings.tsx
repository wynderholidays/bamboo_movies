import React, { useState, useEffect } from 'react';

interface AdminSettings {
  admin_email: string;
  admin_name: string;
  notification_enabled: boolean;
}

interface TheaterConfig {
  movie_name: string;
  movie_poster: string;
  theater_name: string;
  show_date: string;
  showtime: string;
  price: number;
}

const AdminSettings: React.FC = () => {
  const [settings, setSettings] = useState<AdminSettings>({
    admin_email: '',
    admin_name: '',
    notification_enabled: true
  });
  
  const [theaterConfig, setTheaterConfig] = useState<TheaterConfig>({
    movie_name: '',
    movie_poster: '',
    theater_name: '',
    show_date: '',
    showtime: '',
    price: 0
  });
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchSettings();
    fetchTheaterConfig();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await fetch('http://localhost:8000/admin/settings');
      const data = await response.json();
      setSettings(data);
    } catch (error) {
      console.error('Error fetching settings:', error);
    }
  };

  const fetchTheaterConfig = async () => {
    try {
      const response = await fetch('http://localhost:8000/admin/theater-config');
      const data = await response.json();
      setTheaterConfig({
        movie_name: data.movie_name,
        movie_poster: data.movie_poster || '',
        theater_name: data.theater_name,
        show_date: data.show_date || '',
        showtime: data.showtime,
        price: data.price
      });
    } catch (error) {
      console.error('Error fetching theater config:', error);
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async () => {
    setSaving(true);
    try {
      const response = await fetch('http://localhost:8000/admin/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      });
      
      if (response.ok) {
        alert('Settings saved successfully!');
      } else {
        alert('Failed to save settings');
      }
    } catch (error) {
      console.error('Error saving settings:', error);
      alert('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const saveTheaterConfig = async () => {
    setSaving(true);
    try {
      const response = await fetch('http://localhost:8000/admin/theater-config', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(theaterConfig)
      });
      
      if (response.ok) {
        alert('Theater configuration saved successfully!');
      } else {
        alert('Failed to save theater configuration');
      }
    } catch (error) {
      console.error('Error saving theater config:', error);
      alert('Failed to save theater configuration');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div>Loading settings...</div>;

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h1>⚙️ Admin Settings</h1>
      
      {/* Admin Settings Section */}
      <div style={{ 
        background: 'white', 
        padding: '20px', 
        borderRadius: '10px', 
        marginBottom: '20px',
        border: '1px solid #ddd'
      }}>
        <h2>📧 Admin Configuration</h2>
        
        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
            Admin Name:
          </label>
          <input
            type="text"
            value={settings.admin_name}
            onChange={(e) => setSettings({...settings, admin_name: e.target.value})}
            style={{
              width: '100%',
              padding: '10px',
              border: '1px solid #ddd',
              borderRadius: '5px',
              fontSize: '16px'
            }}
          />
        </div>
        
        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
            Admin Email (for notifications):
          </label>
          <input
            type="email"
            value={settings.admin_email}
            onChange={(e) => setSettings({...settings, admin_email: e.target.value})}
            style={{
              width: '100%',
              padding: '10px',
              border: '1px solid #ddd',
              borderRadius: '5px',
              fontSize: '16px'
            }}
          />
          <small style={{ color: '#666' }}>
            This email will receive notifications for new bookings and payment uploads
          </small>
        </div>
        
        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={settings.notification_enabled}
              onChange={(e) => setSettings({...settings, notification_enabled: e.target.checked})}
              style={{ marginRight: '10px' }}
            />
            Enable email notifications
          </label>
        </div>
        
        <button
          onClick={saveSettings}
          disabled={saving}
          style={{
            padding: '12px 24px',
            background: saving ? '#ccc' : '#4CAF50',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: saving ? 'not-allowed' : 'pointer',
            fontSize: '16px'
          }}
        >
          {saving ? 'Saving...' : 'Save Admin Settings'}
        </button>
      </div>

      {/* Theater Configuration Section */}
      <div style={{ 
        background: 'white', 
        padding: '20px', 
        borderRadius: '10px', 
        border: '1px solid #ddd'
      }}>
        <h2>🎬 Theater Configuration</h2>
        
        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
            Movie Name:
          </label>
          <input
            type="text"
            value={theaterConfig.movie_name}
            onChange={(e) => setTheaterConfig({...theaterConfig, movie_name: e.target.value})}
            style={{
              width: '100%',
              padding: '10px',
              border: '1px solid #ddd',
              borderRadius: '5px',
              fontSize: '16px'
            }}
          />
        </div>
        
        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
            Movie Poster URL:
          </label>
          <input
            type="url"
            value={theaterConfig.movie_poster}
            onChange={(e) => setTheaterConfig({...theaterConfig, movie_poster: e.target.value})}
            placeholder="https://example.com/poster.jpg"
            style={{
              width: '100%',
              padding: '10px',
              border: '1px solid #ddd',
              borderRadius: '5px',
              fontSize: '16px'
            }}
          />
          {theaterConfig.movie_poster && (
            <div style={{ marginTop: '10px' }}>
              <img 
                src={theaterConfig.movie_poster} 
                alt="Movie Poster Preview" 
                style={{ 
                  maxWidth: '200px', 
                  maxHeight: '300px', 
                  border: '1px solid #ddd',
                  borderRadius: '5px'
                }}
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = 'none';
                }}
              />
            </div>
          )}
        </div>
        
        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
            Theater Name:
          </label>
          <input
            type="text"
            value={theaterConfig.theater_name}
            onChange={(e) => setTheaterConfig({...theaterConfig, theater_name: e.target.value})}
            style={{
              width: '100%',
              padding: '10px',
              border: '1px solid #ddd',
              borderRadius: '5px',
              fontSize: '16px'
            }}
          />
        </div>
        
        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
            Show Date:
          </label>
          <input
            type="date"
            value={theaterConfig.show_date}
            onChange={(e) => setTheaterConfig({...theaterConfig, show_date: e.target.value})}
            style={{
              width: '100%',
              padding: '10px',
              border: '1px solid #ddd',
              borderRadius: '5px',
              fontSize: '16px'
            }}
          />
        </div>
        
        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
            Showtime:
          </label>
          <input
            type="time"
            value={theaterConfig.showtime}
            onChange={(e) => setTheaterConfig({...theaterConfig, showtime: e.target.value})}
            style={{
              width: '100%',
              padding: '10px',
              border: '1px solid #ddd',
              borderRadius: '5px',
              fontSize: '16px'
            }}
          />
        </div>
        
        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
            Ticket Price (₹):
          </label>
          <input
            type="number"
            value={theaterConfig.price}
            onChange={(e) => setTheaterConfig({...theaterConfig, price: parseInt(e.target.value) || 0})}
            style={{
              width: '100%',
              padding: '10px',
              border: '1px solid #ddd',
              borderRadius: '5px',
              fontSize: '16px'
            }}
          />
        </div>
        
        <button
          onClick={saveTheaterConfig}
          disabled={saving}
          style={{
            padding: '12px 24px',
            background: saving ? '#ccc' : '#2196F3',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: saving ? 'not-allowed' : 'pointer',
            fontSize: '16px'
          }}
        >
          {saving ? 'Saving...' : 'Save Theater Config'}
        </button>
      </div>
    </div>
  );
};

export default AdminSettings;