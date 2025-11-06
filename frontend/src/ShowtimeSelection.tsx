import React, { useState, useEffect } from 'react';

interface Showtime {
  id: number;
  movie_title: string;
  poster_url: string;
  theater_name: string;
  address: string;
  show_date: string;
  show_time: string;
  price: number;
}

interface Props {
  onShowtimeSelect: (showtimeId: number) => void;
}

const ShowtimeSelection: React.FC<Props> = ({ onShowtimeSelect }) => {
  const [showtimes, setShowtimes] = useState<Showtime[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchShowtimes();
  }, []);

  const fetchShowtimes = async () => {
    try {
      const response = await fetch('http://localhost:8000/showtimes');
      const data = await response.json();
      setShowtimes(data);
    } catch (error) {
      console.error('Error fetching showtimes:', error);
    } finally {
      setLoading(false);
    }
  };

  const groupedShowtimes = showtimes.reduce((acc, showtime) => {
    const key = `${showtime.movie_title}-${showtime.show_date}`;
    if (!acc[key]) {
      acc[key] = {
        movie_title: showtime.movie_title,
        poster_url: showtime.poster_url,
        show_date: showtime.show_date,
        times: []
      };
    }
    acc[key].times.push({
      id: showtime.id,
      theater_name: showtime.theater_name,
      address: showtime.address,
      show_time: showtime.show_time,
      price: showtime.price
    });
    return acc;
  }, {} as any);

  if (loading) return <div>Loading showtimes...</div>;

  return (
    <div style={{ padding: '20px' }}>
      <h1>🎬 Select Movie & Showtime</h1>
      
      {Object.entries(groupedShowtimes).map(([key, group]: [string, any]) => (
        <div key={key} style={{ 
          background: 'white', 
          borderRadius: '15px', 
          padding: '20px', 
          marginBottom: '20px',
          boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
        }}>
          <div style={{ display: 'flex', gap: '20px', marginBottom: '20px' }}>
            {group.poster_url && (
              <img 
                src={group.poster_url} 
                alt={group.movie_title}
                style={{ 
                  width: '120px', 
                  height: '180px', 
                  objectFit: 'cover', 
                  borderRadius: '10px'
                }}
              />
            )}
            <div>
              <h2 style={{ margin: '0 0 10px 0', color: '#333' }}>{group.movie_title}</h2>
              <p style={{ margin: '5px 0', fontSize: '16px', color: '#666' }}>
                📅 {new Date(group.show_date).toLocaleDateString('en-US', { 
                  weekday: 'long', 
                  year: 'numeric', 
                  month: 'long', 
                  day: 'numeric' 
                })}
              </p>
            </div>
          </div>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '15px' }}>
            {group.times.map((time: any) => (
              <div 
                key={time.id}
                onClick={() => onShowtimeSelect(time.id)}
                style={{
                  border: '2px solid #e0e0e0',
                  borderRadius: '10px',
                  padding: '15px',
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                  background: '#f9f9f9'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = '#2196F3';
                  e.currentTarget.style.background = '#f0f8ff';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = '#e0e0e0';
                  e.currentTarget.style.background = '#f9f9f9';
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                  <span style={{ fontSize: '18px', fontWeight: 'bold', color: '#2196F3' }}>
                    🕐 {time.show_time}
                  </span>
                  <span style={{ fontSize: '16px', fontWeight: 'bold', color: '#4CAF50' }}>
                    ₹{time.price}
                  </span>
                </div>
                <div style={{ fontSize: '14px', color: '#666' }}>
                  <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>🏢 {time.theater_name}</div>
                  <div>📍 {time.address}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
      
      {Object.keys(groupedShowtimes).length === 0 && (
        <div style={{ 
          textAlign: 'center', 
          padding: '40px', 
          color: '#666',
          background: 'white',
          borderRadius: '15px'
        }}>
          <h2>No showtimes available</h2>
          <p>Please check back later or contact admin to add showtimes.</p>
        </div>
      )}
    </div>
  );
};

export default ShowtimeSelection;