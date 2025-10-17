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

# WORK IN PROGRESS - MORE TO COME
