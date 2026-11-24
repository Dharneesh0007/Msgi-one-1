/**
 * MSGI One — Offline Read Cache & Pending Mutation Outbox (Phase 9)
 * Invariant (Kleppmann / Directive Phase 9):
 *   Queued offline actions remain strictly marked 'queued_offline' and are
 *   NEVER falsely displayed as confirmed meetings or sent messages until verified by server.
 */

import AsyncStorage from '@react-native-async-storage/async-storage';

export interface OfflineQueuedAction {
  id: string;
  userId: string;
  kind: 'send_message' | 'meeting_feedback';
  payload: Record<string, any>;
  status: 'queued_offline';
  createdAt: string;
}

export async function saveOfflineReadCache<T>(userId: string, key: string, data: T): Promise<void> {
  try {
    await AsyncStorage.setItem(`msgi_cache_${userId}_${key}`, JSON.stringify({ data, savedAt: new Date().toISOString() }));
  } catch {
    // Non-fatal storage error
  }
}

export async function loadOfflineReadCache<T>(userId: string, key: string): Promise<T | null> {
  try {
    const raw = await AsyncStorage.getItem(`msgi_cache_${userId}_${key}`);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    return parsed?.data ?? null;
  } catch {
    return null;
  }
}

export async function enqueueOfflineMutation(
  userId: string,
  kind: OfflineQueuedAction['kind'],
  payload: Record<string, any>
): Promise<OfflineQueuedAction> {
  const storageKey = `msgi_offline_queue_${userId}`;
  const current = await listOfflineMutations(userId);
  const item: OfflineQueuedAction = {
    id: `q-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`,
    userId,
    kind,
    payload,
    status: 'queued_offline',
    createdAt: new Date().toISOString(),
  };
  await AsyncStorage.setItem(storageKey, JSON.stringify([...current, item]));
  return item;
}

export async function listOfflineMutations(userId: string): Promise<OfflineQueuedAction[]> {
  try {
    const raw = await AsyncStorage.getItem(`msgi_offline_queue_${userId}`);
    if (!raw) return [];
    return JSON.parse(raw) as OfflineQueuedAction[];
  } catch {
    return [];
  }
}

export async function removeOfflineMutation(userId: string, actionId: string): Promise<void> {
  const current = await listOfflineMutations(userId);
  const remaining = current.filter((x) => x.id !== actionId);
  await AsyncStorage.setItem(`msgi_offline_queue_${userId}`, JSON.stringify(remaining));
}
