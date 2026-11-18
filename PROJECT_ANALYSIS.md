# KumariQuest — Project Analysis

**Status:** Planning baseline derived from the repository as it exists on 2026-11-17. This document distinguishes observed behavior from proposed work. It is not approval to begin implementation.

## 1. Purpose and problem statement

KumariQuest is a web application intended to help visitors discover places in Kanyakumari and organize a trip. It brings destination information, preference-based itineraries, account profiles, and travel information into one site. The current repository is a small Django monolith with server-rendered templates and SQLite for local development.

**Problem addressed:** travelers may need to consult disparate sources to learn about local destinations and plan a short visit. The product aims to make that discovery and basic itinerary-planning flow convenient in one place.

**Known limitation:** the repository does not establish a validated user problem, geographic/content data source, commercial model, or target traffic. These remain product decisions.

## 2. Users and roles

| Role | Intended capabilities | Current state |
|---|---|---|
| Visitor | Browse destinations, details, safety and about pages; use the planner | Most browse pages and planner are reachable without authentication |
| Registered traveler | Sign in, manage a profile, view saved trip preferences, see favorites, receive notifications, submit feedback | Account/profile, trip preference records, notifications, and reviews exist; favorite management and notification creation are not exposed as complete user flows |
| Content administrator | Manage destination content and review/manage records | Django admin is configured for several models; no documented operational or moderation workflow |

Use Django's existing user/group/permission system for the first release. No separate staff, guide, or business role is assumed. Admin access must be explicitly restricted to trusted staff.

## 3. Feature inventory

### Present in the repository (not necessarily production-ready)

- Django authentication views for login, registration, logout, and account editing.
- Destination listing, destination detail, and a client-side search/category filter.
- A form that creates a preference-based itinerary from available destinations.
- A `TripPlan` row for an authenticated user's selected days, category, trip type, and budget.
- Profile image field and profile page.
- Favorite, notification, review, and destination coordinate models.
- Notification list/read views; site-wide review submission/listing; map links/embedded map in the destination template.
- Django admin registrations for destinations, profiles, trip plans, notifications, and reviews.

### Partial, absent, or needing verification

- **Favorites:** model and profile display exist; no add/remove favorite route or UI was found.
- **Saved itineraries:** only planning preferences are stored; generated per-day destination assignments are not persisted.
- **Notifications:** a list/read UI exists; notification generation/delivery is not specified. Mark-as-read currently changes state through a GET link.
- **Logout:** the current logout view is reached through a GET link; state-changing actions should be POST with CSRF protection.
- **Reviews:** current schema and UI are site-wide, not destination-specific; moderation and abuse handling are not defined.
- **Live location/routing:** this is an approved planned launch feature, but current implementation is incomplete: the destination template's JavaScript expects map/status elements and coordinate variables not present in the rendered page; its Leaflet popup also combines a destination name with HTML after JavaScript escaping, which is not HTML sanitization. External Google Maps links/iframe are present. Rebuild and test the user-initiated foreground flow; do not present current routing as working.
- **Destination content:** no seed/import workflow or content provenance is documented.
- **Testing:** `manage.py test` currently discovers zero tests.
- **Production readiness:** settings contain a development secret in source, enable debug, and have no allowed hosts; SQLite is configured; media is served from the app URL configuration in development.
- **API:** there is no JSON API contract or REST framework implementation in the current repository.

## 4. Functional requirements (proposed, measurable)

