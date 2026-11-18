# KumariQuest — Testing Strategy

**Current baseline:** Django's test runner currently discovers zero tests. The strategy below is the target; it does not claim coverage already exists.

## 1. Test layers

| Layer | What to test | Suggested mechanism |
|---|---|---|
| Unit/domain | Planner filtering, preference validation, day assignment, model invariants | Django `TestCase` / focused pure functions |
| Integration | Views, templates, forms, ORM, migrations, sessions, media validation | Django test client and temporary test DB |
| API | Serializer contracts, pagination, statuses, error shapes, CSRF/session behavior | DRF `APITestCase` if DRF is approved; otherwise Django client for JSON views |
| Frontend | Accessible controls, responsive layouts, no-JS/basic enhancement fallback | Manual review plus browser automation for core journeys |
| End-to-end | Register/sign in, browse, generate trip, favorite, feedback, notification behavior | Playwright or equivalent only if selected and maintained |
| Security | Production settings, access boundaries, upload handling, CSRF, XSS, dependency posture | Django deployment checks, focused adversarial tests, dependency scanner |
| Operations | Migrations, health check, static/media configuration, backup restore | CI/staging smoke and scheduled restore drill |

## 2. Required tests by feature

### Destination discovery

- Public list is available without login; missing detail returns 404.
- Search/category combination matches only expected destinations; unknown category behavior is explicit.
- Empty data and missing optional image/coordinates render without error.
- User-provided or admin content is escaped; no unsafe markup is executed.
- If publication status exists, drafts are invisible to visitors and visible only to authorized staff.

### Accounts and profiles

- Successful/failed registration and sign-in; duplicate username/email policy; password validators.
- Logout invalidates the session and is not triggered by GET.
- Anonymous users are redirected or receive `401` consistently for protected routes.
- User A cannot read/update User B's profile or upload.
- Password change works with the documented session policy; responses never echo passwords.
- Reject invalid file type, spoofed MIME, oversized image, and malformed image; preserve existing image on failed update.
- Login/registration throttling and generic failure response do not reveal account existence.

### Planner/trips

- Each accepted combination yields requested day count and deterministic destination assignment.
- Cases: no destinations, one destination, fewer destinations than days, all filters, each budget boundary, each trip type, maximum days, invalid text/negative/zero/very large day count.
- Invalid request never creates a `TripPlan`.
- Anonymous planning behavior is tested; saved plans are owner-scoped.
- If stops are persisted, update/delete semantics and destination deletion/snapshot behavior are tested.

### Live location and navigation

- Location permission is requested only after the user activates navigation; the page must be served from a secure context (HTTPS in production).
- Mock browser Geolocation API outcomes: permission granted, denied, unavailable, timeout, stale/low-accuracy fix, and permission revoked while active.
- Verify the marker follows new fixes only while navigation is active and `clearWatch` is called when the user stops, navigates away, or the component/page is torn down.
- Verify destinations with missing/out-of-range coordinates show a useful unavailable state and do not call the route service.
- Test walking/driving mode validation, route geometry parsing (GeoJSON `[longitude, latitude]`), distance/duration display, empty route, malformed upstream response, timeout, and service outage.
- Verify route refresh follows initial defaults: immediate on start, then no more than once per 30 seconds and only after at least 50 m movement or more than 50 m route deviation; insignificant GPS jitter does not cause requests.
- Verify no precise origin is written to the database, Django session, cookies, local/session storage, URL, analytics, application logs, or error response. Test proxy/upstream logging configuration separately.
- Test rate limits, CSRF, coordinate bounds, and that map/routing failure does not break destination details or browsing.
- Keep map tiles under a compliant configured host in tests; use mocked responses rather than public OSM/OSRM endpoints in automated tests.

### Favorites, reviews, notifications

- Favorite uniqueness under duplicate and concurrent attempts; delete behavior is stable.
- Review ratings 1 and 5 accepted; 0, 6, decimals, missing and malformed values rejected.
- Blank/oversized review comments rejected; pending/unapproved reviews are not publicly visible.
- Notification list and mutation are scoped to owner; GET does not change `is_read`.
- Staff moderation endpoints reject non-staff accounts.

