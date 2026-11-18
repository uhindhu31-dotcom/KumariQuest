# KumariQuest — Security Review and Safeguards

**Scope:** Defensive design review of the current repository and proposed target. This is not a penetration test, exploit reproduction, or claim that all runtime paths have been independently audited. Findings are based on inspected settings, views, models, URLs, and templates.

## 1. Current high-priority risks

| Priority | Finding | Evidence / impact | Recommended action |
|---|---|---|---|
| Critical before deployment | Development `SECRET_KEY` is hard-coded; `DEBUG=True`; `ALLOWED_HOSTS=[]` | Current settings are development-only and must not be exposed as production configuration. A known or reused signing key can compromise sessions/tokens; debug pages can disclose sensitive internals. | Load a unique secret from a secret manager/environment; rotate any key that may have been used in a deployed environment; fail closed if absent; `DEBUG=False`; explicit host allowlist; run `manage.py check --deploy`. |
| High | State-changing notification action is linked with GET | `mark_notification_read` sets `is_read=True` on a GET route; crawlers/prefetchers can trigger mutations and CSRF semantics are wrong. | Change to POST/PATCH with CSRF and owner filtering; GET must be read-only. |
| High | Logout also changes state through GET | `logout_view` logs out on GET and is linked as a normal anchor, allowing cross-site navigation to sign a user out. | Use a CSRF-protected POST form for logout; keep GET read-only. |
| High | Input parsing is incomplete | Planner and feedback views convert request values with `int()`; malformed input can raise errors; planner does not enforce the form's day range server-side. | Use Django forms/serializers, strict choices/ranges, bounded payloads, consistent field errors; test malformed input. |
| High | Account mutation and login lifecycle need hardening | Registration/password/profile logic is hand-written; registration calls `create_user` without explicit `validate_password`; password change policy is custom; account endpoints rely on inline auth checks. | Use framework forms/auth helpers, invoke configured password validators, define password-change/session behavior, use safe redirects and generic auth errors, rate limits, explicit permission decorators/classes. |
| High | Profile image upload is not validated in application code | `ImageField` exists, but no explicit size/dimension/format policy is visible. | Validate actual decoded image, allowlist formats, limit size/dimensions, generate storage names, use object storage, serve with safe headers. |
| High | Destination name is inserted into a Leaflet HTML popup | The destination name is JavaScript-escaped, then concatenated into popup HTML; JavaScript escaping does not make HTML insertion safe if content contains markup. | Render popup content as text using a DOM text node or apply a proven HTML-escaping function at the HTML sink; add a stored-content regression test. |
| Medium/High | Test suite has no tests | Django test runner discovers zero tests; authorization and edge-case regressions are unguarded. | Add focused tests in the implementation checkpoints; block releases on critical flow/security tests. |
| High | New live navigation exposes transient precise location | Approved target will collect GPS while foreground navigation is active and send it for routing. Tile/routing hosts may process location/viewport data; logs could unintentionally retain exact coordinates. | Explicit start/stop and browser permission; disclose routing transfer; hold coordinates only in page memory; do not persist or log them; redact reverse-proxy and upstream logs; rate-limit requests; use approved tile/routing hosts and CSP. |
| Medium | Existing map/location scripts and providers are incomplete | Templates load third-party mapping assets/services. Current live-map script references missing page elements/variables. | Rebuild the navigation flow rather than expose the existing broken code; keep destination browsing usable on map/routing failure; document provider terms and attribution; test failure and permission states. |
| Medium | Dependency manifest appears broader than the application | `requirements.txt` contains many unrelated packages, increasing installation and supply-chain review burden. | Identify the app's actual runtime/test dependencies; lock supported versions; scan and update under review. |
| Medium | User-generated review content and public visibility | Review comments are rendered; rating range is only enforced in a view; no moderation/status policy or DB rating constraint exists. | Enforce DB and request constraints; escape text; agree moderation/rate-limit/report process; paginate. |
| Medium | Production media/static deployment and privacy settings are unspecified | Local media routes are added in root URL config; no production storage policy or security headers are documented. | Do not serve user media through development helper in production; use dedicated storage/CDN; configure HTTPS, cookies, CSP, framing and content-type protections. |

## 2. Threat areas and mitigations

### SQL injection

- Django ORM parameterizes normal query operations, reducing common injection risk.
- Do not construct raw SQL from search/category/ID inputs. If raw SQL becomes necessary, use bound parameters.
- Validate allowed sort/filter fields; never pass user-controlled ORM field names directly.
- Test suspicious strings as literal input and review every raw-query use before release.

### Cross-site scripting (XSS)

