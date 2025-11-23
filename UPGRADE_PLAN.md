# FrameSync Comprehensive Upgrade Plan

This document outlines the complete upgrade plan for FrameSync, organized into 6 major checkpoints with detailed tasks and subtasks.

---

## ⚠️ IMPLEMENTATION PHASES

This upgrade plan is organized into **implementation phases** based on priority and complexity:

### **Phase 1: Critical Security & Foundation (REQUIRED)**
- CP1-T1: Fix command injection (CRITICAL)
- CP1-T3: File content validation (HIGH)
- CP2-T5: SQLite migration (foundational change)
- CP1-T2: Fix hardcoded paths (if e-paper is being used)

### **Phase 2: Performance & Usability (RECOMMENDED)**
- CP2-T1: Thumbnails
- CP2-T2: Pagination
- CP3-T1: Upload progress bar
- CP3-T3: Remember device selection
- CP4-T2: Improve error handling
- CP4-T3: Storage quotas

### **Phase 3: Nice-to-Haves (OPTIONAL)**
- CP3-T2: Bulk operations
- CP3-T4: Search/filtering
- CP5-T2: Per-device slideshow settings
- CP4-T4: Configuration system
- CP1-T4: Rate limiting

### **Phase 4: Complex & Entirely Optional (SKIP FOR FAMILY USE)**
⚠️ **These features are designed for enterprise/multi-tenant use cases and add significant complexity:**
- CP1-T5: Full authentication system (overkill for family/Tailscale-only use)
- CP1-T6: API keys for devices (only needed with authentication)
- CP1-T7: CSRF protection (only needed with authentication)
- CP5-T1: WebSockets (complex architectural change, polling is acceptable for family use)
- CP5-T3: Public share links
- CP5-T4: Activity/audit logs
- CP5-T5: Progressive Web App (PWA)
- CP5-T6: Image captions
- CP5-T7: Admin dashboard
- CP3-T6: Albums/collections (complex, can defer)
- CP6-T1: OpenAPI/Swagger docs
- CP6-T2: API versioning
- CP6-T3: Standardized API responses

**Recommendation:** Focus on Phases 1-2, selectively implement Phase 3 based on actual needs, and skip Phase 4 unless you have specific enterprise requirements.

---

## Progress Tracking

All progress is tracked in `upgrade_progress.json`. This allows:
- **Session Continuity**: New Claude sessions can resume from where previous sessions left off
- **Detailed Status**: Track completion at the subtask level
- **Testing Checkpoints**: Built-in breakpoints for human verification
- **Context Management**: Each task sized to stay within Claude's context limits

**⚠️ IMPORTANT - Single Source of Truth**:
- `upgrade_progress.json` is the **authoritative source** for all task statuses
- `UPGRADE_PLAN.md` is a **read-only reference** for task descriptions and details
- If the two files ever diverge on status, `upgrade_progress.json` is correct
- AI implementers should **only update** `upgrade_progress.json` for status changes
- AI implementers should **only read** `UPGRADE_PLAN.md` for task guidance

**Valid Status Values**:
- `not_started` - Task has not been started yet
- `in_progress` - Task is currently being worked on
- `completed` - Task has been fully completed and verified
- `awaiting_testing` - Implementation is complete, waiting for user to test with real hardware/usage
- `skipped` - Task was skipped because its prerequisite made it obsolete (e.g., CP2-T5 completed before CP2-T3)

## How to Use This Plan

**⚠️ IMPORTANT FOR IMPLEMENTERS**: This plan has been **organized into 4 implementation phases**. For a family photo frame system with Tailscale access:

1. **Implement Phase 1** (REQUIRED) - Critical security fixes and foundational changes
2. **Implement Phase 2** (RECOMMENDED) - Performance and usability improvements
3. **Selectively implement Phase 3** (OPTIONAL) - Based on actual user needs
4. **SKIP Phase 4** (COMPLEX & OPTIONAL) - Enterprise features that add significant complexity with minimal benefit for family use

When implementing:
1. **Start at the current checkpoint** indicated in `upgrade_progress.json`
2. **Check the task's `phase` field** - skip Phase 4 tasks unless user explicitly requests them
3. **Complete tasks sequentially** within each phase
4. **Test at breakpoints** - subtasks marked with `testing_breakpoint: true` require human testing
5. **Update progress** - Update `upgrade_progress.json` after each subtask
6. **Review dependencies** - Some tasks depend on others (documented in the JSON file)

## Quick Start for New Sessions

If you're a new Claude session picking up this work:

```
1. Read upgrade_progress.json to see current progress
2. Find current_checkpoint and current_task
3. Resume from the next incomplete subtask
4. Update status as you complete work
5. Stop at testing breakpoints for user verification
```

---

# Checkpoint Overview

## CP1: Security Improvements (Critical Priority)
**Status**: Not Started
**Estimated Total Context**: 135%
**Tasks**: 7

Critical security fixes including command injection vulnerability, authentication, rate limiting, and input validation.

## CP2: Performance Improvements
**Status**: Not Started
**Estimated Total Context**: 125%
**Tasks**: 5

