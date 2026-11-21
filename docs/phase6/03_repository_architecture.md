# MSGI ONE — ASYNCHRONOUS REPOSITORY ARCHITECTURE SPECIFICATION (GATE 6.2)
**Project Title:** MSGI One — Agentic AI-Powered Institutional Alumni Ecosystem  
**Phase:** 6 — PostgreSQL Persistence, Async Repository Architecture, and Legacy Android Compatibility  
**Document ID:** `docs/phase6/03_repository_architecture.md`  
**Execution Standard:** Executive Engineering Directive v2.0  
**Audit Baseline Commit:** `9b29883`  
**Status:** COMPLETE / VERIFIED  

---

## 1. Architectural Foundation & Theoretical Principles

The repository layer of MSGI One provides an asynchronous, strongly-typed abstraction between the FastAPI domain services and the underlying Supabase PostgreSQL database.

### 1.1 Academic Engineering Grounding
- **Martin Fowler — *Patterns of Enterprise Application Architecture*:**
  - *The Repository Pattern (Fowler, p. 322):* Mediates between the domain and data mapping layers using a collection-like interface for accessing domain objects. Decouples business logic from SQL dialect specifics, connection parameters, and transaction management.
  - *Unit of Work Pattern (Fowler, p. 184):* Maintained via SQLAlchemy 2.0 `AsyncSession`, coordinating transaction boundaries, dirty tracking, and flush cycles.
- **Ian Sommerville — *Software Engineering* (10th Edition):**
  - *Layered Architecture & Separation of Concerns (Sommerville, Ch. 6):* Strict isolation between Presentation (FastAPI APIRouters), Domain Services (Business Validation & Policy), and Data Access (Repositories & ORM).
- **Abraham Silberschatz et al. — *Database System Concepts* (7th Edition):**
  - *Transaction Management & ACID Guarantees (Silberschatz, Ch. 14):* Every mutation occurs within an explicit transaction context with automatic rollback upon unhandled exceptions.

---

## 2. Component Hierarchy and Layering

```
+-------------------------------------------------------------+
| Layer A: Mobile Client (Expo SDK 52 / React Native)        |
| - Sends requests with dual prefix: /api/v1 or /api/v1/api/v1|
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
| Layer B: API Routing Layer (FastAPI APIRouters)            |
| - Parameter parsing, Pydantic schema validation             |
| - Dependency Injection: Depends(get_current_user),          |
|   Depends(get_db) -> AsyncSession                           |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
| Layer C: Domain Service Layer (src/services/)               |
| - Business policies, FERPA/GDPR privacy masking             |
| - Skill overlap evaluation, verification logic              |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
| Layer D: Asynchronous Repository Layer (src/repositories/)  |
| - BaseRepository[T] (Generic CRUD, pagination, filtering)   |
| - Domain Repositories (UserRepository, AlumniRepository,    |
|   JobsRepository, MentorRepository, EventsRepository, etc.) |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
| Layer E: Object-Relational Mapping (src/db/models/)         |
| - Declarative SQLAlchemy 2.0 Models (38 Tables)             |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
| Layer F: PostgreSQL 17 (Supabase Staging / AWS Pooler)      |
| - PgBouncer Transaction Mode (port 6543)                    |
| - RLS Policies, Constraints, Triggers, Vector Embeddings    |
+-------------------------------------------------------------+
```

---

## 3. Session & Connection Management

The async database connection is managed in `services/api/src/db/session.py`:
```python
connect_args = {}
if settings.DATABASE_URL.startswith("postgresql"):
    import ssl
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    connect_args = {"statement_cache_size": 0, "ssl": ssl_ctx}

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    connect_args=connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)
```

### 3.1 PgBouncer Statement Cache Configuration
Because Supabase connects via PgBouncer in transaction pooling mode (port 6543), prepared statements across different physical connections will fail if cached on the client. MSGI One explicitly configures `statement_cache_size: 0` on the asyncpg driver, preventing `DuplicatePreparedStatementError` during high-concurrency connection pooling.

---

## 4. Repository Inventory & Capabilities

1. **`BaseRepository[ModelT]` (`src/repositories/base.py`):**
   - `get_by_id(entity_id)`: Fetches a single entity by primary key.
   - `list(limit, offset, **filters)`: Generic filtered query with offset/limit pagination.
   - `count(**filters)`: Aggregate record count.
   - `create(**kwargs)`: Stages a new entity in the Unit of Work.
   - `update(entity_id, **kwargs)`: Updates permitted attributes and flushes.
   - `delete(entity_id)`: Removes entity within transaction.
2. **`UserRepository` (`src/repositories/user_repository.py`):**
   - Eager-loading of `user_roles`, `role`, `student_profile`, `alumni_profile`, `preferences`.
   - Email uniqueness lookups and profile field updates.
3. **`AlumniRepository` (`src/repositories/alumni_repository.py`):**
   - Multi-parameter search across major, company, industry, country, graduation year, and full text.
   - Join with `users` table for verification and active status filtering.
4. **`JobsRepository` (`src/repositories/jobs_repository.py`):**
   - Search active opportunities with deadline filtering.
   - Enforce duplicate application prevention via `UNIQUE(job_id, applicant_id)`.
5. **`MentorRepository` (`src/repositories/mentor_repository.py`):**
   - Query mentors with `is_accepting_requests == True` and capacity validation (`current_active_mentees < max_active_mentees`).
   - Enforce pending request uniqueness.
6. **`EventsRepository` (`src/repositories/events_repository.py`):**
   - Search upcoming events with end_time validation.
   - Transactional user registration with capacity increment.
7. **`LearningRepository` (`src/repositories/learning_repository.py`):**
   - Courseware discovery, user enrollment tracking, and completion updates.
8. **`CommunityRepository` (`src/repositories/community_repository.py`):**
   - Slug resolution, member count tracking, and membership lifecycle.
9. **`AdminRepository` (`src/repositories/admin_repository.py`):**
   - Verification queue management and immutable admin action audit logging.
10. **`NotificationsRepository` (`src/repositories/notifications_repository.py`):**
    - Owner-isolated notification delivery and read receipt stamping.

---

## 5. Architectural Verification

Execution verification of the repository module imports:
```powershell
cd msgi-one/services/api; .venv/Scripts/python -c "import src.repositories as r; print(len(r.__all__))"
```
**Output:** 10 registered repository classes `[V-EXEC]`.
Gate 6.2 is formally marked **PASSED**.
