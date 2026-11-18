# KumariQuest — API Documentation

**Status: Proposed contract only.** The current repository serves Django HTML pages and does not implement these JSON endpoints or Django REST Framework. These examples are a review artifact; implementation requires approval of the product decisions and API scope.

## 1. Conventions

- Base URL: `/api/v1/`
- Content type: `application/json; charset=utf-8`
- Same-origin browser authentication: Django session cookie; unsafe methods require a valid CSRF token (for example `X-CSRFToken`).
- JSON API authentication failures: `401`; authenticated but forbidden: `403`; missing/inaccessible resource: `404`.
- JSON validation errors: `400`; duplicate conflict where not idempotent: `409`; rate limit: `429`.
- Pagination: `?page=1&page_size=20`; server maximum page size 100.
- Public destination endpoints require no login. Account-owned endpoints require authentication and always scope queries to the current user.
- Timestamps are ISO 8601 UTC strings. IDs are integer identifiers in examples; clients should treat them as opaque.
- Do not expose password hashes, session identifiers, private emails, internal storage paths, or staff-only fields.

Suggested error shape:

```json
{
  "error": {
    "code": "validation_error",
    "message": "One or more fields are invalid.",
    "fields": {
      "days": ["Must be an integer between 1 and 5."]
    }
  }
}
```

## 2. Endpoint summary

| Method | Endpoint | Purpose | Auth |
|---|---|---|---|
| GET | `/api/v1/destinations` | Search/filter published destinations | No |
| GET | `/api/v1/destinations/{id}` | Destination details | No |
| POST | `/api/v1/auth/register` | Create account | No + CSRF for cookie-based browser |
| POST | `/api/v1/auth/login` | Start session | No + CSRF |
| POST | `/api/v1/auth/logout` | End session | Yes + CSRF |
| GET | `/api/v1/me` | Current account/profile | Yes |
| PATCH | `/api/v1/me` | Update profile fields | Yes + CSRF |
| POST | `/api/v1/plans` | Generate and, per approved policy, save a plan | Yes + CSRF |
| GET | `/api/v1/me/plans` | List own saved plans | Yes |
| GET | `/api/v1/me/favorites` | List own favorites | Yes |
| POST | `/api/v1/me/favorites` | Add a favorite | Yes + CSRF |
| DELETE | `/api/v1/me/favorites/{destination_id}` | Remove a favorite | Yes + CSRF |
| GET | `/api/v1/reviews` | List published feedback/reviews | No |
| POST | `/api/v1/reviews` | Submit feedback/review | Yes + CSRF |
| GET | `/api/v1/me/notifications` | List own notifications | Yes |
| PATCH | `/api/v1/me/notifications/{id}` | Mark own notification read | Yes + CSRF |
| POST | `/api/v1/navigation/routes` | Calculate transient walking/driving route overview | No login; CSRF and rate limit |

The exact set is subject to product approval. In particular, trip persistence and site-wide versus destination-specific reviews affect request and response schemas.

## 3. Endpoint specifications

### 3.1 List destinations

`GET /api/v1/destinations?search=beach&category=Beach&page=1&page_size=20`

**Request:** optional query parameters `search` (trimmed, maximum 100 characters), `category` (known published category), `page` (positive integer), `page_size` (1–100).

