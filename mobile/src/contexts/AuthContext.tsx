import React, { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { apiClient, setAuthToken, getAuthToken } from '../api/client';

export interface User {
  id: string;
  email: string;
  displayName: string;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, displayName: string, inviteCode: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const token = await getAuthToken();
        if (!token) {
          return;
        }
        const response = await apiClient.get('/api/auth/me');
        setUser(response.data);
      } catch {
        await setAuthToken(null);
      } finally {
        setIsLoading(false);
      }
    };
    checkAuth();
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const response = await apiClient.post('/api/auth/login', { email, password });
    const { access_token, user: userData } = response.data;
    await setAuthToken(access_token);
    setUser(userData);
  }, []);

  const register = useCallback(
    async (email: string, password: string, displayName: string, inviteCode: string) => {
      const response = await apiClient.post('/api/auth/register', {
        email,
        password,
        display_name: displayName,
        invite_code: inviteCode,
      });
      const { access_token, user: userData } = response.data;
      await setAuthToken(access_token);
      setUser(userData);
    },
    []
  );

  const logout = useCallback(async () => {
    await setAuthToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, isLoading, isAuthenticated: !!user, login, register, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
