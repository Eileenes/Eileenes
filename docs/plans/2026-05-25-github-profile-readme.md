# GitHub Profile README Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a bilingual GitHub profile README for `duke-yeah` that introduces the user as an independent developer and highlights the most relevant public projects.

**Architecture:** Build a single `README.md` inside a local `duke-yeah` profile repository scaffold. Use lightweight Markdown + HTML sections so the page renders cleanly on GitHub without external build steps.

**Tech Stack:** GitHub Profile README, Markdown, inline HTML, shields.io badges

### Task 1: Gather current public profile context

**Files:**
- Reference: GitHub public repo metadata fetched from `https://api.github.com/users/duke-yeah/repos?per_page=100`

**Step 1: Inspect public repositories**

Identify the current flagship repos by recency, language, and apparent product direction.

**Step 2: Select the README narrative**

Position the user as an independent developer building AI and iOS productivity products.

### Task 2: Create the profile repository scaffold

**Files:**
- Create: `duke-yeah/README.md`
- Create: `duke-yeah/docs/plans/2026-05-25-github-profile-readme.md`

**Step 1: Create the local repo directory**

Run: `mkdir -p /Users/huayang.sun/duke-yeah/docs/plans`

Expected: directory exists for the profile scaffold and plan doc.

**Step 2: Write the README**

Create a bilingual profile README with:
- headline and positioning
- concise intro in Chinese and English
- current focus areas
- featured projects
- tech stack badges
- contact section

### Task 3: Review and refine the rendered structure

**Files:**
- Modify: `duke-yeah/README.md`

**Step 1: Inspect the Markdown locally**

Check that section order is readable and bilingual content is compact.

**Step 2: Remove weak or unverifiable claims**

Prefer accurate project framing over inflated marketing language.

**Step 3: Final verification**

Run a file preview command such as `sed -n '1,220p' /Users/huayang.sun/duke-yeah/README.md`

Expected: a complete README ready to copy into the GitHub profile repository.
