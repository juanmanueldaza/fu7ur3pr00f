---
description: View and manage career profile, goals, and preferences
agent: build
model: opencode-go/qwen3.5-plus
skill: career-profile
---
View or edit the user's career profile. $ARGUMENTS

## Workflow

1. Parse arguments:
   - No args → view profile
   - `--edit` → interactive edit session
   - `--goals` → view/edit goals

2. View profile:
   ```python
   from fu7ur3pr00f.memory.profile import load_profile
   profile = load_profile()
   print(profile.summary())
   ```

3. Edit profile (interactive):
   - Ask user what fields to update
   - Use `edit_profile()` for atomic updates:
   ```python
   from fu7ur3pr00f.memory.profile import edit_profile

   def update(profile):
       profile.name = "..."
       profile.current_role = "..."
       profile.target_roles = ["...", "..."]

   edit_profile(update)
   ```

4. Manage goals:
   ```python
   from fu7ur3pr00f.memory.profile import CareerGoal, edit_profile

   def add_goal(profile):
       profile.goals.append(CareerGoal(
           description="Become Staff Engineer",
           target_date="2026-12-31",
           priority="high"
       ))

   edit_profile(add_goal)
   ```

5. Show current state after any changes.
