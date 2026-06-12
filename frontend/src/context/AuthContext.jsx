import React, { createContext, useContext, useState, useEffect } from 'react';
import { authService, setAuthToken } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check if user has token and load profile
  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('capitallens_token');
      if (token) {
        try {
          const profile = await authService.getCurrentUser();
          setUser(profile);
        } catch (error) {
          console.warn('Session init failed, logging out and logging in guest.');
          setAuthToken(null);
          try {
            const guestSession = await authService.login('executive@capitallens.com', 'password');
            setUser(guestSession.user);
          } catch (err) {
            setUser({ id: 1, email: 'guest@capitallens.com', name: 'Executive Officer' });
          }
        }
      } else {
        // Auto-login Guest session for instant premium showcase without login barriers
        try {
          const guestSession = await authService.login('executive@capitallens.com', 'password');
          setUser(guestSession.user);
        } catch (err) {
          setUser({ id: 1, email: 'guest@capitallens.com', name: 'Executive Officer' });
        }
      }
      setLoading(false);
    };

    // Safety timeout: if backend is slow/down, never block UI forever (3 seconds max)
    const timeout = setTimeout(() => {
      console.warn('[AuthContext] Init timed out after 3s — using guest session fallback.');
      setUser({ id: 1, email: 'guest@capitallens.com', name: 'Executive Officer' });
      setLoading(false);
    }, 3000);

    initAuth().finally(() => clearTimeout(timeout));
  }, []);


  const login = async (email, password) => {
    setLoading(true);
    try {
      const session = await authService.login(email, password);
      setUser(session.user);
      return session.user;
    } catch (error) {
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const register = async (name, email, password) => {
    setLoading(true);
    try {
      const session = await authService.register(name, email, password);
      setUser(session.user);
      return session.user;
    } catch (error) {
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    authService.logout();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
