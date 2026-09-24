# Beauty & Radiance Endpoint Documentation

**Endpoint:** `POST /api/v1/beauty/overview`  
**Service:** `ai/services/beauty_service.py`  
**Routes:** `ai/routes/beauty_routes.py`  
**Models:** `ai/models/beauty_models.py`  
**Database:** AWS RDS MySQL - `pulse_mysql` database  
**Last Updated:** 2026-09-24  
**Status:** ✅ BUGS FIXED & TESTED

---

## 1. Data Sources & How Data is Generated

### 1.1 Skin Scan Metrics (Scores: 80, 72, 22, 84, 68, 79, 81)

**Where They Come From:**
1. User uploads skin image via Skin Scan API endpoint
2. `ai/services/skin_scan_service.py` receives image bytes
3. Calls Claude AI with vision capabilities to analyze the image
4. Claude performs AI analysis and returns JSON with 7 metric scores:
   - `overall_score` (0-100)
   - `hydration_score` (0-100)
   - `redness_score` (0-100)
   - `texture_score` (0-100)
   - `luminosity_score` (0-100)
   - `firmness_score` (0-100)
   - `clarity_score` (0-100)
5. Results are **persisted to AWS RDS MySQL** in `skin_scans` table
6. Beauty API retrieves these scores from database

**Key Point:** Scores are **NOT hardcoded or static** - each score is Claude's AI analysis of an actual uploaded skin image.

### 1.2 Cycle Phase Data

**Where It Comes From:**
- User's menstrual cycle data from `menstrual_cycles` table in AWS RDS
- Beauty API maps skin scan dates to cycle phases using menstrual cycle dates
- Calculates average skin score for each phase (menstrual, follicular, ovulation, luteal)

### 1.3 Sleep & Activity Correlations

**Where They Come From:**
- External Terra Data API (health wearables integration)
- Fetched via `_fetch_terra_activity_data()` in beauty_service.py

### 1.4 AI Insights & Personalized Recommendations

**Where They Come From (ONLY if user has scan data):**
1. Check: Does user have scan data?
2. If **YES**: Call Claude LLM to generate personalized insights
3. If **NO**: Skip Claude call, return `ai_insights: null`

---

## 2. AWS RDS Database Connection Details

**Server Type:** Amazon RDS MySQL 8.0.46  
**Host:** `mysql-database.cc98ouaycdke.us-east-1.rds.amazonaws.com`  
**Port:** `3306`  
**Database:** `pulse_mysql`  
**Region:** us-east-1  
**Table:** `skin_scans` (stores all skin metrics)

**Connection Configuration (from `.env`):**
```
MYSQL_HOST=mysql-database.cc98ouaycdke.us-east-1.rds.amazonaws.com
MYSQL_PORT=3306
MYSQL_USER=pulse
MYSQL_PASSWORD=Pul$$e2026_mysql
MYSQL_DATABASE=pulse_mysql
```

---

## 3. Fixed Problems - Bug Fixes Applied

### Bug Fix #1: TodayScan Validation Errors (500 Error)

**Problem:** Beauty API returned HTTP 500 errors when constructing TodayScan model

**Root Cause:** Database query returned partial data; Pydantic model validation failed

**Solution Applied (Lines 428-453 in beauty_service.py):**
Added setdefault() calls for all 19 required fields before Pydantic instantiation

**Status:** ✅ FIXED

### Bug Fix #2: Hardcoded Cycle Phase Scores for All Users

**Problem:** ALL users received identical scores: menstrual=62, follicular=75, ovulation=84, luteal=70

**Root Cause:** Function had hardcoded return statement; never queried database

**Solution Applied (Lines 819-955 in beauty_service.py):**
Completely rewrote to query menstrual_cycles table and calculate per-phase averages

**Status:** ✅ FIXED - Each user now gets personalized phase scores

### Bug Fix #3: Best/Worst Phases Set Even With Zero Data

**Problem:** Best/worst phases set to "ovulation"/"menstrual" even when user had NO scan data

**Root Cause:** Logic didn't check if actual data existed

**Solution Applied (Lines 940-950 in beauty_service.py):**
Added conditional: only set phases if max_score > 0, else return None

**Status:** ✅ FIXED

### Bug Fix #4: Claude LLM Called Even When User Has No Scan Data

**Problem:** Beauty API called Claude LLM even when user had NO skin scan data

