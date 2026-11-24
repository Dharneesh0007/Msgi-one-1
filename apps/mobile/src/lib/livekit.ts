/**
 * MSGI One — LiveKit WebRTC Native Integration Guard (Phase 7)
 * Isolates native WebRTC initialization cleanly so Expo Go / Web / Metro export never crash,
 * while EAS / Expo Dev Builds initialize full WebRTC audio, video, and screen sharing.
 */

import { Platform } from 'react-native';

export const ENABLE_SCREEN_SHARE_NATIVE = Platform.OS === 'android';

let globalsRegistered = false;

export function initLiveKitGlobals(): boolean {
  if (globalsRegistered || Platform.OS === 'web') {
    return globalsRegistered;
  }
  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const lk = require('@livekit/react-native');
    if (lk && typeof lk.registerGlobals === 'function') {
      lk.registerGlobals();
      globalsRegistered = true;
      return true;
    }
  } catch {
    // Expected when running inside Expo Go without native WebRTC binary
  }
  return false;
}

export function isLiveKitNativeAvailable(): boolean {
  if (Platform.OS === 'web') return false;
  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const lk = require('@livekit/react-native');
    return Boolean(lk && lk.LiveKitRoom);
  } catch {
    return false;
  }
}
