"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  ReactNode,
} from 'react';
import {
  isAuthenticated,
  loginRequest,
  logoutRequest,
  refreshRequest,
  clearTokens,
  getAccessToken,
} from '@/lib/auth-client';

// ── Types ─────────────────────────────────────────────────────────────────────

interface AuthContextType {
  username: string | null;
  isLoggedIn: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

// ── Context ───────────────────────────────────────────────────────────────────

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// ── Decode username from JWT payload (no verify — informational only) ─────────

function decodeUsername(token: string | null): string | null {
  if (!token) return null;
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.sub ?? null;
  } catch {
    return null;
  }
}

// ── Provider ──────────────────────────────────────────────────────────────────

export function AuthProvider({ children }: { children: ReactNode }) {
  const [username, setUsername] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // On mount: check stored token; attempt silent refresh if expired
  useEffect(() => {
    async function init() {
      if (isAuthenticated()) {
        setUsername(decodeUsername(getAccessToken()));
        setIsLoading(false);
        return;
      }
      // Try silent refresh
      const refreshed = await refreshRequest();
      if (refreshed) {
        setUsername(decodeUsername(refreshed.access_token));
      } else {
        clearTokens();
        setUsername(null);
      }
      setIsLoading(false);
    }
    init();
  }, []);

  const login = useCallback(async (user: string, password: string) => {
    const tokens = await loginRequest(user, password);
    setUsername(decodeUsername(tokens.access_token));
  }, []);

  const logout = useCallback(async () => {
    await logoutRequest();
    setUsername(null);
    // Hard redirect so all cached query data is cleared
    window.location.href = '/login';
  }, []);

  return (
    <AuthContext.Provider
      value={{
        username,
        isLoggedIn: Boolean(username),
        isLoading,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// ── Hook ──────────────────────────────────────────────────────────────────────

export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
}