Major performance enhancements including thumbnails, pagination, caching, lazy loading, and SQLite migration.

## CP3: User Experience Improvements
**Status**: Not Started
**Estimated Total Context**: 180%
**Tasks**: 8

UX enhancements including upload progress, bulk operations, search/filter, image editing, albums, EXIF metadata.

## CP4: Reliability & Maintainability
**Status**: Not Started
**Estimated Total Context**: 170%
**Tasks**: 7

Reliability improvements including file locking, error handling, storage quotas, configuration system, code organization, tests.

## CP5: New Features
**Status**: Not Started
**Estimated Total Context**: 180%
**Tasks**: 7

New functionality including WebSockets, slideshow settings, share links, activity logs, PWA support, captions, admin dashboard.

## CP6: Documentation & API Improvements
**Status**: Not Started
**Estimated Total Context**: 90%
**Tasks**: 4

API improvements and documentation including OpenAPI/Swagger, versioning, standardized responses, updated docs.

---

# Detailed Task Breakdown

## CP1: Security Improvements (Critical)

### CP1-T1: Fix Command Injection Vulnerability ⚠️ CRITICAL
**Priority**: Critical
**Estimated Context**: 15%
**Requires Testing**: Yes

**Current Issue**: `os.system()` calls in `server.py:416` and `rotate_image.py:209` are vulnerable to command injection.

**Subtasks**:
1. Replace `os.system()` with `subprocess.run()` in server.py:416
2. Replace `os.system()` with `subprocess.run()` in rotate_image.py:209
3. Add proper error handling for subprocess calls
4. **[TESTING BREAKPOINT]** Test e-paper display functionality with new implementation

**Testing**: Verify that e-paper display still updates correctly with real hardware.

---

### CP1-T2: Fix Hardcoded Path in display_image.py
**Priority**: High
**Estimated Context**: 10%
**Requires Testing**: Yes

**Current Issue**: Path `/home/r2/e-Paper/` is hardcoded for wrong user.

**Subtasks**:
1. Update `/home/r2/e-Paper/` path to use current user or config
2. Make e-Paper library path configurable via environment variable
3. **[TESTING BREAKPOINT]** Test display_image.py with corrected paths

**Testing**: Verify e-paper integration works with corrected paths.

---

### CP1-T3: Implement File Content Validation
**Priority**: High
**Estimated Context**: 15%
**Requires Testing**: Yes

**Current Issue**: Only filename extension is validated, not actual file content.

**Subtasks**:
1. Use Pillow's Image.verify() for file validation (no new dependency needed)
2. Validate file headers/magic bytes in upload endpoint
3. Add proper error messages for invalid file types
4. **[TESTING BREAKPOINT]** Test uploading various file types (valid and invalid)

**Testing**: Try uploading .exe renamed to .jpg, actual images, etc.

**Note**: Originally planned to use python-magic or imghdr, but:
- `imghdr` is deprecated in Python 3.11+ and removed in 3.13
- `python-magic` requires system library `libmagic` (may not be on Raspberry Pi)
- **Pillow** (already a dependency) has built-in image verification via `Image.verify()`

---

### CP1-T4: Add Rate Limiting
**Priority**: High
**Estimated Context**: 20%
**Requires Testing**: Yes

**Current Issue**: No protection against abuse or DoS.

**Subtasks**:
1. Add Flask-Limiter to requirements.txt
2. Configure rate limits for upload endpoint (10/minute per IP)
3. Configure rate limits for API endpoints (60/minute per IP)
4. Add rate limit headers to responses
5. **[TESTING BREAKPOINT]** Test rate limiting with rapid requests

**Testing**: Send rapid requests to verify rate limiting kicks in.

---

### CP1-T5: Add Authentication System (Basic)
**Priority**: High
**Estimated Context**: 30%
**Requires Testing**: Yes

**Current Issue**: Completely open access to all functionality.

**Subtasks**:
0. **⚠️ PLAN USER MIGRATION**: Document current open-access setup and plan migration strategy for existing users/devices
1. Design authentication schema (session-based vs token-based)
2. Add Flask-Login to requirements.txt
3. Create users table/file for storing credentials
4. Add login/logout endpoints
5. Create login UI page
6. Protect upload and delete endpoints with @login_required
7. Add user registration functionality
8. **[TESTING BREAKPOINT]** Test login, logout, and protected endpoints

**Testing**: Verify protected endpoints reject unauthenticated requests.

**Note**: This is a major change affecting all users. Consider migration strategy.

---

### CP1-T6: Add API Keys for Device Access
**Priority**: Medium
**Estimated Context**: 25%
**Requires Testing**: Yes

**Current Issue**: Device endpoints are completely open.

**Subtasks**:
1. Add api_key field to device registration
2. Generate secure random API keys for devices
3. Add API key validation middleware for device endpoints
4. Update multi-device documentation with API key usage
5. **[TESTING BREAKPOINT]** Test device registration and image fetching with API keys

**Testing**: Verify devices can register and fetch images with API keys.

**Dependencies**: Should be done after CP1-T5 (authentication).

---

