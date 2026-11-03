import React, { createContext, useContext, useEffect, useState } from 'react';
import { api, setAuthToken } from '../services/api';
import type { LoginRequest, RoleEnum, UserOut } from '../types';

interface AuthContextType {
  user: UserOut | null;
  token: string | null;
  restaurantName: string;
  isLoading: boolean;
  login: (data: LoginRequest) => Promise<void>;
  logout: () => void;
  hasRole: (role: RoleEnum) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserOut | null>(null);
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('serviceflow_token'));
  const [restaurantName, setRestaurantName] = useState<string>(() => localStorage.getItem('serviceflow_restaurant_name') || '');
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    async function loadUser() {
      if (token) {
        try {
          const me = await api.auth.me();
          setUser(me);
        } catch {
          setToken(null);
          setUser(null);
          setAuthToken(null);
          localStorage.removeItem('serviceflow_restaurant_name');
        }
      }
      setIsLoading(false);
    }

    loadUser();

    const handleUnauthorized = () => {
      setUser(null);
      setToken(null);
      setAuthToken(null);
      localStorage.removeItem('serviceflow_restaurant_name');
    };

    window.addEventListener('serviceflow:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('serviceflow:unauthorized', handleUnauthorized);
  }, [token]);

  const login = async (data: LoginRequest) => {
    setIsLoading(true);
    try {
      const resp = await api.auth.login(data);
      setAuthToken(resp.access_token);
      setToken(resp.access_token);
      setRestaurantName(resp.restaurant_name);
      localStorage.setItem('serviceflow_restaurant_name', resp.restaurant_name);

      const me = await api.auth.me();
      setUser(me);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    setAuthToken(null);
    setToken(null);
    setUser(null);
    setRestaurantName('');
    localStorage.removeItem('serviceflow_token');
    localStorage.removeItem('serviceflow_restaurant_name');
  };

  const hasRole = (role: RoleEnum) => user?.role === role;

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        restaurantName,
        isLoading,
        login,
        logout,
        hasRole,
      }}
    >
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
