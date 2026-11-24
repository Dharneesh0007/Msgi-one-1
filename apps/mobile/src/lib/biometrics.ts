/**
 * MSGI One — Biometric Lock & Secure Credential Preference (Phase 9)
 * Backed by expo-local-authentication + expo-secure-store.
 */

import * as LocalAuthentication from 'expo-local-authentication';
import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

const BIOMETRIC_PREF_KEY = 'msgi_biometric_lock_enabled';

export interface BiometricCapability {
  hasHardware: boolean;
  isEnrolled: boolean;
  types: LocalAuthentication.AuthenticationType[];
}

export async function getBiometricCapability(): Promise<BiometricCapability> {
  if (Platform.OS === 'web') {
    return { hasHardware: false, isEnrolled: false, types: [] };
  }
  try {
    const hasHardware = await LocalAuthentication.hasHardwareAsync();
    const isEnrolled = await LocalAuthentication.isEnrolledAsync();
    const types = await LocalAuthentication.supportedAuthenticationTypesAsync();
    return { hasHardware, isEnrolled, types };
  } catch {
    return { hasHardware: false, isEnrolled: false, types: [] };
  }
}

export async function isBiometricLockEnabled(): Promise<boolean> {
  try {
    const val = await SecureStore.getItemAsync(BIOMETRIC_PREF_KEY);
    return val === 'true';
  } catch {
    return false;
  }
}

export async function setBiometricLockEnabled(enabled: boolean): Promise<void> {
  try {
    if (enabled) {
      await SecureStore.setItemAsync(BIOMETRIC_PREF_KEY, 'true');
    } else {
      await SecureStore.deleteItemAsync(BIOMETRIC_PREF_KEY);
    }
  } catch {
    // Web / unsupported fallback
  }
}

export async function promptBiometricUnlock(reason: string = 'Verify your identity to access MSGI One'): Promise<boolean> {
  try {
    const cap = await getBiometricCapability();
    if (!cap.hasHardware || !cap.isEnrolled) {
      return false;
    }
    const result = await LocalAuthentication.authenticateAsync({
      promptMessage: reason,
      fallbackLabel: 'Use Device Passcode',
      cancelLabel: 'Cancel',
    });
    return result.success;
  } catch {
    return false;
  }
}