- Django templates autoescape by default; preserve autoescaping for destination descriptions, reviews, names, notification content, and usernames.
- Avoid `safe`, untrusted HTML, and unsafe DOM APIs such as assigning user content to `innerHTML`.
- If rich text is required, use a maintained allowlist sanitizer and restrict allowed tags/URLs.
- Apply a restrictive Content Security Policy; minimize third-party scripts and inline script exceptions.

### Cross-site request forgery (CSRF)

- Keep Django CSRF middleware enabled and include tokens in all unsafe HTML form and same-origin API requests.
- Replace GET mutation routes (notably notification read) with POST/PATCH/DELETE.
- Set secure `SameSite` session and CSRF cookies; use HTTPS and a correct trusted-origin list.
- Do not disable CSRF as a shortcut for JSON endpoints using browser session auth.

### Broken access control / IDOR

- For each profile, trip, favorite, and notification detail/update, filter querysets by `request.user`; do not fetch by object ID and trust the UI.
- Return 404 for objects outside the caller's scope where appropriate; avoid existence leaks.
- Add tests with two users for every private resource and mutation.
- Use Django permissions/groups for staff operations; admin accounts require strong operational protection.

### Authentication and sessions

- Use Django password hashers and configured validators; no plaintext or reversible password storage.
- Generic login/register errors; rate limits and monitoring for brute force/credential stuffing.
- Require POST + CSRF for logout; rotate session on login; review session expiry and invalidation on password change.
- Configure production cookies (`Secure`, `HttpOnly`, suitable `SameSite`), HTTPS redirect, HSTS only after HTTPS is confirmed, and safe `next` URL validation.
- Decide email verification, password reset, account deletion, and recovery requirements before launch.

### Sensitive data exposure and privacy

- Do not return password hashes, session identifiers, reset tokens, private email, internal file paths, or precise location by default.
- Start browser geolocation only after an explicit navigation action and permission, over HTTPS. Keep fixes in active page memory only; do not write them to a Django session, database, local/session storage, analytics, URL, or logs.
- A route request necessarily transfers origin coordinates to the configured OSRM service. Disclose the data flow, select a trusted/self-hosted routing host, configure retention/redaction, and bound/rate-limit requests. Map tile requests can disclose the approximate viewport to the tile host.
- Stop `watchPosition` when the user ends navigation or leaves the active page; do not implement background tracking in this browser scope.
- Remove debug mode and source-controlled development secrets from deployment settings; rotate exposed/reused secrets.
- Minimize collection and retention of location/profile data; define privacy notice, deletion, backup retention, and data subject process.
- Redact credentials, tokens, cookies, exact GPS coordinates, and unnecessary PII from application, proxy, and provider logs.

### Insecure file uploads

- Accept only required image formats after decoding content; do not trust extension or client MIME type.
- Limit bytes, dimensions, and processing time; generate storage keys; optionally re-encode images.
- Store uploads outside executable/public application paths; use a separate media host/bucket with safe content headers.
- Check malware/content scanning needs against threat model; prevent SVG/HTML execution unless sanitized and specifically required.
- Authorize upload/read/delete operations and define orphan cleanup.

### Improper input validation / abuse

- Server-side validation for username/email, trip choices, rating, comment length, search length, pagination, file content, and route coordinates/mode/destination.
- Use database constraints for invariant ranges and unique ownership pairs.
- Apply request/body limits and throttling to auth, reviews, registration, planner, and route-calculation endpoints; enforce upstream timeouts and response-size limits.
- Avoid detailed errors that reveal credentials, account existence, DB internals, or filesystem paths.

### Dependencies, deployment, and operations

- Lock only needed dependencies; scan vulnerabilities and review provenance/updates.
- Run with a dedicated low-privilege service account, least-privilege DB credentials, isolated staging/production secrets, and patched runtime.
- Add TLS, security headers, backups, tested restoration, health checks, centralized redacted logs, and incident contact/process.
- Restrict admin by staff authorization and operational access policy; consider MFA/SSO at the hosting/identity layer if risk warrants.

## 3. Release security gates

1. No known production secret in source; any previously deployed secret is rotated.
2. `DEBUG=False`, explicit hosts, `check --deploy` clean, HTTPS and secure cookies verified.
3. CSRF required for all browser state changes; no mutating GET endpoints.
4. Owner-only access tests pass for each private model.
5. Upload tests reject invalid/oversized content; media storage is production-safe.
6. XSS, validation, throttling, dependency review, and logging redaction tests/checks pass.
7. Geolocation starts only by user action; route and tile hosts, attribution, disclosure, retention, and coordinate log redaction are reviewed; tracking stops on exit; route failures do not block destination browsing.
8. Backups and restore procedure tested; incident and dependency patch ownership assigned.

Reassess this review after the API, upload policy, and deployment provider are selected.
