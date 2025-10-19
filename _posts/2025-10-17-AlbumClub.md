---
layout: post
title: Creating a Progressive Web App (PWA)
---

## Preface

A long-time hobby of mine has been expanding the scope of my music library. I’ve always enjoyed discovering new artists and letting my playlists wander—often by following whatever recommended song Apple Music’s algorithm throws my way.  

In high school, I was lucky enough to have a group of friends who shared that same curiosity for new music. Together, we started **Album Club**.  

The rules were simple:
- Everyone’s name was added to a wheel. We spun it until all names had been drawn, creating an order for the season.  
- Each week, the next person on the list chose an album for everyone to listen to.  
- We spent about a week listening, writing short reviews, and rating the album.  
- At the end of the week, we met—either in person or on Discord—to discuss our thoughts before moving on to the next picker.

After a few seasons and many discussions, I decided it was time to build a **web application** to host Album Club in a more organized, automated way. This project is the result of that effort.

As you can imagine, I had to hash out what exactly would be in the application. Below are a series of decisions I made so far (with no particular prioritization):

# 1. General ruleset and thought process:

Create and run invite only “album club” leagues. Each season is one full round where every member gets exactly one pick in a pre-published order. For each week (or configurable window), the scheduled picker submits an album link, members listen, rate (1–10), and we output stats. Late ratings are allowed until the end of the season (can be toggled) and count toward the official averages (but are marked as late). Duplicate albums are blocked across all time within a league.

# 2. Roles and Access

- **Manager (Organizer/Commissioner):** Full control over league configuration, calendar windows, picker order, editing weeks, reopening ratings, fixing typos, and overriding records when needed. Can manage invites and set an optional league password. Can designate Co-manager(s).
- **Co-producer:** Same as Producer for operational controls; Producer assigns/removes.
- **Member:** Can see schedule, submit ratings/comments, and view stats/history.
- **Access Model:** Members join via a unique league invite link (optionally protected by a league password).

# 3. Season and Picker Order

- **Season Definition:** One full pass through the picker order so that each active member picks exactly once.
- **Order Transparency:** The entire pick order is published at season start (dates included) so members can plan picks. A cosmetic wheel/spin is optional later; order is pre seeded and visible.
- **No Repeats Rule:** A member cannot be scheduled to pick again within the same season.
- **Skips:** If a picker fails to submit by their pick window deadline, they are skipped and the schedule compresses forward (no byes). Skips are logged.
- **Join Mid-season:** New members are appended to the back of the remaining order.
- **Leave Mid season:** The order is compressed, removing the member and pulling up subsequent pickers.
- **Season Boundaries:** App tracks season start and end timestamps; end occurs when the final scheduled picker’s window closes.

# 4. Windows, Deadlines, and Late Policy

- **Listening Window:** Configurable per league (e.g., 7 days by default; can be 10, 14, etc.). The same window length applies to every pick in the season unless changed by Producer.
- **Pick Deadline:** The picker must submit the album link by the window start (or a configurable cutoff) to keep cadence.
- **Ratings Deadline:** Ratings are due at the window end for that pick.
- **Late Ratings:** Allowed until the season ends and are clearly labeled Late. Late ratings do affect official averages and downstream stats.
- **Reminders:** In-app only. Show a prominent “24h left” banner + bell badge 24 hours before each rating window closes.

# 5. Album Submissions and Eligibility

- **Submission:** Picker submits a primary link from *Spotify, Apple Music, or YouTube*.
-	**Duplicate Prevention:** Block duplicates across all time within the league. Matching is done via provider IDs when available; otherwise normalized Artist + Album Title.

# 6. Ratings and Comments

- **Scale:** *1.0 to 10.0*, inclusive, with exactly one decimal place (0.1 steps). Integers like 7.0 are valid.
- **Identity:** Non anonymous. All ratings and comments show member identity.
- **Edits:** Members may edit their rating/comment until their pick’s rating window closes; after the deadline, edits are allowed only within the late window (and remain marked late upon any late change). After season end, ratings lock.
- **Picker Rating:** Picker can rate their own pick.
- **Comments:** Optional free text comment with basic formatting; no moderation tooling, length 500 characters.

# 7. Time and Timezone

- **Canonical Time:** All deadlines are stored in UTC.
- **Display Time:** The UI displays times in the viewer’s device local time.
- **Consistency:** To reduce confusion for multi timezone leagues, each page also shows a small UTC/offset badge and “X hours remaining.”

# 8. Deciding on Platform(s)

**Frontend:** Next.js (App Router) + Tailwind
**Backend/DB:** Supabase (Postgres, SQL, RLS, Edge Functions)
**Hosting:** Vercel (frontend) + Supabase (backend)
**Auth:** None initially (invite link + optional password stored on league)
**Exports:** SQL to CSV endpoints (or Supabase RPC)
**Future:** Add Spotify/Apple/YouTube metadata by provider ID; optional Discord/Calendar later


# WORK IN PROGRESS - MORE TO COME
