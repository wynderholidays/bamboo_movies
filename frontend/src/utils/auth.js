// Authentication utilities
const TOKEN_KEY = 'admin_token';

export const authUtils = {
  // Store token
  setToken: (token) => {
    localStorage.setItem(TOKEN_KEY, token);
  },

  // Get token
  getToken: () => {
    return localStorage.getItem(TOKEN_KEY);
  },

  // Remove token
  removeToken: () => {
    localStorage.removeItem(TOKEN_KEY);
  },

  // Check if user is authenticated
  isAuthenticated: () => {
    return !!localStorage.getItem(TOKEN_KEY);
  },

  // API call with authentication
  apiCall: async (url, options = {}) => {
    const token = authUtils.getToken();
    
    const config = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);
      
      // Handle authentication errors
      if (response.status === 401 || response.status === 403) {
        authUtils.removeToken();
        window.location.href = '/admin/login';
        throw new Error('Authentication failed');
      }
      
      return response;
    } catch (error) {
      console.error('API call failed:', error);
      throw error;
    }
  },

  // Logout
  logout: async () => {
    try {
      // Optional: Call backend logout endpoint
      await authUtils.apiCall('/api/admin/logout', { method: 'POST' });
    } catch (error) {
      console.log('Logout API call failed, but continuing...');
    }
    
    authUtils.removeToken();
    window.location.href = '/admin/login';
  }
};