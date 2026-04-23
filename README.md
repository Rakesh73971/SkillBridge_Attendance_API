# SkillBridge Attendance API

FastAPI backend for the SkillBridge attendance management assignment.

## Live API

- Base URL: `ADD_YOUR_LIVE_BASE_URL_HERE`
- Deployment notes:
  - Public deployment is still pending
  - Recommended deployment for this project: Render/Railway/Fly.io with PostgreSQL
  - Environment variables should be configured through the hosting platform, not committed to the repo

## Local Setup

Assumptions:

- Python is installed
- `pip` is installed
- PostgreSQL is installed and running locally

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Create environment file

Copy `.env.example` to `.env` and set real values.

Required variables:

```env
DATABASE_HOSTNAME=localhost
DATABASE_PORT=5432
DATABASE_NAME=student_data_management
DATABASE_USERNAME=postgres
DATABASE_PASSWORD=your_password
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
MONITORING_API_KEY=test-api-key-123
```

### 3. Create databases

Create these PostgreSQL databases:

- `student_data_management`
- `student_data_management_test`

### 4. Run the API

```bash
uvicorn src.main:app --reload
```

### 5. Seed the database

```bash
python seed.py
```

### 6. Run tests

```bash
pytest
```

Note: the test configuration uses a real PostgreSQL test database, not SQLite.

## Test Accounts

- Student: `student1@example.com` / `student123`
- Trainer: `john.trainer@example.com` / `trainer123`
- Institution: `alice.institution@example.com` / `institution123`
- Programme Manager: `carol.progmgr@example.com` / `progmgr123`
- Monitoring Officer: `david.monitor@example.com` / `monitor123`

## Sample cURL

Replace `BASE_URL` with either:

- `http://127.0.0.1:8000` for local testing
- your deployed live URL later

### 1. Create institution

```bash
curl -X POST "BASE_URL/institutions" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"New Institute\",\"region\":\"North\"}"
```

### 2. Signup

```bash
curl -X POST "BASE_URL/auth/signup" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"Jane Student\",\"email\":\"jane.student@example.com\",\"password\":\"password123\",\"role\":\"student\",\"institution_id\":1}"
```

### 3. Login

```bash
curl -X POST "BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"john.trainer@example.com\",\"password\":\"trainer123\"}"
```

### 4. Get monitoring token

First log in as the monitoring officer and get the standard JWT. Then exchange it for the scoped monitoring token:

```bash
curl -X POST "BASE_URL/auth/monitoring-token" \
  -H "Authorization: Bearer <STANDARD_MONITORING_OFFICER_TOKEN>" \
  -H "Content-Type: application/json" \
  -d "{\"key\":\"test-api-key-123\"}"
```

### 5. Create batch

```bash
curl -X POST "BASE_URL/batches" \
  -H "Authorization: Bearer <TRAINER_OR_INSTITUTION_TOKEN>" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"Advanced Python 2026\",\"institution_id\":1}"
```

### 6. Generate batch invite

```bash
curl -X POST "BASE_URL/batches/1/invite" \
  -H "Authorization: Bearer <TRAINER_TOKEN>"
```

### 7. Join batch

```bash
curl -X POST "BASE_URL/batches/join" \
  -H "Authorization: Bearer <STUDENT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d "{\"token\":\"<INVITE_TOKEN>\"}"
```

### 8. Create session

```bash
curl -X POST "BASE_URL/sessions" \
  -H "Authorization: Bearer <TRAINER_TOKEN>" \
  -H "Content-Type: application/json" \
  -d "{\"batch_id\":1,\"title\":\"Python Advanced Topics\",\"date\":\"2026-04-23\",\"start_time\":\"09:00:00\",\"end_time\":\"11:00:00\"}"
```

### 9. Mark attendance

```bash
curl -X POST "BASE_URL/attendance/mark" \
  -H "Authorization: Bearer <STUDENT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\":1,\"status\":\"present\"}"
```

### 10. Get session attendance

```bash
curl -X GET "BASE_URL/sessions/1/attendance" \
  -H "Authorization: Bearer <TRAINER_TOKEN>"
```

### 11. Get batch summary

```bash
curl -X GET "BASE_URL/batches/1/summary" \
  -H "Authorization: Bearer <INSTITUTION_TOKEN>"
```

### 12. Get institution summary

```bash
curl -X GET "BASE_URL/institutions/1/summary" \
  -H "Authorization: Bearer <PROGRAMME_MANAGER_TOKEN>"
```

### 13. Get programme summary

```bash
curl -X GET "BASE_URL/programme/summary" \
  -H "Authorization: Bearer <PROGRAMME_MANAGER_TOKEN>"
```

### 14. Get monitoring attendance

This endpoint requires the scoped monitoring token from `/auth/monitoring-token`, not the standard login token.

```bash
curl -X GET "BASE_URL/monitoring/attendance" \
  -H "Authorization: Bearer <SCOPED_MONITORING_TOKEN>"
```

## Schema Decisions

- `batch_trainers`:
  - This table is used for the many-to-many relationship between trainers and batches.
  - It also supports authorization checks so a trainer can create sessions and view attendance only for batches they are assigned to.

- `batch_invites`:
  - This table stores invite tokens for batch enrollment.
  - It includes the creator, expiry time, and used state so student joins can be controlled without directly exposing enrollment edits.

- Dual-token approach for Monitoring Officer:
  - Monitoring Officer first logs in like a normal user and gets a standard JWT.
  - Then they call `/auth/monitoring-token` with the API key to receive a short-lived scoped token.
  - `/monitoring/attendance` accepts only the scoped monitoring token, not the standard login token.
  - This adds an extra layer of control for the highest-visibility read-only endpoint.

- Institutions:
  - Institutions are modeled separately because users, batches, and region-based summary access depend on them.

## What Is Fully Working

- Core FastAPI REST API structure
- JWT login and signup flow
- Role-based access control on protected endpoints
- Monitoring Officer dual-token flow
- Batch creation, invite generation, and student join flow
- Session creation by assigned trainers
- Student attendance marking for active sessions
- Attendance and summary endpoints
- Seed script with required minimum data
- Pytest test file covering the required assignment scenarios plus a few additional authorization checks

## What Is Partially Done

- README deployment section is prepared, but the live base URL still needs to be added
- Local test execution depends on PostgreSQL being installed and configured correctly on the machine

## What I Skipped

- Public deployment configuration inside this repo
- Token revocation/logout flow
- Rate limiting on authentication endpoints
- Advanced production hardening beyond the scope of the assignment
