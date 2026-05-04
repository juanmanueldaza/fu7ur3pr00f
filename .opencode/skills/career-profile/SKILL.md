---
name: career-profile
description: "View and manage career profile, goals, and preferences."
compatibility: opencode
when_to_use: "When the user wants to view or edit their career profile."
model: low
user-invocable: false
hub-skill-ids:
  - career-intelligence
  - configuration
allowed-tools:
  - Bash
  - Read
  - Edit
---

# Skill: Career Profile

Manage the user's career profile stored at `~/.fu7ur3pr00f/profile.yaml`.

## View Profile

```python
from fu7ur3pr00f.memory.profile import load_profile
profile = load_profile()
print(profile.summary())
```

## Edit Profile

```python
from fu7ur3pr00f.memory.profile import edit_profile

def update(profile):
    profile.name = "Jane Doe"
    profile.current_role = "Senior ML Engineer"
    profile.target_roles = ["Staff ML Engineer", "ML Engineering Manager"]
    profile.technical_skills = ["Python", "PyTorch", "Kubernetes", ...]
    profile.deal_breakers = ["no relocation", "remote only"]

edit_profile(update)
```

## Profile Fields

| Field | Description |
|-------|-------------|
| `name` | Full name |
| `email` | Contact email |
| `location` | City/Country |
| `github_username` | GitHub handle |
| `current_role` | Current job title |
| `years_experience` | Total years |
| `technical_skills` | List of tech skills |
| `soft_skills` | List of soft skills |
| `target_roles` | Desired roles |
| `target_companies` | Dream companies |
| `deal_breakers` | Non-negotiables |
| `salary_expectations` | Compensation range |
| `preferred_work_style` | remote/hybrid/onsite |
| `goals` | CareerGoal entries with timeline |

## Goals

```python
from fu7ur3pr00f.memory.profile import CareerGoal, edit_profile

def add_goal(profile):
    profile.goals.append(CareerGoal(
        description="Become a Staff Engineer",
        target_date="2027-12-31",
        priority="high"
    ))

edit_profile(add_goal)
```