| ID | Requirement | Acceptance evidence |
|---|---|---|
| FR-01 | Visitors can browse, search, filter, and open published Kanyakumari destinations. | List/detail tests cover empty, matching, non-matching, and invalid IDs. |
| FR-02 | Destination details show descriptive information, category, location, visiting hours, best time, entry fee, and optional coordinates/image. | Detail response renders every populated field and handles missing optional media/coordinates. |
| FR-03 | A visitor can generate an itinerary for 1–5 days with category, trip type, and budget preferences. | Valid inputs produce no more than one day-group per requested day; invalid inputs do not raise a server error or create a record. |
| FR-04 | A signed-in traveler can save and retrieve a trip. | A trip is associated only with its owner; another user cannot read or alter it. The product must decide whether to save itinerary stops or preferences only. |
| FR-05 | A traveler can manage their account/profile and optional profile image. | Authenticated owner-only access; input and uploads are validated; password changes preserve a valid session or require reauthentication. |
| FR-06 | A traveler can add/remove a destination favorite and see their favorites. | One favorite per user/destination; duplicate create is idempotent or returns documented conflict; user isolation is tested. |
| FR-07 | A traveler can submit feedback/reviews and view published reviews. | Rating is 1–5, comment is non-empty and bounded; publication/moderation policy is applied. |
| FR-08 | A traveler can list notifications and mark one as read. | Only the owner may read or update the notification; mutation uses POST/PATCH, not GET. |
| FR-09 | Administrators can maintain destination content and moderate user-generated content. | Staff-only actions are tested; audit expectations and moderation policy are documented. |
| FR-10 | A user can start an in-app walking/driving navigation overview to a selected destination, view their live position and route, and stop tracking. | Request location only after an explicit start action over HTTPS; handle permission denial/timeout; update the marker from accepted fixes while active; show route, distance, and estimated duration; initially recalculate no more than once per 30 seconds and only after movement of at least 50 m or more than 50 m off-route; stop watching when navigation ends; do not store exact coordinates in the database. Treat the thresholds as starting values to verify in field testing. |

FR-04 through FR-10 describe the proposed complete product flow, not fully implemented functionality.

## 5. Non-functional requirements (provisional targets)

These are recommended initial targets for review, not measured current performance:

- **Security:** deploy only with `DEBUG=False`, a secret provided outside source control, HTTPS, secure session/CSRF cookies, validated uploads, and least-privilege staff access.
- **Performance:** for a modest initial catalog (up to 10,000 destinations), p95 server-rendered page/API response under 500 ms excluding external map providers; paginate growing lists.
- **Availability:** target 99.5% monthly availability after production launch, excluding announced maintenance.
- **Accessibility:** responsive layouts; keyboard-accessible controls; meaningful labels/alt text; target WCAG 2.2 AA for core journeys.
- **Reliability:** database migrations are repeatable and backed up; errors are observable without logging credentials or unnecessary personal data.
- **Maintainability:** focused Django apps, explicit dependencies, documented local setup, and automated tests for critical flows.
- **Privacy:** collect only account data needed for the service; do not collect precise location unless a user explicitly starts a location feature and understands browser/provider disclosure.

## 6. Main workflows and business rules

1. Visitor opens the site, browses destinations, optionally filters locally, and opens a detail page.
2. Traveler optionally creates an account, signs in, and edits profile details.
3. Traveler chooses itinerary duration (currently 1–5), interest/category, trip type, and budget. The planner filters destinations and assigns destinations to days. A signed-in user currently gets a record of the selected preferences.
4. Traveler may view their profile and stored trip preferences.
5. From a destination with valid coordinates, traveler explicitly starts navigation, grants browser location permission, sees a live position marker and route overview, and can stop tracking. No background tracking is supported.
6. Traveler may view their profile and stored trip preferences.
7. In the proposed complete flow, traveler favorites destinations, posts feedback, and marks owned notifications read.

Proposed rules:

