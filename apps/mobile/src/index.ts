/**
 * MSGI One Mobile App Entry Module
 */

export const APP_CONFIG = {
  name: 'MSGI One',
  version: '0.2.0',
  phase: 'Phase 2 — Core Connected Business Modules (Alumni, Career, Mentors, Events, Global)',
};

export * from './types/auth';
export * from './types/business';
export * from './constants/theme';
export * from './context/AuthContext';
export * from './lib/api';
export * from './lib/supabase';
