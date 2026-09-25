# Data Flow Analysis - Goal Alignment Check

## Goal Statement
**"Everything is AI-generated and dynamic. Not hardcoded or static."**

---

## Current API Status

### 1. ✅ Athlete Performance API (`/api/v1/athlete/readiness`)
**Data Flow**: User ID → Database (Terra) → Claude LLM → Personalized Response

| Component | Status | Details |
|-----------|--------|---------|
| **Data Source** | ✅ Dynamic | Fetches from `terra_activity_data` table |
| **Metrics Generation** | ✅ Dynamic | Claude LLM generates all values (HRV, Sleep, Recovery, Load) |
| **Alerts** | ✅ Dynamic | Claude LLM generates 3 personalized fatigue alerts |
| **Recommendations** | ✅ Dynamic | Phase-based but static response structure |
| **Error Handling** | ❌ BROKEN | Returns 200 with error dict instead of 404 |
| **Goal Alignment** | ⚠️ 95% | Nearly perfect except error handling |

**Issues Found**:
- Exception handler at line 140 catches HTTPException and converts to error dict
- Returns `{"status": "error", "message": "...", "user_id": 100}` with 200 status
- Should return 404 status code for non-existent users

---

### 2. ❓ Beauty/Radiance API (`/api/beauty-overview`)
**Data Flow**: User ID → Database (Terra Scans) → Claude LLM → Response

**Need to verify**:
- [ ] Are responses truly Claude-generated or using templates?
- [ ] What happens when user has no scan data?
- [ ] Error handling - 404 vs 200 with error dict?

---

### 3. ❓ Cycle/Fertility API (`/api/cycle-overview`)
**Data Flow**: User ID → Database (Menstrual Cycles) → Response

**Need to verify**:
- [ ] Is data truly dynamic or using default/template cycles?
- [ ] What if user has no cycle data?
- [ ] Is Claude LLM used for insights?

---

### 4. ❓ Other APIs (Daily Scripture, Health Trends, etc.)
**Need to verify**:
- [ ] Are these using Claude LLM or hardcoded responses?
- [ ] Data sources - database or static?
- [ ] Error handling - proper HTTP status codes?

---

## Critical Issues to Fix

### Issue #1: Error Handling (Priority: HIGH)
**Problem**: All APIs return 200 status with error dict instead of proper HTTP codes
```
WRONG:  200 OK  with {"status": "error", "message": "User not found"}
RIGHT:  404 Not Found with proper error response
```

**Affected Endpoints**:
- [ ] `/api/v1/athlete/readiness`
- [ ] `/api/beauty-overview`
- [ ] `/api/cycle-overview`
- [ ] All other endpoints

**Fix**: Use HTTPException with proper status codes in services AND don't catch them in try-except blocks

---

### Issue #2: Fallback/Default Values (Priority: MEDIUM)
**Problem**: When no data available, returning hardcoded defaults
```python
# WRONG - Hardcoded default
return {"value": 0, "trend": 0, "available": False}

# RIGHT - Claude should generate realistic estimate OR return 404
```

**Affected Code**:
- `_fetch_hrv_data()` line 172
- `_fetch_sleep_data()` line 228, 259
- `_fetch_recovery_data()` line 286
- `_fetch_training_load_data()` lines

**Fix**: 
1. For valid user with no data → Claude generates estimate based on defaults
2. For invalid user → Return 404 immediately
3. For missing data → Use Claude to estimate, don't return 0

---

### Issue #3: Hardcoded Phase Recommendations (Priority: LOW)
**Problem**: Phase recommendations have hardcoded workout lists
```python
"menstrual": PhaseRecommendation(
    workout_type="recovery",
    intensity_level="low",
    suggested_workouts=[
        "Restorative yoga",  # ← Hardcoded
        "Light walking or leisurely cycling",  # ← Hardcoded
    ],
),
```

**Fix**: Generate recommendations via Claude LLM instead of static dicts

---

## Data Flow Verification Checklist

### For Each API Endpoint:
- [ ] Is HTTP status code correct (404, 500, 200)?
- [ ] Are values from database or Claude LLM?
- [ ] If no data: Claude generates OR 404 returned?
- [ ] Error messages are descriptive?
- [ ] No hardcoded static responses?
- [ ] Personalized to user (not generic)?

---

## Recommended Implementation Order

1. **FIRST**: Fix error handling (404 status codes)
   - Remove try-except that catches HTTPException
   - Use proper HTTP exception raising
   - Takes: 30 minutes

2. **SECOND**: Verify all APIs follow same error pattern
   - Audit all services
   - Standardize error responses
   - Takes: 1 hour

3. **THIRD**: Replace hardcoded defaults with Claude estimates
   - When no data available, use Claude to generate realistic values
   - Remove hardcoded 0s and defaults
   - Takes: 2 hours

4. **FOURTH**: Generate recommendations via Claude
   - Replace static phase recommendations
   - Make personalized to user's actual fitness level
   - Takes: 1 hour

5. **FIFTH**: Complete data flow testing
   - Test with real users (User 2, User 3, etc.)
   - Verify no hardcoded values anywhere
   - Takes: 1 hour

---

## Real User Impact

**If we don't fix this, real users will experience:**
1. ❌ Returning 200 OK with error messages (confuses apps)
2. ❌ Missing data returns zeros instead of personalized estimates
3. ❌ Some hardcoded responses that don't fit their data
4. ❌ Inconsistent error handling across APIs

**Result**: Backend team can't trust API responses, UI can't show errors properly, real users get poor experience
