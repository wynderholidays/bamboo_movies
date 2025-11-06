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

  // Check if page was refreshed on payment page
  React.useEffect(() => {
    const path = window.location.pathname;
    if (path.includes('/payment/') && window.performance.navigation.type === 1) {
      const showtimeId = path.match(/\/payment\/(\d+)/)?.[1];
      if (showtimeId) {
        navigate(`/booking/${showtimeId}`);
      }
    }
  }, []);

  const handleShowtimeSelect = (showtimeId: number) => {
    setSelectedShowtimeId(showtimeId);
    navigate(`/booking/${showtimeId}`);
  };

  // Reset state when navigating away from payment
  React.useEffect(() => {
    if (!currentRoute.includes('/payment/') && !currentRoute.includes('/booking/') && !currentRoute.includes('/success/')) {
      setSelectedShowtimeId(null);
    }
  }, [currentRoute]);

  React.useEffect(() => {
    const handlePopState = () => {
      setCurrentRoute(window.location.pathname);
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  React.useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (currentRoute.includes('/payment/')) {
        e.preventDefault();
        e.returnValue = 'Are you sure you want to refresh? All changes will be lost and you will be redirected to booking page.';
        return e.returnValue;
      }
    };

    const handleUnload = () => {
      if (currentRoute.includes('/payment/')) {
        const showtimeId = currentRoute.match(/\/payment\/(\d+)/)?.[1];
        if (showtimeId) {
          window.location.href = `/booking/${showtimeId}`;
        }
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    window.addEventListener('unload', handleUnload);
    
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      window.removeEventListener('unload', handleUnload);
    };
  }, [currentRoute]);

  React.useEffect(() => {
    // Extract showtime ID from URL
    const match = currentRoute.match(/\/(booking|payment|success)\/(\d+)/);
    if (match) {
      setSelectedShowtimeId(parseInt(match[2]));
    }
    
    // Handle payment page refresh redirect
    if (currentRoute.includes('/payment/') && window.performance.navigation.type === 1) {
      const showtimeId = match?.[2];
      if (showtimeId) {
        navigate(`/booking/${showtimeId}`);
      }
    }
  }, [currentRoute]);

  if (currentRoute === '/admin' || currentRoute === '/admin/login') {
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