## 3. Authentication and authorization matrix

| Operation | Anonymous | Owner | Other authenticated user | Staff |
|---|---:|---:|---:|---:|
| Read published destination | Allow | Allow | Allow | Allow |
| Edit destination | Deny | Deny | Deny | Allow only with permission |
| Read own profile/plan/favorite/notification | Deny | Allow | Deny/404 | No implicit access |
| Update own profile or notification | Deny | Allow | Deny/404 | No implicit access |
| Moderate review/content | Deny | Deny | Deny | Allow only with permission |

Test direct URL/API calls, not only hidden frontend controls.

## 4. Validation, edge cases, and security testing

- Test malformed JSON, unknown fields, wrong types, boundary lengths, unexpected Unicode, null values, and invalid IDs.
- Verify Django ORM usage prevents injection; test hostile input as ordinary literal data.
- Verify template autoescaping and safe URL schemes; avoid testing only static strings.
- Verify CSRF enforcement for browser mutations and rejection of cross-origin unsafe requests.
- Test open-redirect attempts in `next`/return URLs.
- Check headers and cookie attributes in staging: HTTPS, HttpOnly, Secure, SameSite, CSP, frame policy, content sniffing protections.
- Test rate limiting on login, registration, and user submissions.
- Upload handling: file content sniffing, allowlist, maximum size and dimensions, random storage name, safe response content type, access control.
- Run dependency vulnerability checks against the app's actual locked dependencies and review alerts before release.
- Test that logs and errors omit passwords, cookies, tokens, full uploaded paths, and unnecessary personal data.

Security tests are preventive checks, not a substitute for a scoped professional penetration test when deployment risk requires one.

## 5. Measurable acceptance criteria

| Feature | Release acceptance |
|---|---|
| Destination browse/detail | All core list/detail scenarios pass; unknown destination returns 404; empty and optional-field states render successfully. |
| Authentication | Register/login/logout happy path and invalid cases pass; all account-owned routes reject anonymous access; no user can access another user's data. |
| Profile/upload | Valid profile updates persist; invalid/oversized/non-image uploads are rejected; existing profile remains intact on validation failure. |
| Itinerary | For every supported day count 1–5, output contains exactly that many day groups; each eligible destination appears at most once unless approved otherwise; invalid inputs create no saved plan. |
| Favorites | At most one favorite per user/destination under repeated requests; owner can list/remove; another user cannot inspect it. |
| Reviews | Only ratings 1–5 and bounded non-empty comments are accepted; public output follows moderation decision. |
| Notifications | Only owner sees/updates a notification; state change uses a non-GET method; unread counts match stored state. |
| Live navigation | GPS starts only on explicit action and HTTPS; permission/error states are understandable; marker updates while active and stops on exit; walking/driving route overview shows valid geometry/distance/ETA; refresh obeys the documented movement/deviation and 30-second thresholds; invalid coordinates/provider failure are handled; no exact location is persisted or logged. |
| Accessibility | Core workflows keyboard-operable and labels/errors announced; automated accessibility checks have no critical/serious violations, followed by manual review. |
| Performance | With an agreed representative dataset and environment, p95 server response <500 ms for core pages/API excluding external providers; record test conditions. |
| Release | `manage.py check`, migration checks, all automated tests, dependency review, `check --deploy`, staging smoke, backup restore all pass. |

## 6. CI and test data policy

- Run formatting/lint/type checks only after selecting and configuring tools; do not add tooling without need.
- CI sequence: dependency install → migration check → Django checks → unit/integration/API tests → production configuration check where secrets are safely mocked.
- Use factories/fixtures with synthetic data. Never copy production PII or secrets into tests.
- Include a fresh-database migration test and a migration upgrade test from the currently supported baseline.
- Keep browser E2E tests limited to critical workflows to avoid brittle duplication of unit/view coverage.
