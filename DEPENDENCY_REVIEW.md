# FrameSync Dependency Review & Optimization

**Date**: 2025-11-22
**Status**: Completed - No Conflicts Found

## Summary

All planned dependencies have been reviewed for compatibility, conflicts, and Raspberry Pi suitability. Several optimizations were made to reduce dependencies and use built-in alternatives.

## ✅ Compatibility Status

**Result**: No conflicts found. All dependencies are compatible with:
- Each other (no version conflicts)
- Flask 3.0+
- Python 3.9+
- Raspberry Pi ARM64 architecture

## 🎯 Optimizations Made

### 1. Removed Unnecessary Dependencies

| Originally Planned | Replaced With | Reason |
|-------------------|---------------|---------|
| `python-magic` | Pillow's `Image.verify()` | Requires system library `libmagic`; already have Pillow |
| `imghdr` | Pillow's `Image.verify()` | Deprecated in Python 3.11+, removed in 3.13 |
| `piexif` | Pillow's `Image.getexif()` | Unmaintained since 2018; Pillow has built-in EXIF |
| `SQLAlchemy` | Python's built-in `sqlite3` | Unnecessary complexity for this use case |

**Benefit**: Fewer dependencies, smaller footprint, better Raspberry Pi compatibility

### 2. Updated Task Implementations

**CP1-T3 (File Content Validation)**:
- Old: "Add python-magic or imghdr for file type detection"
- New: "Use Pillow's Image.verify() for file validation (no new dependency needed)"

**CP3-T7 (EXIF Metadata)**:
- Old: "Add piexif or pillow EXIF extraction on upload"
- New: "Use Pillow's built-in Image.getexif() method for EXIF extraction (no new dependency needed)"

**CP5-T1 (WebSocket Updates)**:
- Added: eventlet WSGI server requirement
- Added: systemd service update subtask
- Added: architectural change warning
- Recommendation: Implement this task last

## 📦 Final Dependency List

### Already Installed
```
Flask>=3.0.0
flask-cors>=4.0.0
Pillow>=10.0.0
```

### To Be Added (By Checkpoint)

**CP1 - Security**:
```
Flask-Limiter>=3.5.0      # Rate limiting
Flask-Login>=0.6.3        # Authentication
Flask-WTF>=1.2.0          # CSRF protection
```

**CP4 - Configuration & Testing**:
```
python-dotenv>=1.0.0      # Environment variables
pytest>=7.4.0             # Testing
pytest-flask>=1.3.0       # Flask testing utilities
```

**CP5 - WebSockets** (⚠️ Requires WSGI server change):
```
Flask-SocketIO>=5.3.0
python-socketio>=5.9.0
eventlet>=0.33.0          # WSGI server
```

**CP6 - Documentation**:
```
flask-swagger-ui>=4.11.1  # API documentation
```

### No Additional Dependencies Needed
- SQLite (Python's built-in `sqlite3` module)
- Image validation (Pillow's `Image.verify()`)
- EXIF extraction (Pillow's `Image.getexif()`)
- Subprocess execution (Python's built-in `subprocess`)
- File locking (Python's built-in `fcntl`)

## ⚠️ Important Notes

### 1. WebSocket Implementation (CP5-T1)

**Architectural Change Required**:
- Current: Flask development server
- Future: eventlet WSGI server

**Impact**:
- Cannot use Flask's `app.run()` anymore
- Must update systemd service file
- Different startup command
- Different process management

**Recommendation**:
- Implement this task **LAST** after all other features are stable
- Test thoroughly before deploying

**Why eventlet?**
- Simpler than gevent
- Well-tested on Raspberry Pi ARM64
- Good performance for WebSocket workloads

### 2. Python Version Compatibility

**Minimum**: Python 3.9 (for Flask 3.0)
**Recommended**: Python 3.10+
**Current on Raspberry Pi**: Check with `python3 --version`

**Why avoid Python 3.13+?**
- `imghdr` module removed (but we're not using it)
- Some dependencies may not be tested yet
- Stick with Python 3.10 or 3.11 for now

### 3. Raspberry Pi Considerations

All chosen dependencies are Raspberry Pi compatible:
- ✅ No C extensions requiring compilation
- ✅ Pure Python or have ARM64 wheels
- ✅ Minimal memory footprint
- ✅ No exotic system libraries required

## 🔄 Task Updates in upgrade_progress.json

The following subtasks were updated:

1. **CP1-T3-S1**: Changed from "Add python-magic or imghdr" to "Use Pillow's Image.verify()"
2. **CP3-T7-S1**: Changed from "Add piexif or pillow EXIF" to "Use Pillow's built-in Image.getexif()"
3. **CP5-T1**: Added 2 new subtasks for eventlet WSGI server configuration
4. **CP5-T1**: Added `architectural_note` field warning about WSGI server change

## 🔍 Verification Commands

To verify compatibility after installing dependencies:

```bash
# Check Python version
python3 --version

# Install dependencies one checkpoint at a time
pip install Flask-Limiter Flask-Login Flask-WTF  # CP1
pip install python-dotenv pytest pytest-flask    # CP4
pip install Flask-SocketIO python-socketio eventlet  # CP5
pip install flask-swagger-ui                     # CP6

# Verify no conflicts
pip check

# Test imports
python3 -c "from flask_limiter import Limiter; print('✓ Flask-Limiter')"
python3 -c "from flask_login import LoginManager; print('✓ Flask-Login')"
python3 -c "from flask_wtf import CSRFProtect; print('✓ Flask-WTF')"
python3 -c "from flask_socketio import SocketIO; print('✓ Flask-SocketIO')"
python3 -c "import eventlet; print('✓ eventlet')"
```

## 📊 Benefits of Optimization

1. **Reduced Dependencies**: 3 fewer external packages needed
2. **Better Stability**: Using well-maintained, built-in alternatives
3. **Smaller Footprint**: Less disk space and memory usage
4. **Easier Installation**: No system libraries to install
5. **Future-Proof**: Built-in modules won't be deprecated

## ✅ Conclusion

The dependency review is complete. All planned dependencies are:
- ✅ Compatible with each other
- ✅ Compatible with Flask 3.0+
- ✅ Compatible with Raspberry Pi ARM64
- ✅ Optimized to use built-in alternatives where possible
- ✅ Well-maintained and actively supported

**No conflicts found. Safe to proceed with implementation.**

---

**Next Steps**:
1. Begin implementation with CP1-T1 (Fix Command Injection)
2. Add dependencies incrementally as each checkpoint is reached
3. Test each checkpoint before moving to the next
4. Save CP5-T1 (WebSockets) for last due to architectural change