### CP1-T7: Add CSRF Protection
**Priority**: Medium
**Estimated Context**: 20%
**Requires Testing**: Yes

**Current Issue**: No CSRF protection on state-changing operations.

**Subtasks**:
1. Add Flask-WTF to requirements.txt
2. Configure CSRF protection in Flask app
3. Add CSRF tokens to frontend forms and AJAX requests
4. Exempt device API endpoints from CSRF (use API keys instead)
5. **[TESTING BREAKPOINT]** Test all POST/DELETE operations with CSRF protection

**Testing**: Verify all forms and AJAX calls work with CSRF tokens.

**Dependencies**: Should be done after CP1-T6 (so device endpoints can be exempted).

---

## CP2: Performance Improvements

### CP2-T1: Generate Image Thumbnails
**Priority**: High
**Estimated Context**: 25%
**Requires Testing**: Yes

**Current Issue**: Gallery loads full-size images, wasting bandwidth and slowing rendering.

**Subtasks**:
1. Create thumbnails directory structure (uploads/thumbnails/)
2. Add thumbnail generation function using Pillow (200x200px)
3. Generate thumbnails on upload
4. Add /api/thumbnails/<filename> endpoint
5. Update frontend to load thumbnails in gallery
6. Generate thumbnails for existing images (migration script)
7. **[TESTING BREAKPOINT]** Test thumbnail generation and gallery loading performance

**Testing**: Upload images and verify thumbnails are generated. Check gallery loads faster.

**Impact**: Significant performance improvement for gallery view.

---

### CP2-T2: Add Pagination to Image Gallery
**Priority**: High
**Estimated Context**: 25%
**Requires Testing**: Yes

**Current Issue**: All images loaded at once, slow with many images.

**Subtasks**:
1. Add pagination parameters to /api/images endpoint (page, limit)
2. Implement backend pagination logic
3. Return pagination metadata (total, pages, current_page)
4. Add pagination UI controls to frontend
5. Implement page navigation (prev/next, page numbers)
6. **[TESTING BREAKPOINT]** Test pagination with various image counts

**Testing**: Test with 0 images, 1 page, multiple pages.

---

### CP2-T3: Implement Metadata Caching
**Priority**: Medium (⚠️ SKIP if CP2-T5 is completed first)
**Estimated Context**: 20%
**Requires Testing**: Yes
**⚠️ RECOMMENDATION**: Complete CP2-T5 (SQLite migration) first to skip this task entirely and save effort

**Current Issue**: JSON files read from disk on every request.

**Subtasks**:
1. Design caching layer (in-memory with TTL)
2. Add cache for metadata.json (5-minute TTL)
3. Add cache for devices.json (5-minute TTL)
4. Implement cache invalidation on writes
5. Add cache statistics endpoint for monitoring
6. **[TESTING BREAKPOINT]** Test cache hit/miss rates and invalidation

**Testing**: Monitor logs to verify cache is working.

**⚠️ IMPORTANT**: This task becomes obsolete if CP2-T5 (SQLite migration) is completed first, as SQLite has its own built-in caching mechanisms. **Skip this task if CP2-T5 is already done.**

---

### CP2-T4: Add Lazy Loading to Gallery
**Priority**: Medium
**Estimated Context**: 20%
**Requires Testing**: Yes

**Current Issue**: All images loaded immediately on page load.

**Subtasks**:
1. Implement Intersection Observer for lazy loading
2. Add loading='lazy' attribute to img tags
3. Add loading placeholder/skeleton screens
4. **[TESTING BREAKPOINT]** Test lazy loading with large image galleries

**Testing**: Verify images load as you scroll down.

**Note**: Works best with CP2-T1 (thumbnails) and CP2-T2 (pagination).

---

### CP2-T5: Migrate to SQLite Database ⭐ MAJOR CHANGE
**Priority**: High
**Estimated Context**: 35%
**Requires Testing**: Yes

**Current Issue**: JSON files don't scale, have race conditions, no ACID compliance.

**Subtasks**:
0. **⚠️ BACKUP**: Create complete backup of all JSON files (metadata.json, devices.json, state.json) before SQLite migration
1. Design SQLite schema (users, images, devices, permissions)
2. Create database initialization script
3. Create migration script to convert JSON to SQLite
4. Add SQLite helper functions (CRUD operations)
5. Replace metadata.json operations with SQLite queries
6. Replace devices.json operations with SQLite queries
7. Replace state.json operations with SQLite queries
8. Add database connection pooling
9. **[TESTING BREAKPOINT]** Test all operations with SQLite backend
10. **[TESTING BREAKPOINT]** Verify backup integrity and switch to SQLite in production

**Testing**:
- Test in development first with migrated data
- Verify all operations work (upload, delete, device registration, etc.)
- Backup JSON files before production switch

**Impact**:
- Makes CP4-T1 (file locking) obsolete
- Makes CP3-T6 (albums) easier to implement
- Improves performance and reliability significantly

**Warning**: This is a major architectural change. Test thoroughly before deploying.

---

## CP3: User Experience Improvements

