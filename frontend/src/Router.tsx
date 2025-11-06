import React, { useState } from 'react';
import BookingApp from './BookingApp';
import AdminPanel from './AdminPanel';
import ShowtimeSelection from './ShowtimeSelection';

const Router: React.FC = () => {
  const [currentRoute, setCurrentRoute] = useState(window.location.pathname);
  const [selectedShowtimeId, setSelectedShowtimeId] = useState<number | null>(null);

  const navigate = (path: string) => {
    window.history.pushState({}, '', path);
    setCurrentRoute(path);
  };

  const handleShowtimeSelect = (showtimeId: number) => {
    setSelectedShowtimeId(showtimeId);
    navigate(`/booking/${showtimeId}`);
  };

  React.useEffect(() => {
    const handlePopState = () => {
      setCurrentRoute(window.location.pathname);
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  React.useEffect(() => {
    // Extract showtime ID from URL
    const match = currentRoute.match(/\/(booking|payment|success)\/(\d+)/);
    if (match) {
      setSelectedShowtimeId(parseInt(match[2]));
    }
  }, [currentRoute]);

  if (currentRoute === '/admin') {
    return <AdminPanel navigate={navigate} />;
  }

  if (currentRoute === '/' || currentRoute === '/showtimes') {
    return <ShowtimeSelection onShowtimeSelect={handleShowtimeSelect} />;
  }

  if (currentRoute.startsWith('/booking') || currentRoute.startsWith('/payment') || currentRoute.startsWith('/success')) {
    return <BookingApp navigate={navigate} currentRoute={currentRoute} selectedShowtimeId={selectedShowtimeId} />;
  }

  return <ShowtimeSelection onShowtimeSelect={handleShowtimeSelect} />;
};

export default Router;