import React, { createContext, useContext, useState, useEffect } from 'react';
import { authService, setAuthToken, setUnauthorizedCallback } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check if user has token and load profile
  useEffect(() => {
    // Register the 401 logout callback
    setUnauthorizedCallback(() => {
      console.warn('[AuthContext] 401 Unauthorized detected, logging out user.');
      setUser(null);
    });

    const initAuth = async () => {
      const token = localStorage.getItem('capitallens_token');
      if (token) {
        try {
          const profile = await authService.getCurrentUser();
          setUser(profile);
        } catch (error) {
          console.warn('Session init failed, clearing token.');
          setAuthToken(null);
          setUser(null);
        }
      } else {
        setUser(null);
      }
      setLoading(false);
    };

    // Safety timeout: if backend is slow/down, resolve loading state
    const timeout = setTimeout(() => {
      console.warn('[AuthContext] Init timed out after 30s.');
      setUser(null);
      setLoading(false);
    }, 30000);

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