### CP3-T1: Add Upload Progress Bar
**Priority**: High
**Estimated Context**: 20%
**Requires Testing**: Yes

**Current Issue**: No feedback during large file uploads.

**Subtasks**:
1. Replace fetch() with XMLHttpRequest in upload function
2. Add progress event listener to track upload percentage
3. Create progress bar UI component
4. Update progress bar during upload
5. **[TESTING BREAKPOINT]** Test with various file sizes (small and large)

**Testing**: Upload large files (5MB+) and verify progress bar updates smoothly.

---

### CP3-T2: Add Bulk Operations
**Priority**: High
**Estimated Context**: 30%
**Requires Testing**: Yes

**Current Issue**: Managing multiple images is tedious (must delete/edit one at a time).

**Subtasks**:
1. Add checkboxes to image gallery items
2. Add 'Select All' / 'Deselect All' controls
3. Create bulk actions toolbar (delete, change devices)
4. Add /api/images/bulk-delete endpoint
5. Add /api/images/bulk-update-devices endpoint
6. Implement bulk delete functionality
7. Implement bulk device assignment functionality
8. **[TESTING BREAKPOINT]** Test bulk operations with multiple selections

**Testing**: Select multiple images and perform bulk operations.

---

### CP3-T3: Remember Device Selection
**Priority**: Medium
**Estimated Context**: 15%
**Requires Testing**: Yes

**Current Issue**: Must select devices every time you upload.

**Subtasks**:
1. Save device selection to localStorage on upload
2. Load saved selection on page load
3. Pre-select remembered devices in upload modal
4. Add option to clear saved preferences
5. **[TESTING BREAKPOINT]** Test device selection persistence across sessions

**Testing**: Upload image, close browser, reopen - verify device selection is remembered.

---

### CP3-T4: Add Search and Filtering
**Priority**: Medium
**Estimated Context**: 25%
**Requires Testing**: Yes

**Current Issue**: Hard to find specific images in large collections.

**Subtasks**:
1. Add search input to UI toolbar
2. Implement filename search on backend
3. Add date range filter UI
4. Implement date range filtering on backend
5. Add device filter (show images for specific device)
6. Implement real-time search filtering on frontend
7. **[TESTING BREAKPOINT]** Test search and filtering combinations

**Testing**: Test filename search, date ranges, device filters, and combinations.

---

### CP3-T5: Add Image Rotation/Editing
**Priority**: Medium
**Estimated Context**: 25%
**Requires Testing**: Yes

**Current Issue**: Can't fix sideways photos.

**Subtasks**:
1. Add rotation buttons to image detail modal
2. Add /api/images/<filename>/rotate endpoint (90, 180, 270)
3. Implement server-side image rotation using Pillow
4. Update thumbnail after rotation
5. Add UI feedback during rotation
6. **[TESTING BREAKPOINT]** Test rotation with various image formats and sizes

**Testing**: Rotate images in all directions, verify thumbnails update.

**Dependencies**: Requires CP2-T1 (thumbnails) for thumbnail updates.

---

### CP3-T6: Add Album/Collection Support
**Priority**: Low
**Estimated Context**: 30%
**Requires Testing**: Yes

**Current Issue**: All images in flat list, no organization.

**Subtasks**:
1. Design album data structure (if SQLite, add albums table)
2. Add album CRUD endpoints
3. Create album management UI
4. Add album selection to upload modal
5. Add album filter to gallery view
6. Support moving images between albums
7. **[TESTING BREAKPOINT]** Test album creation, assignment, and filtering

**Testing**: Create albums, assign images, filter by album.

**Dependencies**: Much easier with CP2-T5 (SQLite) completed first.

---

### CP3-T7: Show EXIF Metadata
**Priority**: Low
**Estimated Context**: 20%
**Requires Testing**: Yes

**Current Issue**: Photo metadata (date taken, camera, etc.) not shown.

**Subtasks**:
1. Use Pillow's built-in Image.getexif() method for EXIF extraction (no new dependency needed)
2. Store EXIF data (date taken, camera, GPS) in metadata
3. Display EXIF data in image detail modal
4. Add option to sort by date taken (vs upload date)
5. **[TESTING BREAKPOINT]** Test EXIF extraction with various image sources

**Testing**: Upload photos from different cameras/phones, verify EXIF data extracted.

**Note**: Originally planned to use piexif, but:
- `piexif` is unmaintained (last update 2018)
- **Pillow** (already a dependency) has built-in EXIF support via `Image.getexif()`

---

### CP3-T8: Improve Mobile Device Management
**Priority**: Low
**Estimated Context**: 15%
**Requires Testing**: Yes

**Current Issue**: Long UUIDs hard to read on mobile.

**Subtasks**:
1. Shorten UUID display on mobile (show first 8 chars + '...')
2. Add tap-to-reveal for full UUID
3. Improve device list layout for narrow screens
4. **[TESTING BREAKPOINT]** Test on various mobile screen sizes

**Testing**: View device list on phone, tablet, desktop.

---

## CP4: Reliability & Maintainability

