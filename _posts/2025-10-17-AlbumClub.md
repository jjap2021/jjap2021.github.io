---
layout: post
title: Creating a Progressive Web App (PWA)
---

A hobby of mine for a long time has been expanding the scope of my music library. I have enjoyed growing by listening to new artists and letting my playlists auto-play whatever recommended song Apple Music's algorithm puts in front of me. Thankfully, I went to high school with a bunch of like-minded people and we began organizing Album Club. 

The rules to album club are simple:
- Everyone's name is added to a wheel and we spin and remove each name it lands on to create a list. We go down the list in order and each week, whoever's turn it is selects an album.
- We have about a week to listen to it and formulate our thoughts as a short review and rating.
- Members of Album Club then organized a meeting time and either met in-person or virtually on Discord to discuss this week's album.
- Then, we would move to the next person and repeat it all.

After many renditions of Album Club, I have finally decided to create a web application to host it in a more organized manner. Thus, I began this project.

As you can imagine, I had to hash out what exactly would be in the application. Below are a series of decisions I made so far (with no particular prioritization):
1. General ruleset and thought process:
Create and run invite only “album club” leagues. Each season is one full round where every member gets exactly one pick in a pre-published order. For each week (or configurable window), the scheduled picker submits an album link, members listen, rate (1–10), and we output stats. Late ratings are allowed until the end of the season (can be toggled) and count toward the official averages (but are marked as late). Duplicate albums are blocked across all time within a league.
2. Roles and Access

# WORK IN PROGRESS - MORE TO COME
