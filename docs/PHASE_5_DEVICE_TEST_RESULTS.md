# MSGI ONE — PHASE 5 MOBILE SCREEN AUDIT & DEVICE TEST REPORT

**Document Reference:** `docs/PHASE_5_DEVICE_TEST_RESULTS.md`  
**Mobile Architecture:** Expo Router v4 (File-based navigation), React Native 0.76.5  
**Screen Directory:** `apps/mobile/src/app/`  
**Quality Focus:** Navigation hierarchy, SafeAreaView ergonomics, offline handling, and token management  

---

## 1. MOBILE ROUTE & SCREEN INVENTORY

| Screen File Path | Route | Domain Functionality | Form Factors / Orientations |
| :--- | :--- | :--- | :--- |
| `src/app/_layout.tsx` | Root Layout | Global AuthProvider, theme styling, stack navigator | Portrait, Dark/Light system theme |
| `src/app/(auth)/login.tsx` | `/login` | Supabase credentials login, input validation, error alerts | Portrait, keyboard avoiding view |
| `src/app/(auth)/register.tsx` | `/register` | Institutional registration with `@example.msgi.edu` | Portrait, keyboard avoiding view |
| `src/app/(tabs)/_layout.tsx` | Bottom Tabs | Tab bar routing: Home, Network, Careers, AI, Profile | Responsive bottom navigation |
| `src/app/(tabs)/index.tsx` | `/` (Home) | **Services Hub:** Direct access to all 12 modules + Notification Bell | Scrollable grid with badge indicators |
| `src/app/(tabs)/network.tsx` | `/network` | Alumni Network search, mentor discovery, chapter filters | Virtualized list with search bar |
| `src/app/(tabs)/careers.tsx` | `/careers` | CareerBridge job cards, skill overlap tags, apply modal | Virtualized list with filter chips |
| `src/app/(tabs)/ai.tsx` | `/ai` | AI Command Centre chat, HITL approval cards, agent traces | Interactive chat stream with input bar |
| `src/app/(tabs)/profile.tsx` | `/profile` | Profile details, skills inventory, account deletion button | Scrollable card layout |
| `src/app/notifications.tsx` | `/notifications` | In-app notification center, unread badges, mark as read | Virtualized list with swipe/tap to read |

---

## 2. MOBILE UX & SAFETY VERIFICATIONS

1. **SafeAreaView Compliance:**
   - All screens wrap content inside `SafeAreaView` from `react-native-safe-area-context`.
   - Prevents header content overlap with Android status bar notches or camera cutouts.

2. **Network Offline Handling:**
   - Client detects network state via NetInfo.
   - When offline, renders an unobtrusive status banner: `"Working in offline mode. Changes will sync when connected."`
   - Suppresses unhandled network exceptions and displays cached data gracefully.

3. **Secure Token Storage:**
   - Implemented via `expo-secure-store` on Android (utilizing Android Keystore encryption).
   - Tokens are never logged or stored in unencrypted `AsyncStorage`.

4. **In-App Account Deletion UI:**
   - `src/app/(tabs)/profile.tsx` includes an explicit "Delete Account & Scrub Data" button.
   - Prompts the user with a confirmation dialog and dispatches `DELETE /api/v1/users/me`.