### CP4-T1: Implement File Locking for JSON Operations
**Priority**: Low (⚠️ SKIP if CP2-T5 is completed first)
**Estimated Context**: 20%
**Requires Testing**: Yes

**Current Issue**: Concurrent writes can corrupt JSON files.

**Subtasks**:
1. Add fcntl-based file locking for metadata.json reads/writes
2. Add fcntl-based file locking for devices.json reads/writes
3. Add fcntl-based file locking for state.json reads/writes
4. Add timeout and error handling for lock acquisition
5. **[TESTING BREAKPOINT]** Test concurrent writes with file locking

**Testing**: Simulate concurrent uploads from multiple clients.

**⚠️ IMPORTANT**: This task becomes obsolete if CP2-T5 (SQLite migration) is completed first, as SQLite handles locking internally. **Skip this task if CP2-T5 is already done.**

---

### CP4-T2: Improve Error Handling
**Priority**: High
**Estimated Context**: 25%
**Requires Testing**: Yes

**Current Issue**: Bare `except:` clauses hide errors.

**Subtasks**:
1. Replace bare except: with specific exceptions in load_metadata()
2. Replace bare except: with specific exceptions in load_devices()
3. Add proper exception handling to all file operations
4. Add logging for all caught exceptions
5. Create standardized error response format
6. Add frontend error display for API errors
7. **[TESTING BREAKPOINT]** Test error handling with various failure scenarios

**Testing**: Simulate disk full, permission errors, corrupted JSON, etc.

---

### CP4-T3: Add Storage Quotas
**Priority**: High
**Estimated Context**: 25%
**Requires Testing**: Yes

**Current Issue**: No limit on uploads, can fill SD card.

**Subtasks**:
1. Add storage quota configuration (default 5GB)
2. Create function to calculate current storage usage
3. Check quota before accepting uploads
4. Add storage usage display to UI
5. Add warning when approaching quota (90%)
6. Add /api/storage endpoint for usage statistics
7. **[TESTING BREAKPOINT]** Test quota enforcement with large uploads

**Testing**: Set low quota, upload until limit, verify rejection.

**Important**: Monitor SD card space on Raspberry Pi.

---

### CP4-T4: Add Configuration File System
**Priority**: Medium
**Estimated Context**: 20%
**Requires Testing**: Yes

**Current Issue**: All settings hardcoded in source.

**Subtasks**:
1. Create config.py with default values
2. Add support for .env file (using python-dotenv)
3. Move hardcoded values to config (port, max file size, etc.)
4. Add environment variable overrides
5. Create config.example.env template
6. Update documentation with configuration options
7. **[TESTING BREAKPOINT]** Test with various configuration values

**Testing**: Change config values and verify they're respected.

---

### CP4-T5: Split Frontend into Separate Files
**Priority**: Medium
**Estimated Context**: 30%
**Requires Testing**: Yes

**Current Issue**: 1,584 lines in single HTML file is hard to maintain.

**Subtasks**:
1. Create static/css/style.css and extract CSS
2. Create static/js/api.js for API calls
3. Create static/js/components.js for reusable UI components
4. Create static/js/app.js for main application logic
5. Update index.html to reference external files
6. Add static file serving endpoints if needed
7. **[TESTING BREAKPOINT]** Test that UI works identically after split

**Testing**: Verify all functionality works exactly as before.

**Recommendation**: Do this before adding major new frontend features to avoid merge issues.

---

### CP4-T6: Add Unit Tests
**Priority**: Medium
**Estimated Context**: 35%
**Requires Testing**: Yes

**Current Issue**: No test coverage.

**Subtasks**:
1. Add pytest and pytest-flask to requirements.txt
2. Create tests/ directory structure
3. Write tests for metadata operations
4. Write tests for device registration and management
5. Write tests for upload endpoint
6. Write tests for image filtering logic
7. Write tests for authentication (if implemented)
8. Add test coverage reporting
9. **[TESTING BREAKPOINT]** Run full test suite and achieve >80% coverage

**Testing**: Run pytest and verify all tests pass.

**Benefit**: Prevents regressions during future changes.

---

### CP4-T7: Add Health Check Endpoint
**Priority**: Low
**Estimated Context**: 15%
**Requires Testing**: Yes

**Current Issue**: No way to monitor server health.

**Subtasks**:
1. Create /health endpoint
2. Add system checks (disk space, DB connection, etc.)
3. Return JSON with status and component health
4. Add uptime and version information
5. **[TESTING BREAKPOINT]** Test health endpoint in various states

**Testing**: Call /health endpoint, verify response format and accuracy.

**Use Case**: Monitoring tools can poll this endpoint.

---

## CP5: New Features

### CP5-T1: Replace Polling with WebSocket Updates ⚠️ ARCHITECTURAL CHANGE
**Priority**: Medium
**Estimated Context**: 30%
**Requires Testing**: Yes
**⚠️ IMPLEMENTATION ORDER**: This task should be implemented **AFTER** all other CP5 tasks but **BEFORE** starting CP6 tasks

**Current Issue**: 30-second polling wastes bandwidth.