- A favorite is unique for each `(user, destination)` pair.
- A trip belongs to exactly one user. Whether anonymous plans can be retained is undecided; do not persist anonymous plans by default.
- Day count must be an integer in the supported range, initially 1–5 (matching the current form).
- Categories, trip types, and budget values must be constrained to documented choices; avoid silently accepting arbitrary values.
- A review rating must be an integer from 1 through 5. Decide whether reviews are site-wide or tied to a destination before changing the schema.
- Users can only access or mutate their own profile, plans, favorites, and notifications. Staff permissions are separate.
- Only published/approved destinations and reviews should be visible publicly if a publication/moderation state is adopted.
- Navigation location exists only in active browser memory; it is not written to the database, browser storage, or application logs. A route request necessarily sends coordinates to the configured routing service; disclose this and select the provider/hosting arrangement before release.
- Route overview supports walking and driving only. It displays position/route/distance/ETA, not voice guidance or guaranteed turn-by-turn directions. Stop browser location watching on stop, page teardown, or loss of permission.
- Initial route-refresh policy: calculate on start; afterward, require at least 30 seconds since the last calculation and either 50 m movement from the last route origin or more than 50 m route deviation. Tune from field tests while preserving rate limits and battery use.

## 7. Technical challenges and risks

- Current forms parse some numeric inputs directly and do not consistently validate range/choice values.
- Planner ordering and day slicing need edge-case tests (zero destinations, fewer destinations than days, unusual values).
- Media uploads require content validation, size limits, safe storage, and a production object-storage decision.
- Destination coordinates, browser geolocation, OpenStreetMap tiles, and OSRM introduce availability, privacy, licensing/attribution, data-refresh, and browser-permission considerations. Free/open-source software does not imply unlimited free tile hosting or production routing capacity.
- SQLite is suitable for local development but PostgreSQL is recommended for a production multi-user service.
- The pinned `requirements.txt` is a large mixed package inventory rather than a minimal, reproducible application dependency set.
- The repository has no written deployment, backup, monitoring, data-retention, or moderation process.

## 8. Assumptions and unresolved decisions

| Topic | Working assumption for this blueprint | Decision needed before the affected feature is built |
|---|---|---|
| Product scope | Existing KumariQuest repository is the baseline; no new domain is being introduced. | Confirm target launch scope and which partial features are required. |
| Geography | Kanyakumari destinations only for initial release. | Confirm whether coverage should expand to the district/region. |
| Reviews | Preserve current site-wide feedback semantics initially. | Site-wide feedback or a review attached to each destination? Who can view and moderate it? |
| Trips | Preserve current 1–5 day preference-driven planner. | Save only preferences or the generated ordered stops? Can guests save/share trips? |
| Accounts | Username/password and Django session authentication. | Email verification, password reset, social sign-in, and account deletion requirements? |
| Favorites | Private to the owning account. | Confirm desired UI and whether favorites need sharing. |
| Notifications | In-app notifications only for initial scope. | Who creates them and what events should trigger them? Email/push is not assumed. |
| Maps/location | **User-approved launch requirement:** foreground browser GPS only while a user-initiated navigation page is active; walking/driving route overview; no voice instructions; precise coordinates remain in browser memory and are not written to the database. Proposed stack: Leaflet + OpenStreetMap data/tiles + OSRM-based routing. | Choose a compliant tile source and whether OSRM is self-hosted or provided by an approved host; confirm terms, privacy disclosure, operating cost, and availability target. |
| Deployment | One Django application, managed PostgreSQL and media storage, HTTPS. | Hosting provider, region, expected traffic, budget, retention, recovery objectives. |
| License | No license is inferred from repository state. | Select a project license and verify rights to media, copy, and destination data. |

## 9. Scope boundaries

Not included without explicit approval: bookings/payments, hotel inventory, route optimization guarantees, real-time transit, emergency dispatch, background GPS tracking, turn-by-turn/voice navigation, native mobile apps, AI recommendations, multilingual translation, public social sharing, and third-party account login.

## 10. Review gate

The user approved adding foreground live-map navigation to the launch blueprint, with walking/driving, transient in-browser coordinates, and route overview (no turn-by-turn/voice). Before implementation, select the tile/routing hosting arrangement and settle trip persistence, review scope/moderation, authentication lifecycle, and deployment details.
