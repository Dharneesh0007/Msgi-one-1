/**
 * MSGI One — Shared API Contract & Data Types
 * Aligns strictly with docs/API_CONTRACT.md and Phase 1 Backend/Mobile implementations.
 */

export type UserRole = 'student' | 'alumni' | 'faculty' | 'recruiter' | 'admin';

export interface StandardApiResponse<T> {
  status: 'success' | 'error';
  data: T | null;
  error: ApiError | null;
  meta: Record<string, unknown>;
  timestamp: string;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown> | null;
}

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

export interface CareerRoadmapWorkflowOutput {
  workflow_id: string;
  status: 'in_progress' | 'completed' | 'awaiting_approval' | 'failed';
  summary: {
    target_role: string;
    target_country: string;
    readiness_score: string;
  };
  matched_alumni: Array<{
    alumni_id: string;
    name: string;
    title: string;
    location: string;
    graduation_year: number;
    evidence: string;
  }>;
  mentor_recommendation?: {
    mentor_profile_id: string;
    mentor_name: string;
    match_score: number;
    available_slots: number;
    advisory_topics: string[];
  };
  skill_gap_analysis: {
    current_skills: string[];
    missing_skills: string[];
    recommended_courses: Array<{
      course_id: string;
      title: string;
      provider: string;
      estimated_duration: string;
    }>;
  };
  internship_opportunities: Array<{
    job_id: string;
    title: string;
    company: string;
    location: string;
    deadline: string;
  }>;
  pending_approval?: {
    approval_id: string;
    action_type: string;
    target: string;
    draft_message: string;
    prompt: string;
  };
}