**200 response:**

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 42,
      "name": "Example Beach",
      "category": "Beach",
      "description": "A public destination description.",
      "location": "Kanyakumari",
      "latitude": 8.08,
      "longitude": 77.55,
      "visiting_hours": "See local information",
      "best_time": "Seasonal",
      "entry_fee": "Free",
      "budget_level": "Budget",
      "image_url": null
    }
  ]
}
```

**Statuses:** `200`, `400` invalid query values. Search matching, ordering, and publication semantics must be fixed in implementation.

### 3.2 Retrieve destination

`GET /api/v1/destinations/{id}`

**Request:** positive destination ID.

**200 response:** one destination object as above.

**Statuses:** `200`, `404` if absent or unpublished.

### 3.3 Register

`POST /api/v1/auth/register`

**Request:**

```json
{
  "username": "traveler42",
  "email": "traveler@example.com",
  "password": "use-a-unique-secret"
}
```

Validate normalized username uniqueness, email syntax, configured Django password validators, and request size. Email verification is not assumed.

**201 response:** `{"id": 18, "username": "traveler42"}`. Do not return credentials or a password hash.

**Statuses:** `201`, `400` field errors, `409` duplicate username (or a deliberately generic duplicate response), `429` rate limit.

### 3.4 Login and logout

`POST /api/v1/auth/login` accepts `{"username":"traveler42","password":"..."}`. On success, create a Django session and return `{"user":{"id":18,"username":"traveler42"}}`; set session cookie using secure production attributes.

`POST /api/v1/auth/logout` accepts an empty JSON object and invalidates the current session; return `204`.

**Statuses:** login `200`, `400` malformed request, `401` generic invalid credentials, `429` rate limit; logout `204`, `401`, or `403` for missing CSRF as configured. Avoid revealing whether a username exists.

### 3.5 Current account and profile update

`GET /api/v1/me` returns the authenticated user's safe public profile:

```json
{
  "id": 18,
  "username": "traveler42",
  "email": "traveler@example.com",
  "profile_image_url": null,
  "date_joined": "2026-11-17T05:00:00Z"
}
```

`PATCH /api/v1/me` accepts only explicitly allowed fields, for example `{"username":"new-name","email":"new@example.com"}`. Image upload should use a separately documented multipart endpoint if approved. Do not include password changes in this endpoint without a dedicated reauthentication policy.

**Statuses:** `200`, `400`, `401`, `409` duplicate username.

### 3.6 Generate/save a plan

`POST /api/v1/plans`

**Request:**

```json
{
  "days": 2,
  "category": "All",
  "trip_type": "Family",
  "budget": "Moderate"
}
```

`days` must be integer 1–5; category must be `All` or a supported category; `trip_type` must be one of `Family`, `Couple`, `Solo`, `Friends`; `budget` must be `Budget`, `Moderate`, or `Luxury`. Any change requires API and UI updates together.

**201 response (proposed persisted-trip form):**

```json
{
  "id": 73,
  "preferences": {
    "days": 2,
    "category": "All",
    "trip_type": "Family",
    "budget": "Moderate"
  },
  "itinerary": [
    {"day": 1, "destinations": [{"id": 42, "name": "Example Beach"}]},
    {"day": 2, "destinations": [{"id": 58, "name": "Example Heritage Site"}]}
  ],
  "created_at": "2026-11-17T05:00:00Z"
}
```

The response omits fields for unavailable destinations and may contain empty day lists; policy must be approved. If the project decides not to persist plans, use `200` and do not claim a saved plan ID.

**Statuses:** `201` persisted / `200` transient per approved policy, `400` invalid fields, `401`, `429`.

`GET /api/v1/me/plans` returns only the caller's saved plans, newest first, paginated. `GET /api/v1/me/plans/{id}` or DELETE can be added only if product scope requires detail/deletion; ownership is mandatory.

### 3.7 Favorites

`GET /api/v1/me/favorites` returns paginated destination summaries belonging to the caller.

`POST /api/v1/me/favorites` request: `{"destination_id":42}`. Return `201 {"destination_id":42,"created_at":"..."}`; repeated requests may return `200` with existing state (recommended idempotent behavior) or `409`, but must be documented and race-safe.

`DELETE /api/v1/me/favorites/{destination_id}` removes the caller's favorite and returns `204`; return `404` if absent (or consistently idempotent `204`, by decision).

**Statuses:** `200/201/204`, `400`, `401`, `404`, `409` if non-idempotent policy, `429`.

### 3.8 Reviews / feedback

`GET /api/v1/reviews?page=1` returns only reviews approved for public display:

```json
{
  "count": 1,
  "results": [
    {
      "id": 9,
      "username": "traveler42",
      "rating": 5,
      "comment": "The trip planner was useful.",
      "created_at": "2026-11-17T05:00:00Z"
    }
  ]
}
```

`POST /api/v1/reviews` request for the current site-wide schema:

```json
{"rating":5,"comment":"The trip planner was useful."}
```

Require authentication; rating integer 1–5; trimmed non-empty comment with a documented maximum (recommend 2,000 characters); apply rate limits and moderation policy. If destination-specific, add a validated `destination_id` only after a schema decision.

**Statuses:** `201` (or `202` if queued for moderation), `400`, `401`, `429`.

### 3.9 Notifications

`GET /api/v1/me/notifications?page=1` lists only caller-owned notifications newest first.

`PATCH /api/v1/me/notifications/{id}` request: `{"is_read":true}`. Return `200 {"id":12,"is_read":true}`.

**Statuses:** `200`, `400`, `401`, `404` for another user's or absent notification. Reading is a mutation; GET must never mark as read.

### 3.10 Calculate a navigation route

`POST /api/v1/navigation/routes`

This endpoint is proposed for the approved foreground-only navigation feature. It calculates a route to a known destination and does not create a trip, save the origin, or update user history. The browser requests GPS permission only after the user starts navigation. Coordinates are kept in page memory, sent in this request body, and must be redacted from application/proxy logs. The endpoint processes the origin transiently through the configured OSRM service.

**Request:**

```json
{
  "destination_id": 42,
  "origin": {
    "latitude": 8.0821,
    "longitude": 77.5412
  },
  "travel_mode": "walking"
}
```

`destination_id` must reference a destination with valid coordinates. `origin.latitude` must be between −90 and 90; `origin.longitude` between −180 and 180. `travel_mode` must be `walking` or `driving`. Apply request-size and rate limits. Require CSRF for same-origin browser use even though the endpoint does not require login.

**200 response:**

```json
{
  "destination_id": 42,
  "travel_mode": "walking",
  "distance_meters": 2300,
  "duration_seconds": 1800,
  "geometry": {
    "type": "LineString",
    "coordinates": [
      [77.5412, 8.0821],
      [77.5450, 8.0800],
      [77.5500, 8.0780]
    ]
  }
}
```

GeoJSON coordinate order is `[longitude, latitude]`. The UI shows route line, distance, and estimated duration only; turn-by-turn and voice guidance are not part of this first version. Initial client refresh policy: calculate on start, then recalculate only after at least 30 seconds and either at least 50 m movement from the last route origin or more than 50 m route deviation. These are starting values to validate in field testing; server throttling remains authoritative.

**Statuses:** `200`, `400` invalid coordinates/mode, `404` unknown destination, `422` no route found, `429` rate limit, `503` routing service unavailable, `403` CSRF failure. Never include the raw origin in error or access logs.

## 4. Common validation and operational requirements

- Enforce schemas on the server even when the browser validates.
- Use ORM parameterization; never interpolate request values into SQL.
- Cap request body, list page size, query-string length, and upload size.
- Use pagination for user-generated collections.
- Add throttling to authentication and user-submission endpoints.
- Rate-limit route calculations; validate all coordinates and travel modes; enforce upstream timeouts and response-size limits; redact exact origin coordinates in app, proxy, and routing logs.
- Return provider failures as a clear non-sensitive `503` or route-unavailable response; browsing and destination details must remain usable without routing.
- Avoid public exposure of usernames/email where privacy policy says not to; the example review username is illustrative and requires a display-name policy.
- Keep error messages stable enough for clients, but do not expose stack traces, SQL, file paths, or account-existence details.
- Add API contract tests for every status and ownership boundary before exposing endpoints.
