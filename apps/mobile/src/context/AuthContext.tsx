/**
 * MSGI One — Authentication and Authorization Context
 * Manages Supabase Auth session, JWT token state, profile synchronization,
 * and server-verified RBAC role states.
 */

import React, { createContext, useContext, useEffect, useState, useMemo } from 'react';
import { Session, User } from '@supabase/supabase-js';
import { supabase } from '../lib/supabase';
import { api, ApiError } from '../lib/api';
import { UserProfileResponse, UserRole } from '../types/auth';

interface AuthContextType {
  session: Session | null;
  authUser: User | null;
  user: UserProfileResponse | null;
  primaryRole: UserRole | 'guest';
  roles: UserRole[];
  isLoading: boolean;
  isAuthenticated: boolean;
  isProfileComplete: boolean;
  error: string | null;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, requestedRole: string) => Promise<void>;
  signOut: () => Promise<void>;
  refreshProfile: () => Promise<void>;
  completeProfile: (firstName: string, lastName: string, department?: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [authUser, setAuthUser] = useState<User | null>(null);
  const [user, setUser] = useState<UserProfileResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchProfile = async (currentSession?: Session | null) => {
    const activeToken = currentSession?.access_token || session?.access_token;
    if (!activeToken) {
      setUser(null);
      return;
    }

    try {
      const profile = await api.getMyProfile();
      setUser(profile);
    } catch (err: any) {
      console.warn('[AuthProvider] Failed to fetch server profile:', err.message);
      // Fallback synthetic profile for offline/dev state
      if (currentSession?.user) {
        setUser({
          id: currentSession.user.id,
          email: currentSession.user.email || '',
          first_name: currentSession.user.user_metadata?.first_name || null,
          last_name: currentSession.user.user_metadata?.last_name || null,
          is_verified: false,
          is_active: true,
          roles: ['student'],
          preferences: {
            theme: 'system',
            push_notifications_enabled: true,
            email_digests_enabled: true,
          },
          is_profile_complete: Boolean(
            currentSession.user.user_metadata?.first_name && currentSession.user.user_metadata?.last_name
          ),
        });
      }
    }
  };

  useEffect(() => {
    let isMounted = true;

    async function initializeAuth() {
      try {
        setIsLoading(true);
        const { data: { session: initialSession }, error: sessionError } = await supabase.auth.getSession();

        if (sessionError) {
          console.error('[AuthProvider] Error restoring session:', sessionError.message);
        }

        if (isMounted) {
          setSession(initialSession);
          setAuthUser(initialSession?.user ?? null);
          if (initialSession) {
            await fetchProfile(initialSession);
          }
        }
      } catch (err: any) {
        console.error('[AuthProvider] Initialization failed:', err);
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    initializeAuth();

    const { data: authListener } = supabase.auth.onAuthStateChange(async (event, newSession) => {
      if (!isMounted) return;

      setSession(newSession);
      setAuthUser(newSession?.user ?? null);

      if (event === 'SIGNED_IN' || event === 'TOKEN_REFRESHED') {
        if (newSession) {
          await fetchProfile(newSession);
        }
      } else if (event === 'SIGNED_OUT') {
        setUser(null);
      }
    });

    return () => {
      isMounted = false;
      authListener.subscription.unsubscribe();
    };
  }, []);

  const signIn = async (email: string, password: string) => {
    setError(null);
    setIsLoading(true);
    try {
      const { data, error: signInError } = await supabase.auth.signInWithPassword({
        email: email.trim().toLowerCase(),
        password,
      });

      if (signInError) throw signInError;
      if (data.session) {
        setSession(data.session);
        setAuthUser(data.user);
        await fetchProfile(data.session);
      }
    } catch (err: any) {
      const msg = err.message || 'Failed to sign in. Please check your credentials.';
      setError(msg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const signUp = async (email: string, password: string, requestedRole: string) => {
    setError(null);
    setIsLoading(true);
    try {
      const { data, error: signUpError } = await supabase.auth.signUp({
        email: email.trim().toLowerCase(),
        password,
        options: {
          data: {
            requested_role: requestedRole,
          },
        },
      });

      if (signUpError) throw signUpError;
      if (data.session) {
        setSession(data.session);
        setAuthUser(data.user);
        await fetchProfile(data.session);
      }
    } catch (err: any) {
      const msg = err.message || 'Failed to register account.';
      setError(msg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const signOut = async () => {
    setIsLoading(true);
    try {
      await api.logoutSession().catch(() => null);
      await supabase.auth.signOut();
      setSession(null);
      setAuthUser(null);
      setUser(null);
    } catch (err: any) {
      console.error('[AuthProvider] Sign out error:', err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const refreshProfile = async () => {
    await fetchProfile(session);
  };

  const completeProfile = async (firstName: string, lastName: string, department?: string) => {
    setIsLoading(true);
    try {
      const updated = await api.completeOnboarding({
        first_name: firstName,
        last_name: lastName,
        department,
        requested_role: user?.requested_role || 'student',
      });
      setUser(updated);
    } catch (err: any) {
      setError(err.message || 'Failed to complete profile onboarding.');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const roles = useMemo(() => user?.roles ?? [], [user]);
  const primaryRole: UserRole | 'guest' = useMemo(() => {
    if (!session || !user) return 'guest';
    if (roles.includes('admin')) return 'admin';
    if (roles.includes('faculty')) return 'faculty';
    if (roles.includes('recruiter')) return 'recruiter';
    if (roles.includes('alumni')) return 'alumni';
    return 'student';
  }, [session, user, roles]);

  const isAuthenticated = Boolean(session && session.user);
  const isProfileComplete = Boolean(user?.is_profile_complete);

  const value = {
    session,
    authUser,
    user,
    primaryRole,
    roles,
    isLoading,
    isAuthenticated,
    isProfileComplete,
    error,
    signIn,
    signUp,
    signOut,
    refreshProfile,
    completeProfile,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
