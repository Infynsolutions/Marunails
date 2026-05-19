import { createContext, useContext, useEffect, useState } from 'react';
import { supabase } from './supabase';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [session, setSession]     = useState(undefined); // undefined = loading
  const [tenantId, setTenantId]   = useState(null);
  const [role, setRole]           = useState(null);

  useEffect(() => {
    // Load existing session on mount
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session ?? null);
      if (session) _resolveTenant(session.access_token);
    });

    // Subscribe to auth changes (login, logout, token refresh)
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session ?? null);
      if (session) {
        _resolveTenant(session.access_token);
      } else {
        setTenantId(null);
        setRole(null);
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  async function _resolveTenant(token) {
    try {
      const API_URL = import.meta.env.VITE_API_URL ?? '';
      const res = await fetch(`${API_URL}/api/v1/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setTenantId(data.tenant_id);
        setRole(data.role);
      }
    } catch (e) {
      console.error('Failed to resolve tenant:', e);
    }
  }

  async function signIn(email, password) {
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) throw error;
  }

  async function signOut() {
    await supabase.auth.signOut();
  }

  const loading = session === undefined;

  return (
    <AuthContext.Provider value={{ session, tenantId, role, loading, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
