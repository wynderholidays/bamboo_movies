import React, { useState, useEffect } from 'react';

interface Movie {
  id: number;
  title: string;
  poster_url: string;
  duration_minutes: number;
  genre: string;
  rating: string;
}

interface Theater {
  id: number;
  name: string;
  address: string;
  rows: number;
  left_cols: number;
  right_cols: number;
  non_selectable_seats: string[];
}

interface Showtime {
  id: number;
  movie_title: string;
  theater_name: string;
  show_date: string;
  show_time: string;
  price: number;
}

const AdminManagement: React.FC = () => {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [theaters, setTheaters] = useState<Theater[]>([]);
  const [showtimes, setShowtimes] = useState<Showtime[]>([]);
  const [activeTab, setActiveTab] = useState<'movies' | 'theaters' | 'showtimes'>('movies');

  const [newMovie, setNewMovie] = useState({
    title: '', poster_url: '', duration_minutes: 120, genre: '', rating: ''
  });
  const [editingMovie, setEditingMovie] = useState<Movie | null>(null);
  const [editingTheater, setEditingTheater] = useState<Theater | null>(null);
  const [newTheater, setNewTheater] = useState({
    name: '', address: '', rows: 11, left_cols: 8, right_cols: 6, non_selectable_seats: ''
  });
  const [newShowtime, setNewShowtime] = useState({
    movie_id: 0, theater_id: 0, show_date: '', show_time: '', price: 200000
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [moviesRes, theatersRes, showtimesRes] = await Promise.all([
        fetch('http://localhost:8000/admin/movies'),
        fetch('http://localhost:8000/admin/theaters'),
        fetch('http://localhost:8000/admin/showtimes')
      ]);
      
      setMovies(await moviesRes.json());
      setTheaters(await theatersRes.json());
      setShowtimes(await showtimesRes.json());
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  const createMovie = async () => {
    try {
      const response = await fetch('http://localhost:8000/admin/movies', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newMovie)
      });
      
      if (response.ok) {
        alert('Movie created successfully!');
        setNewMovie({ title: '', poster_url: '', duration_minutes: 120, genre: '', rating: '' });
        fetchData();
      } else {
        const errorData = await response.text();
        alert(`Failed to create movie: ${errorData}`);
      }
    } catch (error) {
      console.error('Error creating movie:', error);
      alert(`Network error: ${error}. Make sure the server is running on http://localhost:8000`);
    }
  };

  const updateMovie = async () => {
    if (!editingMovie) return;
    
    try {
      const response = await fetch(`http://localhost:8000/admin/movies/${editingMovie.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: editingMovie.title,
          poster_url: editingMovie.poster_url,
          duration_minutes: editingMovie.duration_minutes,
          genre: editingMovie.genre,
          rating: editingMovie.rating,
          description: ''
        })
      });
      
      if (response.ok) {
        alert('Movie updated successfully!');
        setEditingMovie(null);
        fetchData();
      }
    } catch (error) {
      console.error('Error updating movie:', error);
    }
  };

  const deleteMovie = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this movie?')) return;
    
    try {
      const response = await fetch(`http://localhost:8000/admin/movies/${id}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        alert('Movie deleted successfully!');
        fetchData();
      }
    } catch (error) {
      console.error('Error deleting movie:', error);
    }
  };

  const updateTheater = async () => {
    if (!editingTheater) return;
    
    try {
      const response = await fetch(`http://localhost:8000/admin/theaters/${editingTheater.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: editingTheater.name,
          address: editingTheater.address,
          rows: editingTheater.rows,
          left_cols: editingTheater.left_cols,
          right_cols: editingTheater.right_cols,
          non_selectable_seats: editingTheater.non_selectable_seats
        })
      });
      
      if (response.ok) {
        alert('Theater updated successfully!');
        setEditingTheater(null);
        fetchData();
      }
    } catch (error) {
      console.error('Error updating theater:', error);
    }
  };

  const deleteTheater = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this theater?')) return;
    
    try {
      const response = await fetch(`http://localhost:8000/admin/theaters/${id}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        alert('Theater deleted successfully!');
        fetchData();
      }
    } catch (error) {
      console.error('Error deleting theater:', error);
    }
  };

  const deleteShowtime = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this showtime?')) return;
    
    try {
      const response = await fetch(`http://localhost:8000/admin/showtimes/${id}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        alert('Showtime deleted successfully!');
        fetchData();
      }
    } catch (error) {
      console.error('Error deleting showtime:', error);
    }
  };

  const createTheater = async () => {
    try {
      const theaterData = {
        ...newTheater,
        non_selectable_seats: newTheater.non_selectable_seats.split(',').map(s => s.trim()).filter(s => s)
      };
      
      const response = await fetch('http://localhost:8000/admin/theaters', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(theaterData)
      });
      
      if (response.ok) {
        alert('Theater created successfully!');
        setNewTheater({ name: '', address: '', rows: 11, left_cols: 8, right_cols: 6, non_selectable_seats: '' });
        fetchData();
      }
    } catch (error) {
      console.error('Error creating theater:', error);
    }
  };

  const createShowtime = async () => {
    try {
      const response = await fetch('http://localhost:8000/admin/showtimes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newShowtime)
      });
      
      if (response.ok) {
        alert('Showtime created successfully!');
        setNewShowtime({ movie_id: 0, theater_id: 0, show_date: '', show_time: '', price: 200000 });
        fetchData();
      }
    } catch (error) {
      console.error('Error creating showtime:', error);
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>🎬 Cinema Management</h1>
      
      <div style={{ marginBottom: '20px' }}>
        {['movies', 'theaters', 'showtimes'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab as any)}
            style={{
              padding: '10px 20px',
              marginRight: '10px',
              background: activeTab === tab ? '#2196F3' : '#f0f0f0',
              color: activeTab === tab ? 'white' : 'black',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer'
            }}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {activeTab === 'movies' && (
        <div>
          <h2>🎭 Movies</h2>
          
          <div style={{ background: '#f9f9f9', padding: '20px', borderRadius: '10px', marginBottom: '20px' }}>
            <h3>Add New Movie</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
              <input
                type="text"
                placeholder="Movie Title"
                value={newMovie.title}
                onChange={(e) => setNewMovie({...newMovie, title: e.target.value})}
                style={{ padding: '10px', borderRadius: '5px', border: '1px solid #ddd' }}
              />
              <input
                type="url"
                placeholder="Poster URL"
                value={newMovie.poster_url}
                onChange={(e) => setNewMovie({...newMovie, poster_url: e.target.value})}
                style={{ padding: '10px', borderRadius: '5px', border: '1px solid #ddd' }}
              />
              <input
                type="number"
                placeholder="Duration (minutes)"
                value={newMovie.duration_minutes}
                onChange={(e) => setNewMovie({...newMovie, duration_minutes: parseInt(e.target.value)})}
                style={{ padding: '10px', borderRadius: '5px', border: '1px solid #ddd' }}
              />
              <input
                type="text"
                placeholder="Genre"
                value={newMovie.genre}
                onChange={(e) => setNewMovie({...newMovie, genre: e.target.value})}
                style={{ padding: '10px', borderRadius: '5px', border: '1px solid #ddd' }}
              />
              <input
                type="text"
                placeholder="Rating (PG-13, R, etc.)"
                value={newMovie.rating}
                onChange={(e) => setNewMovie({...newMovie, rating: e.target.value})}
                style={{ padding: '10px', borderRadius: '5px', border: '1px solid #ddd' }}
              />
            </div>
            <button
              onClick={createMovie}
              style={{ marginTop: '15px', padding: '10px 20px', background: '#4CAF50', color: 'white', border: 'none', borderRadius: '5px' }}
            >
              Add Movie
            </button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
            {movies.map(movie => (
              <div key={movie.id} style={{ border: '1px solid #ddd', borderRadius: '10px', padding: '15px', position: 'relative' }}>
                {editingMovie?.id === movie.id ? (
                  <div>
                    <input
                      type="text"
                      value={editingMovie.title}
                      onChange={(e) => setEditingMovie({...editingMovie, title: e.target.value})}
                      style={{ width: '100%', padding: '5px', marginBottom: '10px', border: '1px solid #ddd', borderRadius: '3px' }}
                    />
                    <input
                      type="url"
                      value={editingMovie.poster_url}
                      onChange={(e) => setEditingMovie({...editingMovie, poster_url: e.target.value})}
                      placeholder="Poster URL"
                      style={{ width: '100%', padding: '5px', marginBottom: '10px', border: '1px solid #ddd', borderRadius: '3px' }}
                    />
                    <input
                      type="number"
                      value={editingMovie.duration_minutes}
                      onChange={(e) => setEditingMovie({...editingMovie, duration_minutes: parseInt(e.target.value)})}
                      style={{ width: '100%', padding: '5px', marginBottom: '10px', border: '1px solid #ddd', borderRadius: '3px' }}
                    />
                    <input
                      type="text"
                      value={editingMovie.genre}
                      onChange={(e) => setEditingMovie({...editingMovie, genre: e.target.value})}
                      placeholder="Genre"
                      style={{ width: '100%', padding: '5px', marginBottom: '10px', border: '1px solid #ddd', borderRadius: '3px' }}
                    />
                    <input
                      type="text"
                      value={editingMovie.rating}
                      onChange={(e) => setEditingMovie({...editingMovie, rating: e.target.value})}
                      placeholder="Rating"
                      style={{ width: '100%', padding: '5px', marginBottom: '10px', border: '1px solid #ddd', borderRadius: '3px' }}
                    />
                    <div style={{ display: 'flex', gap: '10px' }}>
                      <button onClick={updateMovie} style={{ padding: '5px 10px', background: '#4CAF50', color: 'white', border: 'none', borderRadius: '3px' }}>Save</button>
                      <button onClick={() => setEditingMovie(null)} style={{ padding: '5px 10px', background: '#666', color: 'white', border: 'none', borderRadius: '3px' }}>Cancel</button>
                    </div>
                  </div>
                ) : (
                  <div>
                    {movie.poster_url && (
                      <img src={movie.poster_url} alt={movie.title} style={{ width: '100%', height: '200px', objectFit: 'cover', borderRadius: '5px' }} />
                    )}
                    <h3>{movie.title}</h3>
                    <p>Duration: {movie.duration_minutes} min</p>
                    <p>Genre: {movie.genre}</p>
                    <p>Rating: {movie.rating}</p>
                    <div style={{ position: 'absolute', top: '10px', right: '10px', display: 'flex', gap: '5px' }}>
                      <button
                        onClick={() => setEditingMovie(movie)}
                        style={{ background: '#2196F3', color: 'white', border: 'none', borderRadius: '50%', width: '30px', height: '30px', cursor: 'pointer' }}
                      >
                        ✎
                      </button>
                      <button
                        onClick={() => deleteMovie(movie.id)}
                        style={{ background: '#f44336', color: 'white', border: 'none', borderRadius: '50%', width: '30px', height: '30px', cursor: 'pointer' }}
                      >
                        ×
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'theaters' && (
        <div>
          <h2>🏢 Theaters</h2>
          
          <div style={{ background: '#f9f9f9', padding: '20px', borderRadius: '10px', marginBottom: '20px' }}>
            <h3>Add New Theater</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
              <input
                type="text"
                placeholder="Theater Name"
                value={newTheater.name}
                onChange={(e) => setNewTheater({...newTheater, name: e.target.value})}
                style={{ padding: '10px', borderRadius: '5px', border: '1px solid #ddd' }}
              />
              <input
                type="text"
                placeholder="Address"
                value={newTheater.address}
                onChange={(e) => setNewTheater({...newTheater, address: e.target.value})}
                style={{ padding: '10px', borderRadius: '5px', border: '1px solid #ddd' }}
              />
              <input
                type="number"
                placeholder="Rows"
                value={newTheater.rows}
                onChange={(e) => setNewTheater({...newTheater, rows: parseInt(e.target.value)})}
                style={{ padding: '10px', borderRadius: '5px', border: '1px solid #ddd' }}
              />
              <input
                type="number"
                placeholder="Left Columns"
                value={newTheater.left_cols}
                onChange={(e) => setNewTheater({...newTheater, left_cols: parseInt(e.target.value)})}
                style={{ padding: '10px', borderRadius: '5px', border: '1px solid #ddd' }}
              />
              <input
                type="number"
                placeholder="Right Columns"
                value={newTheater.right_cols}
                onChange={(e) => setNewTheater({...newTheater, right_cols: parseInt(e.target.value)})}
                style={{ padding: '10px', borderRadius: '5px', border: '1px solid #ddd' }}
              />
              <input
                type="text"
                placeholder="Disabled Seats (A1,A2,B1)"
                value={newTheater.non_selectable_seats}
                onChange={(e) => setNewTheater({...newTheater, non_selectable_seats: e.target.value})}
                style={{ padding: '10px', borderRadius: '5px', border: '1px solid #ddd' }}
              />
            </div>
            <button
              onClick={createTheater}
              style={{ marginTop: '15px', padding: '10px 20px', background: '#4CAF50', color: 'white', border: 'none', borderRadius: '5px' }}
            >
              Add Theater
            </button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(400px, 1fr))', gap: '20px' }}>
            {theaters.map(theater => (
              <div key={theater.id} style={{ border: '1px solid #ddd', borderRadius: '10px', padding: '15px', position: 'relative' }}>
                {editingTheater?.id === theater.id ? (
                  <div>
                    <input
                      type="text"
                      value={editingTheater.name}
                      onChange={(e) => setEditingTheater({...editingTheater, name: e.target.value})}
                      style={{ width: '100%', padding: '5px', marginBottom: '10px', border: '1px solid #ddd', borderRadius: '3px' }}
                    />
                    <input
                      type="text"
                      value={editingTheater.address}
                      onChange={(e) => setEditingTheater({...editingTheater, address: e.target.value})}
                      placeholder="Address"
                      style={{ width: '100%', padding: '5px', marginBottom: '10px', border: '1px solid #ddd', borderRadius: '3px' }}
                    />
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '10px', marginBottom: '10px' }}>
                      <input
                        type="number"
                        value={editingTheater.rows}
                        onChange={(e) => setEditingTheater({...editingTheater, rows: parseInt(e.target.value)})}
                        placeholder="Rows"
                        style={{ padding: '5px', border: '1px solid #ddd', borderRadius: '3px' }}
                      />
                      <input
                        type="number"
                        value={editingTheater.left_cols}
                        onChange={(e) => setEditingTheater({...editingTheater, left_cols: parseInt(e.target.value)})}
                        placeholder="Left Cols"
                        style={{ padding: '5px', border: '1px solid #ddd', borderRadius: '3px' }}
                      />
                      <input
                        type="number"
                        value={editingTheater.right_cols}
                        onChange={(e) => setEditingTheater({...editingTheater, right_cols: parseInt(e.target.value)})}
                        placeholder="Right Cols"
                        style={{ padding: '5px', border: '1px solid #ddd', borderRadius: '3px' }}
                      />
                    </div>
                    <input
                      type="text"
                      value={editingTheater.non_selectable_seats?.join(', ') || ''}
                      onChange={(e) => setEditingTheater({...editingTheater, non_selectable_seats: e.target.value.split(',').map(s => s.trim()).filter(s => s)})}
                      placeholder="Disabled Seats (A1,A2,B1)"
                      style={{ width: '100%', padding: '5px', marginBottom: '10px', border: '1px solid #ddd', borderRadius: '3px' }}
                    />
                    <div style={{ display: 'flex', gap: '10px' }}>
                      <button onClick={updateTheater} style={{ padding: '5px 10px', background: '#4CAF50', color: 'white', border: 'none', borderRadius: '3px' }}>Save</button>
                      <button onClick={() => setEditingTheater(null)} style={{ padding: '5px 10px', background: '#666', color: 'white', border: 'none', borderRadius: '3px' }}>Cancel</button>
                    </div>
                  </div>
                ) : (
                  <div>
                    <h3>{theater.name}</h3>
                    <p><strong>Address:</strong> {theater.address}</p>
                    <p><strong>Layout:</strong> {theater.rows} rows, {theater.left_cols + theater.right_cols} seats per row</p>
                    <p><strong>Disabled Seats:</strong> {theater.non_selectable_seats?.join(', ') || 'None'}</p>
                    <div style={{ position: 'absolute', top: '10px', right: '10px', display: 'flex', gap: '5px' }}>
                      <button
                        onClick={() => setEditingTheater(theater)}
                        style={{ background: '#2196F3', color: 'white', border: 'none', borderRadius: '50%', width: '30px', height: '30px', cursor: 'pointer' }}
                      >
                        ✎
                      </button>
                      <button
                        onClick={() => deleteTheater(theater.id)}
                        style={{ background: '#f44336', color: 'white', border: 'none', borderRadius: '50%', width: '30px', height: '30px', cursor: 'pointer' }}
                      >
                        ×
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'showtimes' && (
        <div>
          <h2>🕐 Showtimes</h2>
          
          <div style={{ background: '#f9f9f9', padding: '20px', borderRadius: '10px', marginBottom: '20px' }}>
            <h3>Add New Showtime</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
              <select
                value={newShowtime.movie_id}
                onChange={(e) => setNewShowtime({...newShowtime, movie_id: parseInt(e.target.value)})}
                style={{ padding: '10px', borderRadius: '5px', border: '1px solid #ddd' }}
              >
                <option value={0}>Select Movie</option>
                {movies.map(movie => (
                  <option key={movie.id} value={movie.id}>{movie.title}</option>
                ))}
              </select>
              <select
                value={newShowtime.theater_id}
                onChange={(e) => setNewShowtime({...newShowtime, theater_id: parseInt(e.target.value)})}
                style={{ padding: '10px', borderRadius: '5px', border: '1px solid #ddd' }}
              >
                <option value={0}>Select Theater</option>
                {theaters.map(theater => (
                  <option key={theater.id} value={theater.id}>{theater.name}</option>
                ))}
              </select>
              <input
                type="date"
                value={newShowtime.show_date}
                onChange={(e) => setNewShowtime({...newShowtime, show_date: e.target.value})}
                style={{ padding: '10px', borderRadius: '5px', border: '1px solid #ddd' }}
              />
              <input
                type="time"
                value={newShowtime.show_time}
                onChange={(e) => setNewShowtime({...newShowtime, show_time: e.target.value})}
                style={{ padding: '10px', borderRadius: '5px', border: '1px solid #ddd' }}
              />
              <input
                type="number"
                placeholder="Price"
                value={newShowtime.price}
                onChange={(e) => setNewShowtime({...newShowtime, price: parseInt(e.target.value)})}
                style={{ padding: '10px', borderRadius: '5px', border: '1px solid #ddd' }}
              />
            </div>
            <button
              onClick={createShowtime}
              style={{ marginTop: '15px', padding: '10px 20px', background: '#4CAF50', color: 'white', border: 'none', borderRadius: '5px' }}
            >
              Add Showtime
            </button>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', border: '1px solid #ddd' }}>
              <thead>
                <tr style={{ backgroundColor: '#f5f5f5' }}>
                  <th style={{ padding: '12px', border: '1px solid #ddd' }}>Movie</th>
                  <th style={{ padding: '12px', border: '1px solid #ddd' }}>Theater</th>
                  <th style={{ padding: '12px', border: '1px solid #ddd' }}>Date</th>
                  <th style={{ padding: '12px', border: '1px solid #ddd' }}>Time</th>
                  <th style={{ padding: '12px', border: '1px solid #ddd' }}>Price</th>
                  <th style={{ padding: '12px', border: '1px solid #ddd' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {showtimes.map((showtime, index) => (
                  <tr key={index}>
                    <td style={{ padding: '12px', border: '1px solid #ddd' }}>{showtime.movie_title}</td>
                    <td style={{ padding: '12px', border: '1px solid #ddd' }}>{showtime.theater_name}</td>
                    <td style={{ padding: '12px', border: '1px solid #ddd' }}>{showtime.show_date}</td>
                    <td style={{ padding: '12px', border: '1px solid #ddd' }}>{showtime.show_time}</td>
                    <td style={{ padding: '12px', border: '1px solid #ddd' }}>Rp {showtime.price.toLocaleString()}</td>
                    <td style={{ padding: '12px', border: '1px solid #ddd' }}>
                      <button
                        onClick={() => deleteShowtime(showtime.id)}
                        style={{ background: '#f44336', color: 'white', border: 'none', borderRadius: '3px', padding: '5px 10px', cursor: 'pointer' }}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminManagement;