/**
 * MSGI One — Mobile Phase 2 Business Module Interfaces
 * Aligns with docs/API_CONTRACT.md and services/api/src/schemas/business.py
 */

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

export interface AlumniDirectoryResponse {
  items: AlumniDirectoryItem[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
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