**Root Cause:** Early return logic missing

**Solution Applied:**
- Added early return check at Lines 403-415 in beauty_service.py
- Made ai_insights Optional in beauty_models.py (Line 80)

**Status:** ✅ FIXED

---

## 4. Implementation Details

### Files Modified
1. **`ai/models/beauty_models.py`** - Made ai_insights Optional (Line 80)
2. **`ai/services/beauty_service.py`** - Fixed 4 bugs (Lines 403, 428-453, 819-955, 940-950)
3. **`ai/routes/beauty_routes.py`** - No changes needed

### Request Structure
```json
{
  "user_id": 30,
  "days": 30,
  "include_correlations": true
}
```

**Parameters:**
- `user_id` (int, required): User identifier
- `days` (int, optional): Historical days to analyze (default: 30)
- `include_correlations` (bool, optional): Include cycle & sleep correlations (default: true)

---

## 5. Response Examples

### Response WITH Scan Data
```json
{
  "today": {
    "overall_score": 80,
    "hydration_score": 72,
    "redness_score": 22,
    "texture_score": 84
  },
  "history": [...],
  "correlations": {...},
  "ai_insights": {
    "overall_assessment": "Your skin is glowing!",
    "confidence_score": 0.92
  }
}
```

### Response WITHOUT Scan Data
```json
{
  "today": null,
  "history": [],
  "correlations": {...},
  "ai_insights": null
}
```

---

## 6. Testing Guide

### Test 1: User WITH Scan Data
```bash
curl -X POST http://localhost:8002/api/v1/beauty/overview \
  -H "Content-Type: application/json" \
  -d '{"user_id": 30, "days": 30, "include_correlations": true}'
```
**Expected:** Full response with ai_insights (not null)

### Test 2: User WITHOUT Scan Data
```bash
curl -X POST http://localhost:8002/api/v1/beauty/overview \
  -H "Content-Type: application/json" \
  -d '{"user_id": 999, "days": 30, "include_correlations": true}'
```
**Expected:** today=null, ai_insights=null (no Claude call made)

---

## 7. Deployment & Docker Status

### Docker Container
- **Image:** `softvence/pulse_ai:latest`
- **Port Mapping:** `8002:8000`
- **Status:** Running
- **Last Build:** 2026-09-24

### What's Working ✅
- ✅ Skin scores from Claude AI analysis (NOT hardcoded)
- ✅ Cycle phase data personalized per user (NOW dynamic)
- ✅ Early return prevents wasted Claude calls
- ✅ Graceful null handling when no data exists
- ✅ 500 errors eliminated

---

## 8. Database Schema Reference

### skin_scans Table (AWS RDS - pulse_mysql)
```sql
CREATE TABLE skin_scans (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  overall_score INT,
  hydration_score INT,
  redness_score INT,
  texture_score INT,
  luminosity_score INT,
  firmness_score INT,
  clarity_score INT,
  skin_findings JSON,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### menstrual_cycles Table (AWS RDS - pulse_mysql)
```sql
CREATE TABLE menstrual_cycles (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  start_date DATE,
  end_date DATE,
  phase VARCHAR(20),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
);
```

---

## 9. Summary of Changes

| # | Issue | Root Cause | Fix | File | Lines | Status |
|---|-------|-----------|-----|------|-------|--------|
| 1 | TodayScan 500 error | Missing Pydantic fields | Added setdefault() | `beauty_service.py` | 428-453 | ✅ |
| 2 | Hardcoded cycle phases | Ignored user_id param | Database queries | `beauty_service.py` | 819-955 | ✅ |
| 3 | Fake best/worst phases | No zero-data check | Conditional return | `beauty_service.py` | 940-950 | ✅ |
| 4 | Wasted Claude calls | Missing early return | Check & Optional | `beauty_service.py` + `beauty_models.py` | 403-415, 80 | ✅ |

---

## 10. Reference Information

**Backend Language:** Python 3.12  
**Web Framework:** FastAPI 0.139.2  
**Data Validation:** Pydantic v2.13.4  
**Database:** MySQL 8.0.46 on AWS RDS  
**AI Model:** Claude Opus 4.7  
**Docker Image:** softvence/pulse_ai:latest

---

**Documentation Updated:** 2026-09-24  
**All 4 Bugs Fixed and Documented ✅**

