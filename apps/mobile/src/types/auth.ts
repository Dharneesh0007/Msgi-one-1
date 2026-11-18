/**
 * MSGI One — Authentication and Profile TypeScript Definitions
 * Aligns strictly with docs/API_CONTRACT.md and FastAPI Pydantic v2 schemas.
 */

export interface StandardEnvelope<T> {
  status: 'success' | 'error';
  data: T | null;
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown> | null;
  } | null;
  meta: Record<string, unknown>;
  timestamp: string;
}

export type UserRole = 'student' | 'alumni' | 'faculty' | 'recruiter' | 'admin';

export interface UserPreferences {
  theme: 'system' | 'light' | 'dark';
  push_notifications_enabled: boolean;
  email_digests_enabled: boolean;
}

export interface StudentProfileSummary {
  roll_number?: string;
  department?: string;
  enrollment_year?: number;
  expected_graduation_year?: number;
  degree_program?: string;
  career_interests?: string[];
}

export interface AlumniProfileSummary {
  graduation_year?: number;
  degree?: string;
  major?: string;
  headline?: string;
  current_company?: string;
  current_title?: string;
  industry?: string;
}

export interface UserProfileResponse {
  id: string;
  email: string;
  first_name?: string | null;
  last_name?: string | null;
  avatar_url?: string | null;
  requested_role?: string;
  is_verified: boolean;
  is_active: boolean;
  roles: UserRole[];
  preferences: UserPreferences;
  student_profile?: StudentProfileSummary | null;
  alumni_profile?: AlumniProfileSummary | null;
  is_profile_complete: boolean;
}

export interface UserUpdateRequest {
  first_name?: string;
  last_name?: string;
  avatar_url?: string;
  preferences?: Partial<UserPreferences>;
}

export interface UserOnboardingRequest {
  first_name: string;
  last_name: string;
  department?: string;
  requested_role?: string;
}

export interface PublicUserProfileResponse {
  id: string;
  full_name: string;
  avatar_url?: string | null;
  role: string;
  is_verified: boolean;
  headline?: string | null;
  current_company?: string | null;
  current_title?: string | null;
  location?: string | null;
  skills: string[];
}
