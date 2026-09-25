# SCIO Clone — Implementation Plan

## 1. Summary

SCIO is a digital signage management system: customers upload content, build playlists/layouts, schedule playback, pair physical screens, and monitor screen status from a central dashboard.

The goal of the first build isn't feature parity with the original — it's getting **one single flow working reliably**:

> Create account → pair a screen → upload content → build a playlist → schedule it → confirm the screen plays the right content even when offline.

Everything else (third-party integrations, analytics, interactive kiosks, mobile app...) comes later, once that flow is solid.

## 2. Priorities: what to build first

The order isn't based on difficulty — it's based on "if this is missing, the demo means nothing":

1. **Player + offline content sync** — this is the core of signage. A beautiful dashboard means nothing if the screen doesn't play reliably. This goes first, not last.
2. **Screen pairing + online/offline status tracking** — without this, there's nothing real to demo.
3. **Asset + Playlist + Schedule** — the "content management" part users interact with most, but it only matters once (1) and (2) work.
4. **Organization/permissions (roles, inviting members)** — needed to make it look like a real product, but not the hard part; build it in parallel during the foundation stage.

Things to cut first if time runs short: detailed audit logs, a wide variety of layout templates, operational metrics dashboards — keep these minimal, don't invest deeply.

## 3. Scope

### In the first build

- Login, create organization, basic roles (owner/admin/editor/viewer)
- Upload image/video/PDF/web URL, organize with folders + tags
- Build playlists, multi-zone canvas, live preview in the browser
- Schedule by day/time/recurrence, clear conflict handling
- Pair players via pairing code, show online/offline via heartbeat
- Player caches content locally, keeps playing offline, auto-resyncs when back online

### Not in this build

- Third-party integrations (YouTube, Slides, Power BI...)
- Native mobile app, interactive kiosks, AI camera/sensors
- Video wall, advanced proof-of-play, billing/reporting, SSO/SCIM
- Full visual editor — a limited canvas + prebuilt templates is enough
- Designing UI from scratch — since this is a clone, the layout/UI follows the original, no need to spend time on original design work

Why cut these: none of them affect proving the product actually works — they only widen scope, while the biggest risk is whether playback is stable.

## 4. Staffing

| Role | Count | Main work |
|---|---|---|
| Full-stack engineer | 2 | Dashboard, API, playlist/schedule, org/permissions |
| Backend/device engineer | 1 | Core data model, player protocol, manifest, offline sync, heartbeat |
| QA/platform engineer | 1 | Test playback, tenant isolation, CI/CD, error monitoring |

No dedicated designer role — UI follows the original, engineers build directly from the reference instead of designing from scratch.

Note: with only 1–2 people, combine roles in this order: one person owns player + offline sync first, the other owns dashboard/CRUD; QA happens last as a manual checklist rather than full automation.

## 5. Timeline (10 weeks, team of 4)

| Phase | Duration | Outcome |
|---|---:|---|
| Foundation: auth, org, core data model, CI/CD | 1 week | Login, org creation, basic roles, core schema deployed |
| Asset library | 1.5 weeks | Upload, preview, tag, delete assets |
| Player pairing + heartbeat | 1.5 weeks | Pairing works, dashboard shows online/offline status |
| Playlist + canvas | 2 weeks | Build playlists, multi-zone layout, preview |
| Schedule + publish | 2 weeks | Scheduling, publishing, player receives correct content |
| Offline cache + recovery | 1 week | Keeps playing offline, auto-recovers when back online |
| Polish, testing, pilot | 1 week | Test the main flow, fix bugs, ready for demo/pilot |

The most important milestone to hit before anything else: **by the end of week 6, the player must keep playing when the network is pulled, with no crash or blank screen.** That's the condition for moving into the polish phase.

## 6. Risks to watch

- **Unstable network**: this isn't an edge case — it's normal operating conditions for signage hardware. Handle it late and you'll have to rework the player architecture. Do it early.
- **Scheduling edge cases** (timezones, overlapping schedules): easy to overlook; needs clear priority rules from the start rather than being patched in later.
- **Data leakage between organizations**: every query must be scoped by organization, enforced at the API layer, not just the UI.
- **Scope creep**: the biggest risk isn't technical — it's expanding breadth before the core is solid.

## 7. After the first build

Once the demo/pilot is stable, the next directions (in priority order):

1. Support player platforms beyond browser/desktop
2. Integrate popular content sources (YouTube, Slides, cloud storage)
3. Finer-grained permissions per folder, approval workflows
4. Proof-of-play reporting, operational analytics
5. Mobile app for emergency management

## References

- [OptiSigns features](https://www.optisigns.com/features)
- [Digital signage remote management](https://www.optisigns.com/product/digital-signage-remote-management)
- [Set up and add a screen](https://support.optisigns.com/hc/en-us/articles/360016374813-Set-up-add-a-screen)
- [Why a screen is shown as offline](https://support.optisigns.com/hc/en-us/articles/360016484473-Why-Does-My-Screen-Show-as-Offline-on-the-Web-Portal)
- [Folder-level permissions](https://support.optisigns.com/hc/en-us/articles/360044600474-Folder-Level-Permissions)
- [Control and schedule playlist items](https://support.optisigns.com/hc/en-us/articles/20062273670163-How-to-Control-and-Schedule-Playlist-Items)