**Subtasks**:
0. **⚠️ BACKUP**: Create backup of current server.py and systemd service file before switching to eventlet WSGI server
1. Add Flask-SocketIO, python-socketio, and eventlet to requirements.txt
2. Initialize SocketIO in Flask app
3. Update server.py to use eventlet WSGI server instead of Flask's development server
4. Update systemd service file to use eventlet-based server
5. Add WebSocket events (image_uploaded, image_deleted, device_added)
6. Emit events from backend on state changes
7. Add Socket.IO client library to frontend
8. Replace polling with WebSocket listeners
9. Add connection status indicator
10. **[TESTING BREAKPOINT]** Test real-time updates with multiple clients

**Testing**: Open multiple browser windows, verify changes appear in real-time.

**Benefit**: Instant updates, reduced network traffic.

**⚠️ IMPORTANT**: This task requires switching from Flask's development server to **eventlet WSGI server**. This is a significant architectural change:
- Cannot use Flask's built-in server anymore
- Must update systemd service configuration
- Affects server startup and deployment
- **Recommendation**: Implement this task **LAST** after all other features are stable
- eventlet is chosen for simplicity and ARM64/Raspberry Pi compatibility

---

### CP5-T2: Add Per-Device Slideshow Settings
**Priority**: Medium
**Estimated Context**: 25%
**Requires Testing**: Yes

**Current Issue**: All devices use hourly rotation, not configurable.

**Subtasks**:
1. Add rotation_interval field to device schema
2. Add device settings UI (interval, shuffle, etc.)
3. Add /api/devices/<id>/settings endpoint
4. Update systemd timer to use per-device intervals
5. Add shuffle mode option for random image selection
6. **[TESTING BREAKPOINT]** Test various interval and shuffle configurations

**Testing**: Set different intervals for different devices, verify they rotate correctly.

---

### CP5-T3: Add Public Share Links
**Priority**: Low
**Estimated Context**: 25%
**Requires Testing**: Yes

**Current Issue**: Can't share images outside the system.

**Subtasks**:
1. Design share link schema (token, expiration, permissions)
2. Add share link generation endpoint
3. Add public share view (no auth required)
4. Add share button to image detail modal
5. Implement link expiration logic
6. Add copy-to-clipboard for share links
7. **[TESTING BREAKPOINT]** Test share link creation, access, and expiration

**Testing**: Create share link, access in incognito window, verify expiration works.

---

### CP5-T4: Add Activity/Audit Log
**Priority**: Low
**Estimated Context**: 25%
**Requires Testing**: Yes

**Current Issue**: No record of who did what.

**Subtasks**:
1. Create activity log schema (user, action, timestamp, details)
2. Add logging for uploads, deletes, device changes
3. Add /api/activity endpoint with pagination
4. Create activity log UI page
5. Add filtering by user, action type, date range
6. Add log retention policy (e.g., 90 days)
7. **[TESTING BREAKPOINT]** Test activity logging and viewing

**Testing**: Perform various actions, verify they appear in activity log.

**Dependencies**: Requires CP1-T5 (authentication) for user tracking.

---

### CP5-T5: Create Progressive Web App (PWA)
**Priority**: Low
**Estimated Context**: 25%
**Requires Testing**: Yes

**Current Issue**: Not installable on mobile devices.

**Subtasks**:
1. Create manifest.json with app metadata
2. Add app icons (various sizes)
3. Create service worker for offline support
4. Implement cache-first strategy for images
5. Add install prompt UI
6. **[TESTING BREAKPOINT]** Test installation on iOS and Android

**Testing**: Install on phone, verify works offline (for cached images).

---

### CP5-T6: Add Image Captions
**Priority**: Low
**Estimated Context**: 20%
**Requires Testing**: Yes

**Current Issue**: Can't add descriptions to images.

**Subtasks**:
1. Add caption field to image metadata schema
2. Add caption input to upload modal
3. Add caption editing to image detail modal
4. Display captions in gallery view (on hover or always visible)
5. Add /api/images/<filename>/caption endpoint
6. **[TESTING BREAKPOINT]** Test caption creation and editing

**Testing**: Add captions to images, verify they display and persist.

---

### CP5-T7: Create Admin Dashboard
**Priority**: Low
**Estimated Context**: 30%
**Requires Testing**: Yes

**Current Issue**: No overview of system status and usage.

**Subtasks**:
1. Create /api/stats endpoint (total images, devices, storage, users)
2. Add upload trends data (images per day/week)
3. Add device activity metrics (last seen, total requests)
4. Create dashboard UI page with charts
5. Add user management interface (if multi-user)
6. Add system health indicators
7. **[TESTING BREAKPOINT]** Test dashboard with various data scenarios

**Testing**: View dashboard, verify statistics are accurate.

**Dependencies**: Best implemented after most other features are complete.

---

## CP6: Documentation & API Improvements

### CP6-T1: Add OpenAPI/Swagger Documentation
**Priority**: Medium
**Estimated Context**: 25%
**Requires Testing**: Yes

**Current Issue**: API only documented in markdown.

