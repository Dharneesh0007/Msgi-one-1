/**
 * MSGI One — Shared API Contract & Data Types
 * Aligns strictly with docs/API_CONTRACT.md and Phase 2 Backend/Mobile implementations.
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

// =====================================================================
// PHASE 2 BUSINESS ENTITY CONTRACTS
// =====================================================================

export interface AlumniDirectoryItem {
  id: string;
  user_id: string;
  full_name: string;
  avatar_url?: string | null;
  graduation_year: number;
  degree: string;
  major: string;
  headline?: string | null;
  current_company?: string | null;
  current_title?: string | null;
  industry?: string | null;
  country?: string | null;
  city?: string | null;
  skills: string[];
  is_verified: boolean;
  mentor_opt_in: boolean;
}

export interface SkillOverlapResult {
  match_percentage: number;
  matched_skills: string[];
  missing_skills: string[];
}

export interface JobOpportunity {
  id: string;
  title: string;
  company: string;
  location: string;
  country: string;
  opportunity_type: 'full_time' | 'internship' | 'contract' | 'part_time';
  workplace_type: 'remote' | 'hybrid' | 'onsite';
  description: string;
  requirements: string[];
  required_skills: string[];
  application_deadline?: string | null;
  is_active: boolean;
  is_verified_listing: boolean;
  alumni_referral_available: boolean;
  alumni_count_at_company: number;
  skill_overlap?: SkillOverlapResult | null;
  created_at: string;
}

export interface JobApplication {
  id: string;
  job_id: string;
  job_title: string;
  company: string;
  applicant_id: string;
  status: 'submitted' | 'under_review' | 'interviewing' | 'accepted' | 'rejected' | 'withdrawn';
  cover_note?: string | null;
  submitted_at: string;
}

export interface MentorProfile {
  id: string;
  user_id: string;
  full_name: string;
  headline: string;
  current_company: string;
  current_title: string;
  country: string;
  advisory_topics: string[];
  is_accepting_requests: boolean;
  max_active_mentees: number;
  current_active_mentees: number;
  available_slots: number;
  match_score?: number | null;
}

export interface MentorRequest {
  id: string;
  mentor_id: string;
  mentor_name: string;
  mentor_company: string;
  student_id: string;
  student_name: string;
  topic: string;
  career_goal: string;
  message?: string | null;
  status: 'pending' | 'accepted' | 'rejected' | 'completed' | 'cancelled';
  mentor_notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface EventItem {
  id: string;
  title: string;
  event_type: 'webinar' | 'reunion' | 'workshop' | 'career_fair' | 'conference';
  description: string;
  location: string;
  is_virtual: boolean;
  meeting_url?: string | null;
  start_time: string;
  end_time: string;
  max_capacity: number;
  current_registrations: number;
  available_seats: number;
  is_published: boolean;
  is_registered: boolean;
  organizer_name: string;
}

export interface EventRegistration {
  id: string;
  event_id: string;
  event_title: string;
  user_id: string;
  status: 'confirmed' | 'attended' | 'cancelled';
  ticket_code: string;
  registered_at: string;
}

export interface RegionalLocation {
  country: string;
  city: string;
  alumni_count: number;
  is_active_chapter: boolean;
}

export interface AlumniChapter {
  id: string;
  name: string;
  city: string;
  country: string;
  region: string;
  lead_alumni_name?: string | null;
  description?: string | null;
  member_count: number;
}

// ============================================================================
// PHASE 3 — AGENTIC AI COMMAND CENTRE CONTRACTS
// ============================================================================

export interface ApprovalItem {
  id: string;
  run_id: string;
  user_id: string;
  action_type: 'send_mentor_request' | 'apply_job' | 'register_event';
  target_entity_id: string;
  target_entity_name: string;
  status: 'pending' | 'approved' | 'rejected' | 'expired';
  decision_note?: string | null;
  decided_at?: string | null;
  created_at: string;
  execution_result?: Record<string, unknown> | null;
}

export interface SkillGapItem {
  skill_name: string;
  required_level: string;
  importance_weight: number;
  category: string;
}

export interface SkillGapAnalysis {
  target_role: string;
  match_percentage: number;
  covered_skills: SkillGapItem[];
  missing_skills: SkillGapItem[];
  total_required_skills: number;
  missing_skills_count: number;
}

export interface LearningRoadmapStep {
  step: number;
  skill: string;
  course_title: string;
  provider: string;
  difficulty: string;
  duration_hours: number;
  url: string;
  rating: number;
}

export interface AIChatRequest {
  prompt: string;
  session_id?: string;
}

export interface AIChatResponse {
  session_id: string;
  status: 'running' | 'interrupted' | 'completed' | 'rejected' | 'failed';
  intent: 'alumni' | 'career' | 'mentorship' | 'events' | 'orchestrator' | 'rejected';
  target_role?: string | null;
  skill_gap?: SkillGapAnalysis | null;
  learning_roadmap?: LearningRoadmapStep[] | null;
  recommended_mentors?: MentorProfile[] | null;
  recommended_jobs?: JobOpportunity[] | null;
  recommended_events?: EventItem[] | null;
  alumni_matches?: AlumniDirectoryItem[] | null;
  pending_approval?: ApprovalItem | null;
  final_summary: string;
  evidence: Array<Record<string, unknown>>;
  action_logs: Array<Record<string, unknown>>;
  latency_ms: number;
  total_tokens: number;
}

export interface ApprovalDecisionRequest {
  decision: 'approved' | 'rejected';
  decision_note?: string;
}
