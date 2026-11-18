/**
 * MSGI One — Shared API Contract & Data Types
 */

export type UserRole = "student" | "alumni" | "faculty" | "recruiter" | "admin";

export interface UserSummary {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  avatar_url?: string;
  is_verified: boolean;
  roles: UserRole[];
}

export interface StandardApiResponse<T> {
  status: "success" | "error";
  data: T | null;
  error: ApiError | null;
  meta: Record<string, unknown>;
  timestamp: string;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Array<{ field: string; issue: string }>;
}

export interface CareerRoadmapWorkflowOutput {
  workflow_id: string;
  status: "in_progress" | "completed" | "awaiting_approval" | "failed";
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