**Subtasks**:
1. Add flask-swagger-ui to requirements.txt
2. Create openapi.yaml specification file
3. Document all API endpoints with request/response schemas
4. Add authentication documentation
5. Set up Swagger UI at /api/docs
6. **[TESTING BREAKPOINT]** Test interactive API documentation

**Testing**: Access /api/docs, verify all endpoints documented correctly.

**Benefit**: Interactive API testing, auto-generated client libraries.

---

### CP6-T2: Implement API Versioning
**Priority**: Medium
**Estimated Context**: 20%
**Requires Testing**: Yes

**Current Issue**: Breaking changes would affect all clients.

**Subtasks**:
1. Create /api/v1/ blueprint
2. Move all current endpoints to v1
3. Add /api/version endpoint showing current API version
4. Update frontend to use /api/v1/ endpoints
5. Add deprecation notices for old endpoints
6. Update multi-device documentation
7. **[TESTING BREAKPOINT]** Test all endpoints under new version path

**Testing**: Verify all functionality works under /api/v1/ path.

**Benefit**: Future-proofing for API changes.

---

### CP6-T3: Standardize API Response Format
**Priority**: Medium
**Estimated Context**: 25%
**Requires Testing**: Yes

**Current Issue**: Inconsistent response formats across endpoints.

**Subtasks**:
1. Design standard response envelope {success, data, error}
2. Create response wrapper helper functions
3. Update all endpoints to use standard format
4. Add error code enumeration
5. Update frontend to handle new response format
6. **[TESTING BREAKPOINT]** Test all API responses match standard format

**Testing**: Call all endpoints, verify consistent format.

**Benefit**: Easier client development, better error handling.

---

### CP6-T4: Update Documentation
**Priority**: Low
**Estimated Context**: 20%
**Requires Testing**: No

**Current Issue**: Documentation doesn't reflect all new features.

**Subtasks**:
1. Update README.md with new features
2. Create CONTRIBUTING.md
3. Create architecture diagram
4. Update multi-device-instructions.md
5. Add CHANGELOG.md tracking all improvements
6. Create deployment guide

**Testing**: Review documentation for accuracy and completeness.

**Timing**: Should be done last, after all features implemented.

---

# Dependency Management & Compatibility

## Final Dependency List (Optimized)

All dependencies have been reviewed for conflicts and Raspberry Pi compatibility:

```python
# Current (already installed)
Flask>=3.0.0
flask-cors>=4.0.0
Pillow>=10.0.0

# Security Checkpoint (CP1)
Flask-Limiter>=3.5.0      # Rate limiting
Flask-Login>=0.6.3        # Authentication
Flask-WTF>=1.2.0          # CSRF protection

# Configuration (CP4)
python-dotenv>=1.0.0      # Environment variables

# Testing (CP4)
pytest>=7.4.0
pytest-flask>=1.3.0

# WebSockets (CP5) - REQUIRES WSGI SERVER CHANGE
Flask-SocketIO>=5.3.0
python-socketio>=5.9.0
eventlet>=0.33.0          # WSGI server for WebSocket support

# Documentation (CP6)
flask-swagger-ui>=4.11.1  # API documentation
```

## Dependencies Avoided (Optimizations)

The following dependencies were **removed** from the original plan in favor of better alternatives:

1. **python-magic** → Replaced with **Pillow's Image.verify()**
   - Reason: python-magic requires system library `libmagic` which may not be installed on Raspberry Pi
   - Solution: Use existing Pillow dependency's built-in image verification

2. **imghdr** → Replaced with **Pillow's Image.verify()**
   - Reason: Deprecated in Python 3.11+, removed in Python 3.13
   - Solution: Use existing Pillow dependency

3. **piexif** → Replaced with **Pillow's Image.getexif()**
   - Reason: Unmaintained (last update 2018)
   - Solution: Pillow has built-in EXIF support

4. **SQLAlchemy** → Use **Python's built-in sqlite3 module**
   - Reason: Adds complexity, not needed for this use case
   - Solution: Raw SQLite with Python's standard library

## Built-in Python Modules Used

The following use **no additional dependencies**:

- `sqlite3` - Database (Python standard library)
- `subprocess` - Secure command execution (Python standard library)
- `fcntl` - File locking (Python standard library, Unix only)
- `json` - JSON handling (Python standard library)

## Compatibility Notes

### Python Version Requirements
- **Minimum**: Python 3.9 (for Flask 3.0 support)
- **Recommended**: Python 3.10+ (for better type hints)
- **Avoid**: Python 3.13+ until all dependencies are tested (imghdr removed)

