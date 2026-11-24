/**
 * MSGI One — Expo Push Notifications Registration & Deep-Link Routing (Phase 9)
 */

import * as Notifications from 'expo-notifications';
import Constants from 'expo-constants';
import { Platform } from 'react-native';
import { api } from './api';

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
    shouldShowBanner: true,
    shouldShowList: true,
  }),
});

let _lastRegisteredToken: string | null = null;

export async function registerDeviceForPushNotifications(): Promise<string | null> {
  if (Platform.OS === 'web') return null;

  try {
    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;
    if (existingStatus !== 'granted') {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }
    if (finalStatus !== 'granted') {
      return null;
    }

    if (Platform.OS === 'android') {
      await Notifications.setNotificationChannelAsync('msgi-alerts', {
        name: 'MSGI Institutional Alerts',
        importance: Notifications.AndroidImportance.HIGH,
      });
    }

    const projectId = Constants.expoConfig?.extra?.eas?.projectId;
    const tokenRes = await Notifications.getExpoPushTokenAsync(projectId ? { projectId } : undefined);
    const token = tokenRes.data;
    if (token) {
      _lastRegisteredToken = token;
      await api.registerPushToken(token, Platform.OS === 'ios' ? 'ios' : 'android').catch(() => null);
    }
    return token || null;
  } catch {
    return null;
  }
}

export async function revokeRegisteredPushToken(): Promise<void> {
  if (!_lastRegisteredToken) return;
  const tok = _lastRegisteredToken;
  _lastRegisteredToken = null;
  await api.revokePushToken(tok).catch(() => null);
}

export function resolveNotificationTargetRoute(data: Record<string, any> | undefined): string | null {
  if (!data) return null;
  const kind = String(data.type || '');
  if (kind === 'meeting_update' || kind === 'meeting_request') return '/meetings';
  if (kind === 'chat_message' || kind === 'message') return '/messages';
  if (kind === 'ai_approval') return '/(tabs)/ai';
  if (kind === 'room_invite' && data.meeting_id) return `/room/${data.meeting_id}`;
  return '/(tabs)';
}
