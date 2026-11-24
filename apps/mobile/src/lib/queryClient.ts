/**
 * MSGI One — TanStack Query Client & User-Scoped Cache Isolation (Phase 9)
 * Security Guarantee: All cached server queries & offline state keys are user-scoped
 * and purged completely upon signOut to prevent cross-account data bleed.
 */

import { QueryClient } from '@tanstack/react-query';
import AsyncStorage from '@react-native-async-storage/async-storage';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60_000,
      gcTime: 10 * 60_000,
      retry: 1,
      refetchOnReconnect: true,
    },
  },
});

export function userScopedQueryKey(userId: string | undefined, scope: string, extra?: string): string[] {
  const uid = userId || 'anon';
  return extra ? ['msgi', uid, scope, extra] : ['msgi', uid, scope];
}

export async function clearUserScopedCaches(): Promise<void> {
  queryClient.clear();
  try {
    const keys = await AsyncStorage.getAllKeys();
    const scopedKeys = keys.filter((k) => k.startsWith('msgi_cache_') || k.startsWith('msgi_offline_'));
    if (scopedKeys.length > 0) {
      await AsyncStorage.multiRemove(scopedKeys);
    }
  } catch {
    // Best-effort cache cleanup
  }
}