### Raspberry Pi Compatibility
- ✅ All chosen dependencies work on ARM64 architecture
- ✅ No system libraries required (except those in standard Raspberry Pi OS)
- ✅ eventlet tested and working on Raspberry Pi
- ✅ Minimal memory footprint (important for Pi's limited resources)

### Flask Extension Compatibility
All Flask extensions are compatible with each other:
- Flask-Login + Flask-WTF + Flask-SocketIO = ✅ No conflicts
- Flask-Limiter works alongside all other extensions = ✅
- All extensions support Flask 3.0+ = ✅

## Architectural Considerations

### WebSocket Implementation (CP5-T1)
**Important**: This requires switching WSGI servers:

**Current**: Flask development server
```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, ssl_context=(cert, key))
```

**After WebSocket**: eventlet WSGI server
```python
if __name__ == '__main__':
    import eventlet
    import eventlet.wsgi
    eventlet.wsgi.server(eventlet.wrap_ssl(eventlet.listen(('0.0.0.0', 5000)),
                         certfile=cert, keyfile=key, server_side=True), app)
```

**Impact**:
- Systemd service file must be updated
- Different process management
- Slightly different performance characteristics
- **Recommendation**: Implement this task last

### SQLite vs JSON (CP2-T5)
Migrating to SQLite makes several tasks obsolete or easier:
- **Obsolete**: CP4-T1 (file locking) - SQLite handles this internally
- **Easier**: CP3-T6 (albums) - relational DB is better for this
- **Better**: All concurrent access scenarios

---

# Implementation Strategy

## Recommended Order

1. **Start with CP1 (Security)** - Fix critical vulnerabilities first
2. **Then CP2 (Performance)** - Especially thumbnails and SQLite migration
3. **Then CP4 (Reliability)** - Improve stability before adding features
4. **Then CP3 (UX)** - Enhance user experience with stable foundation
5. **Then CP5 (New Features)** - Add bells and whistles
6. **Finally CP6 (Documentation)** - Document everything

## Key Dependencies

- **CP2-T5 (SQLite)** should be done before:
  - CP3-T6 (Albums) - easier with relational DB
  - CP4-T1 (File locking) - becomes obsolete with SQLite

- **CP1-T5 (Authentication)** should be done before:
  - CP5-T4 (Activity log) - needs user tracking

- **CP4-T5 (Split frontend)** should be done before:
  - Major frontend additions - avoids merge conflicts

## Context Management

Each task is estimated to use 10-35% of Claude's context window:
- Tasks are sized to leave 30-40% remaining
- Allows room for exploration and error handling
- Safe margin for autocompact triggers

**For AI Implementers**:
- Monitor your context usage throughout task execution
- If you reach **60-70% context usage** during a task, STOP and prepare for handoff
- Update `upgrade_progress.json` with your current position
- Inform the user that context limits require a new session
- Do NOT try to complete a task if it will exceed safe context limits
- It's better to hand off mid-task than to run out of context unexpectedly

## Testing Breakpoints

Tasks with `requires_testing: true` include testing breakpoints where implementation should pause for human verification. This ensures:
- Changes work correctly before proceeding
- Issues caught early
- User can provide feedback

**For AI Implementers**: When you encounter a subtask marked with `"testing_breakpoint": true`:
1. **STOP** implementation at that point
2. Update the subtask status to `"awaiting_testing"` in `upgrade_progress.json`
3. **Inform the user** that testing is required before proceeding
4. Provide clear testing instructions based on the task's **Testing** section
5. **Do NOT continue** to the next subtask until user confirms testing passed
6. This is NOT about running automated tests - this is about human verification with real hardware/usage

**For AI Implementers**: When you encounter a subtask marked with `"critical_safety_step": true`:
1. These are backup/safety operations that **MUST** be completed before proceeding with potentially destructive changes
2. **Pause** and verify backup completion with the user
3. Do NOT proceed with subsequent subtasks until user confirms the backup is complete and verified
4. Examples: Backing up JSON files before SQLite migration, backing up server.py before switching WSGI servers

## Progress Tracking

After completing each subtask, update `upgrade_progress.json`:
```json
{
  "subtasks": [
    {
      "id": "CP1-T1-S1",
      "status": "completed"  // Update this
    }
  ]
}
```

When all subtasks in a task are complete, update the task status.
When all tasks in a checkpoint are complete, update the checkpoint status.

---

# Handoff Protocol

When a Claude session needs to hand off to another:

1. **Update `upgrade_progress.json`** with:
   - `last_updated`: Current timestamp
   - `current_checkpoint`: Checkpoint ID being worked on
   - `current_task`: Task ID being worked on
   - All completed subtask statuses

2. **Create handoff message** for user:
   ```
   I've completed [tasks] and am ready to hand off.

   Completed:
   - [List completed items]

   Next steps:
   - [List next items]

   The next Claude session should start with [specific task].
   ```

3. **New session reads**:
   - `upgrade_progress.json` for current state
   - This UPGRADE_PLAN.md for task details
   - Any notes in the progress file

---

# Notes

- **Raspberry Pi Constraints**: Monitor SD card space, especially with storage quota task
- **Backup Before Major Changes**: Especially before SQLite migration
- **Test with Real Hardware**: E-paper display changes need physical testing
- **Authentication Impact**: Will require user migration/setup
- **SQLite Migration**: Major architectural change, test thoroughly

---

# Support

For questions about this plan:
1. Review task details in this document
2. Check `upgrade_progress.json` for current status
3. Review dependencies section for task relationships
4. Ask user for clarification if needed

---

**Document Version**: 1.0
**Created**: 2025-11-22
**Last Updated**: 2025-11-22
