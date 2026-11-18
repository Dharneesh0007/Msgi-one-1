/**
 * MSGI One Mobile App Entry Module
 */

export const APP_CONFIG = {
  name: 'MSGI One',
  version: '0.1.0',
  phase: 'Phase 1 — Application Foundation (Auth, Profiles, Migrations, Navigation)',
};

export * from './types/auth';
export * from './constants/theme';
export * from './context/AuthContext';
export * from './lib/api';
export * from './lib/supabase';
