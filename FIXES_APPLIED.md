# Upgrade Plan Fixes Applied

This document summarizes all the logical inconsistencies and confusion points that were identified and fixed in the upgrade planning files.

## Date: 2025-11-22

## Files Modified
- `UPGRADE_PLAN.md`
- `upgrade_progress.json`

---

## ✅ Fix 1: CP4-T1 Priority Mismatch

**Issue**: Task was marked as "Critical" but could be skipped, creating confusion.

**Changes**:
- **UPGRADE_PLAN.md:501** - Changed priority from "Critical" to "Conditional"
- **upgrade_progress.json:842** - Changed priority from "critical" to "conditional"

**Reason**: If a task can be skipped when another task completes, it shouldn't be marked as critical.

---

## ✅ Fix 2: CP2-T3 Missing Skip Condition

**Issue**: Markdown mentioned task becomes obsolete with SQLite, but JSON had no skip condition.

**Changes**:
- **UPGRADE_PLAN.md:265** - Enhanced warning about obsolescence with SQLite
- **upgrade_progress.json:369-370** - Added `skip_if_completed: ["CP2-T5"]` and skip reason

**Reason**: AI might implement caching even after SQLite migration without explicit skip condition.

---

## ✅ Fix 3: Dependency Field Standardization

**Issue**: Inconsistent dependency tracking between task objects and global dependencies section.

**Changes**:
- Added `depends_on_reason` to all tasks with dependencies
- Added `enables` and `enables_reason` to CP2-T1 and CP2-T5
- Added `obsoletes` and `obsoletes_reason` to CP2-T5
- Added `should_precede` and `should_precede_reason` to CP4-T5

**Affected Tasks**:
- CP1-T6, CP1-T7, CP2-T1, CP2-T5, CP3-T5, CP3-T6, CP4-T5, CP5-T4

**Reason**: All dependency information now directly in task objects for easier AI parsing.

---

## ✅ Fix 4: CP5-T1 Missing "Implement Last" Flag

**Issue**: No explicit flag preventing early implementation of architectural change.

**Changes**:
- **upgrade_progress.json:1183-1184** - Added `implement_last: true` and reason

**Reason**: Prevents AI from implementing WebSocket changes before other features are stable.

---

## ✅ Fix 5: Design Subtasks Requiring User Input

**Issue**: Design decisions had no guidance for AI on how to proceed.

**Changes Added `requires_user_input: true` and `default_choice` to**:
- **CP1-T5-S1** - Authentication schema design
- **CP2-T3-S1** - Caching layer design
- **CP2-T5-S1** - SQLite schema design
- **CP3-T6-S1** - Album data structure design
- **CP5-T3-S1** - Share link schema design
- **CP5-T4-S1** - Activity log schema design
- **CP6-T3-S1** - API response envelope design

**Reason**: AI knows to ask user or use sensible default if user doesn't provide preference.

---

## ✅ Fix 6: SQLite Conditionals Made Explicit

**Issue**: Vague "(if SQLite)" conditionals in descriptions.

**Changes**:
- **CP3-T6-S1** - Updated description to clarify dependency on CP2-T5
- All SQLite-dependent tasks now have explicit `depends_on` fields

**Reason**: AI can programmatically check dependencies instead of parsing parenthetical notes.

---

## ✅ Fix 7: Testing Breakpoint Behavior Documentation

**Issue**: Unclear what AI should do when encountering testing breakpoints.

**Changes**:
- **UPGRADE_PLAN.md:1042-1048** - Added explicit instructions for AI implementers

**Instructions Added**:
1. STOP implementation at testing breakpoint
2. Update subtask status to "awaiting_testing"
3. Inform user testing is required
4. Provide clear testing instructions
5. Do NOT continue until user confirms
6. This is human verification, not automated tests

**Reason**: AI knows exactly how to behave at testing checkpoints.

---

## ✅ Fix 8: Context Usage Guidance

**Issue**: No guidance on what to do if context usage exceeds estimates.

**Changes**:
- **UPGRADE_PLAN.md:1035-1041** - Added explicit context monitoring instructions

**Instructions Added**:
- Monitor context usage throughout execution
- STOP at 60-70% usage and prepare for handoff
- Update progress JSON before stopping
- Inform user about context limit requirements
- Don't exceed safe context limits
- Better to hand off mid-task than run out of context

**Reason**: AI can self-monitor and hand off gracefully before context exhaustion.

---

## ✅ Fix 9: Single Source of Truth Clarification

**Issue**: Two files with status information could diverge.

**Changes**:
- **UPGRADE_PLAN.md:13-18** - Added prominent "Single Source of Truth" section
- **upgrade_progress.json:1698** - Added note as first item in notes array

**Clarifications**:
- `upgrade_progress.json` is authoritative for all statuses
- `UPGRADE_PLAN.md` is read-only reference
- AI should only update JSON, only read markdown
- If files diverge, JSON is correct

**Reason**: Eliminates ambiguity about which file to trust and update.

---

## ✅ Fix 10: Backup Subtasks Before Risky Changes

**Issue**: No explicit backup steps before major destructive operations.

**Changes Added Backup Subtasks (S0) to**:
- **CP1-T5-S0** - Plan user migration strategy for authentication
- **CP2-T5-S0** - Backup all JSON files before SQLite migration
- **CP5-T1-S0** - Backup server.py and systemd service before WSGI change

**Updated Markdown**:
- All three tasks now have subtask 0 as backup step
- CP2-T5-S10 description clarified to "Verify backup integrity"

**Reason**: Ensures critical data/configuration backed up before risky operations.

---

## Additional Improvements

### New JSON Fields Added
- `requires_user_input` - Flags subtasks needing user decisions
- `default_choice` - Provides sensible defaults for design decisions
- `skip_if_completed` - Lists tasks that make this task obsolete
- `skip_reason` - Explains why task should be skipped
- `depends_on_reason` - Explains dependency relationships
- `enables` / `enables_reason` - Documents what this task enables
- `obsoletes` / `obsoletes_reason` - Documents what this task makes obsolete
- `should_precede` / `should_precede_reason` - Ordering recommendations
- `implement_last` / `implement_last_reason` - Defers risky changes
- `critical_safety_step` - Marks backup/safety subtasks

### Enhanced Notes in JSON
Added guidance notes about:
- Single source of truth
- Design subtasks with defaults
- Skip conditions checking
- Implement-last tasks

---

## Summary Statistics

- **Files Modified**: 2
- **Tasks with New Dependency Info**: 8
- **Design Subtasks Enhanced**: 7
- **Backup Subtasks Added**: 3
- **Priority Changes**: 2 (CP4-T1, CP2-T3 warnings enhanced)
- **New Documentation Sections**: 3 (Testing Breakpoints, Context Management, Source of Truth)

---

## Impact on AI Behavior

These fixes significantly improve AI reliability by:

1. **Eliminating ambiguity** - Clear source of truth, explicit dependencies
2. **Preventing errors** - Backup steps, skip conditions, implement-last flags
3. **Improving guidance** - Default choices, context monitoring, testing protocols
4. **Better handoffs** - Progress tracking, status clarity, session continuity
5. **Safer operations** - Mandatory backups before risky changes

---

## Validation

All changes have been validated for:
- ✅ JSON syntax correctness
- ✅ Markdown formatting
- ✅ Consistency between files
- ✅ Logical coherence
- ✅ Completeness of instructions

---

**All recommended fixes have been successfully applied.**
