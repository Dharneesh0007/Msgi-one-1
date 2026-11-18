# MSGI One — Agent Tool Contracts & Schema Registry

**Project Title:** MSGI One — Agentic AI-Powered Institutional Alumni Ecosystem  
**Phase:** Phase 0 — Project Foundation and Architecture Lock  
**Author:** AI Systems Architect & Senior Full-Stack Engineer  
**Date:** November 18, 2026  
**Status:** APPROVED & LOCKED  

---

## 1. Tool Execution Security Principles

Following **Sommerville** (*Software Engineering*, Ch. 7) and DevSecOps guidelines:
1. **Schema Guardrails:** Every tool invoked by an LLM agent requires a formal Pydantic schema for both its parameters (`ToolInput`) and return payload (`ToolOutput`). Unrecognized or malformed arguments raise validation errors before reaching domain services.
2. **Read vs Mutation Separation:** Read-only tools execute synchronously and return immediately. Consequential mutation tools do **not** execute immediately; they draft an `ActionDraft` and trigger a workflow interruption.
3. **Identity Derivation:** The executing user's UUID is injected by the FastAPI session context, never accepted as an LLM tool parameter.

---

## 2. Pydantic Tool Registry

### 2.1 Alumni Discovery Tool: `search_alumni_vector`
- **Owner Agent:** Alumni Discovery Agent
- **Domain Service:** `AlumniService.search_alumni(query, filters, current_user)`
- **Input Schema:**
  ```python
  from pydantic import BaseModel, Field
  from typing import Optional, List

  class SearchAlumniInput(BaseModel):
      query: str = Field(description="Natural language career or domain query, e.g. 'AI engineer in Japan'")
      target_country: Optional[str] = Field(default=None, description="ISO 2-letter country code or country name")
      required_skills: List[str] = Field(default_factory=list, description="Specific competencies to filter by")
      limit: int = Field(default=5, ge=1, le=20, description="Maximum candidate profiles to return")
  ```
- **Output Schema:**
  ```python
  class AlumniCandidate(BaseModel):
      alumni_id: str
      name: str
      headline: str
      current_company: Optional[str]
      location: str
      matched_skills: List[str]
      similarity_score: float
      is_available_mentor: bool

  class SearchAlumniOutput(BaseModel):
      total_matches: int
      candidates: List[AlumniCandidate]
  ```

---

### 2.2 Mentor Ranking Tool: `rank_available_mentors`
- **Owner Agent:** Mentor Matching Agent
- **Domain Service:** `MentorService.rank_mentors(goal, candidate_ids)`
- **Input Schema:**
  ```python
  class RankMentorsInput(BaseModel):
      mentee_goal: str = Field(description="Specific goal or career objective of the student")
      candidate_alumni_ids: List[str] = Field(description="List of alumni UUIDs from discovery step")
      topic: Optional[str] = Field(default=None, description="Specific mentorship topic area")
  ```
- **Output Schema:**
  ```python
  class RankedMentor(BaseModel):
      mentor_profile_id: str
      alumni_name: str
      company: str
      topics: List[str]
      available_slots: int
      match_rationale: str
      fit_score: float

  class RankMentorsOutput(BaseModel):
      ranked_mentors: List[RankedMentor]
  ```

---

### 2.3 Career & Internship Search Tool: `search_verified_jobs`
- **Owner Agent:** Career Agent
- **Domain Service:** `CareerService.search_jobs(title, location, type)`
- **Input Schema:**
  ```python
  class SearchJobsInput(BaseModel):
      role_keyword: str = Field(description="Target role title, e.g. 'Machine Learning Intern'")
      location: Optional[str] = Field(default=None, description="Target city or country")
      employment_type: str = Field(default="internship", description="'internship' or 'full_time'")
      limit: int = Field(default=5, ge=1, le=15)
  ```
- **Output Schema:**
  ```python
  class JobListing(BaseModel):
      job_id: str
      title: str
      company_name: str
      location: str
      required_skills: List[str]
      deadline: str
      application_url: str

  class SearchJobsOutput(BaseModel):
      jobs: List[JobListing]
  ```

---

### 2.4 Skill Gap Analysis Tool: `analyze_skill_gaps`
- **Owner Agent:** Learning Agent
- **Domain Service:** `LearningService.calculate_gap(student_skills, target_role_skills)`
- **Input Schema:**
  ```python
  class SkillGapInput(BaseModel):
      student_current_skills: List[str] = Field(description="Skills currently possessed by the student")
      target_role: str = Field(description="Target industry role")
  ```
- **Output Schema:**
  ```python
  class CourseRecommendation(BaseModel):
      course_id: str
      title: str
      provider: str
      difficulty: str
      addressed_skill: str

  class SkillGapOutput(BaseModel):
      missing_skills: List[str]
      recommended_learning_path: List[CourseRecommendation]
  ```

---

### 2.5 Consequential Action Tool: `draft_mentorship_request` (Approval Gate Trigger)
- **Owner Agent:** Mentor Matching Agent
- **Domain Service:** `MentorService.draft_request(mentee_id, mentor_id, statement)`
- **Input Schema:**
  ```python
  class DraftMentorRequestInput(BaseModel):
      mentor_profile_id: str = Field(description="Target mentor profile UUID")
      goal_statement: str = Field(description="Tailored personal statement explaining why this mentor was chosen")
  ```
- **Output Schema:**
  ```python
  class DraftMentorRequestOutput(BaseModel):
      approval_required: bool = True
      action_type: str = "send_mentor_request"
      target_mentor_name: str
      draft_payload: dict
      message: str = "Mentorship request drafted. Awaiting student confirmation."
  ```
- **Side Effect:** Halts LangGraph execution; writes pending approval to `public.approval_requests`.
