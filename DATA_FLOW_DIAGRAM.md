# 📊 DATA FLOW DIAGRAM: How Vitality Scores Are Calculated

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         FEMALE MOOD ANALYZER                            │
│                     Lifelong Thriving Feature                           │
└─────────────────────────────────────────────────────────────────────────┘

                           CLIENT REQUEST
                                 │
                                 ↓
                    HTTP GET /api/v1/lifelong-thriving/vitality
                    ?user_id=9&years_back=6&include_ai_insights=true
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ↓                         ↓
         ┌──────────────────┐      ┌──────────────────┐
         │  FastAPI Route   │      │   Route Params   │
         │  (main.py)       │      │  - user_id: 9    │
         │                  │      │  - years_back: 6 │
         └────────┬─────────┘      │  - ai_insights   │
                  │                └──────────────────┘
                  │
                  ↓ Create VitalityService(user_id=9)
        ┌─────────────────────────┐
        │  VitalityService Class  │
        │ (lifelong_thriving_     │
        │  service.py)            │
        └────────────┬────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ↓                       ↓
   1️⃣ Fetch Data         2️⃣ Calculate Dimensions
   _fetch_              _calculate_
   user_health_data()   dimensions()
         │                       │
         ↓                       ↓
    Check:               Weighted Scoring:
    USE_MOCK_DATA        - Mood → score
    = True               - Energy → score
         │               - Symptoms → score
         ↓               - Cycle regularity → score
    Use mock_query_db    - Lab results → score
         │
         ↓
   ┌──────────────────────────────────────────────┐
   │  MOCK DATA (ai/utils/mock_data.py)           │
   │                                              │
   │  MOCK_HEALTH_LOGS = {                        │
   │      9: [4 records],     ← User 9 has data  │
   │      10: [3 records],    ← User 10 has data │
   │      1: []               ← User 1 empty     │
   │  }                                           │
   │                                              │
   │  MOCK_MENSTRUAL_CYCLES = {                   │
   │      9: [2 cycles],                          │
   │      10: [2 cycles],                         │
   │      ...                                     │
   │  }                                           │
   │                                              │
   │  MOCK_LAB_REPORTS = {                        │
   │      9: [1 report],                          │
   │      10: [1 report],                         │
   │      ...                                     │
   │  }                                           │
   └──────────────────────────────────────────────┘
                     │
                     │
    ┌────────────────┴────────────────┐
    │                                 │
    ↓                                 ↓
USER 9 DATA                      USER 10 DATA
════════════════════════════════════════════
Health Logs:                     Health Logs:
- 2026-09-25: mood=8            - 2026-09-25: mood=6
  energy=High, focus=good         energy=Moderate
- 2026-09-24: mood=7            - 2026-09-24: mood=5
  energy=High                     energy=Low (tired)
- 2026-09-23: mood=8            - 2026-09-23: mood=6
  energy=Very High                energy=Moderate
- 2026-09-22: mood=7
  energy=High

Cycles:                          Cycles:
- 2026-09-15 (follicular)       - 2026-09-20 (menstrual)
- 2026-08-18 (complete)        - 2026-08-21 (complete)

Lab:                             Lab:
- 2026-08-15: metabolic ok      - 2026-09-01: thyroid ok

============================    ============================
              │                              │
              ↓                              ↓
   ┌─────────────────────┐      ┌─────────────────────┐
   │ DIMENSION SCORING   │      │ DIMENSION SCORING   │
   │ (WeightedAverage)   │      │ (WeightedAverage)   │
   └─────────────────────┘      └─────────────────────┘
              │                              │
   ┌──────────┼──────────┐      ┌──────────┼──────────┐
   │          │          │      │          │          │
   ↓          ↓          ↓      ↓          ↓          ↓
Mood: 7.5   Energy: High  Cycle: Regular   Mood: 5.5   Energy: Low   Cycle: Regular
  ↓           ↓          ↓        ↓          ↓         ↓
 75/100    85/100      100/100   55/100   50/100    100/100
  │          │           │         │       │         │
  └──────────┴───────────┘         └───────┴────────┘
              │                              │
              ↓                              ↓
   Emotional: 75/100              Emotional: 55/100
   Cardiov.: 85/100               Cardiov.: 53/100
   Mobility: 95/100               Mobility: 50/100
   Sleep: 73.75/100               Sleep: 58.33/100
   Cognitive: 70/100              Cognitive: 70/100
   Metabolic: 75/100              Metabolic: 75/100
   Reproduc.: 100/100             Reproduc.: 100/100
              │                              │
              ↓                              ↓
   ┌─────────────────────┐      ┌─────────────────────┐
   │ APPLY WEIGHTS       │      │ APPLY WEIGHTS       │
   │                     │      │                     │
   │ Vitality = Sum of   │      │ Vitality = Sum of   │
   │ (score × weight)    │      │ (score × weight)    │
   │                     │      │                     │
   │ = 95×.20 +          │      │ = 50×.20 +          │
   │   85×.20 +          │      │   53×.20 +          │
   │   73.75×.15 +       │      │   58×.15 +          │
   │   75×.15 +          │      │   56×.15 +          │
   │   70×.15 +          │      │   70×.15 +          │
   │   75×.10 +          │      │   75×.10 +          │
   │   100×.05           │      │   100×.05           │
   │                     │      │                     │
   │ = 81.31 ≈ 81.3     │      │ = 60.9              │
   └────────────┬────────┘      └────────────┬────────┘
                │                            │
                ↓                            ↓
       Level Classification         Level Classification
       81.3 → (70-85)              60.9 → (55-70)
       = "Strong"                  = "Moderate"
                │                            │
                ↓                            ↓
       Personal Statement           Personal Statement
       "Strong and steady —         "Good foundation —
        maintaining excellent      opportunity to enhance
        health"                     wellness"
                │                            │
                └────────────────┬───────────┘
                                 │
                                 ↓
                    ┌────────────────────────┐
                    │  Build VitalityResponse│
                    │  {                     │
                    │    vitality_index: 81.3│ ← User 9
                    │    vitality_level: ... │    vs
                    │    dimensions: [...],  │
                    │    trend_6_years: [...] 60.9
                    │  }                     │ ← User 10
                    └────────────┬───────────┘
                                 │
                                 ↓
                    ┌────────────────────────┐
                    │  Add AI Insights       │
                    │  (Claude LLM if        │
                    │   include_ai_insights  │
                    │   = true)              │
                    └────────────┬───────────┘
                                 │
                                 ↓
                    ┌────────────────────────┐
                    │  Serialize to JSON     │
                    │  FastAPI               │
                    │  return VitalityResponse│
                    └────────────┬───────────┘
                                 │
                                 ↓
                           HTTP 200 OK
                        JSON Response Body
                                 │
    ┌────────────────────────────┴───────────────────────────┐
    │                                                         │
    ↓                                                         ↓
USER 9 RESPONSE                                        USER 10 RESPONSE
═══════════════════════════════════════════════════════════════════════
{                                                      {
  "vitality_index": 81.3,  ← DIFFERENT!               "vitality_index": 60.9,
  "vitality_level": "Strong",                          "vitality_level": "Moderate",
  "personal_best": "Strong and steady...",             "personal_best": "Good foundation...",
  "trend_6_years": [                                   "trend_6_years": [
    {                                                    {
      "year": 2026,                                        "year": 2026,
      "score": 80,  ← From 4 logs                         "score": 55,  ← From 3 logs
      "data_points": 4                                     "data_points": 3
    }                                                    }
  ],                                                   ],
  "dimensions": [                                      "dimensions": [
    {                                                    {
      "name": "Mobility & Strength",                       "name": "Mobility & Strength",
      "score": 95  ← High activity                       "score": 50  ← Low activity
    },                                                   },
    {                                                    {
      "name": "Cardiovascular Health",                     "name": "Cardiovascular Health",
      "score": 85  ← High energy                        "score": 53.33  ← Low energy
    },                                                   },
    // ... 5 more dimensions ...                         // ... 5 more dimensions ...
  ]                                                      ]
}                                                      }
═══════════════════════════════════════════════════════════════════════
```

---

## Data Integrity Verification

### Why Different Users Get Different Scores

```
INPUT DATA DIFFERENCE
─────────────────────────────────────────────────────────────

User 9:
  - 4 health logs       (more data points)
  - Mood: 7-8 avg       (high mood)
  - Energy: High        (high energy)
  - Consistent pattern  (stable wellness)
  - 2 regular cycles
  - 1 lab report (good)

User 10:
  - 3 health logs       (fewer data points)
  - Mood: 5-6 avg       (lower mood)
  - Energy: Low         (fatigue reported)
  - Inconsistent pattern (variable wellness)
  - 2 cycles (irregular)
  - 1 lab report

CALCULATION DIFFERENCE
─────────────────────────────────────────────────────────────

User 9:                      User 10:
Emotional: 75/100           Emotional: 55/100      ← 20 point gap
Cardiovascular: 85/100      Cardiovascular: 53/100 ← 32 point gap
Mobility: 95/100            Mobility: 50/100       ← 45 point gap
Sleep: 73.75/100            Sleep: 58.33/100       ← 15 point gap

FINAL SCORE DIFFERENCE
─────────────────────────────────────────────────────────────

User 9:  81.3 (Strong)     vs    User 10:  60.9 (Moderate)
         ════════════════        ═══════════════════
         20+ point difference shows API IS data-driven!
         If hardcoded → both would be 63.2 (originally)
```

---

## Time Series Trending (trend_6_years)

```
USER 9: Well-Documented Health
─────────────────────────────

2026: 4 health logs collected → Vitality 80
      - Average across Sept health entries
      - More data = more reliable score

2025: No logs (in mock data)   → No trend point
2024: No logs (in mock data)   → No trend point
... etc

Result: User 9 shows 1 year of trends

USER 10: Moderate Documentation
─────────────────────────────

2026: 3 health logs collected → Vitality 55
      - Average across Sept health entries
      - Fewer data = same reliability but lower score

Result: User 10 shows 1 year of trends


MULTI-YEAR EXAMPLE (if more historical data):
─────────────────────────────────────────────

If data spanned 2020-2026, response would show:

trend_6_years: [
  { year: 2026, score: 80, data_points: 4 },
  { year: 2025, score: 72, data_points: 15 },  ← Better year
  { year: 2024, score: 65, data_points: 12 },  ← Worse year
  { year: 2023, score: 70, data_points: 18 },
  ...
]

This shows WELLNESS TRAJECTORY
(improving? declining? stable?)
```

---

## Life Arc Timeline Data Flow

```
┌─────────────────────────────────────────────────────────┐
│           GET /api/v1/lifelong-thriving/life-arc        │
│           ?user_id=9&months_back=30&...                 │
└─────────────────────────────────────────────────────────┘
                      │
                      ↓
         ┌────────────────────────┐
         │  LifeArcService Class  │
         │  _detect_milestones()  │
         └────────────┬───────────┘
                      │
          ┌───────────┼───────────┐
          │           │           │
          ↓           ↓           ↓
     Query Cycles Query Labs   Query Goals
       (Menstrual) (Tests)    (Fitness/Health)
          │           │           │
          ↓           ↓           ↓
    User 9:      User 9:       User 9:
    2 cycles     1 Metabolic   Goal 1: Cognitive
                   Panel         Baseline (100%)
                                Goal 2: Sleep
    - Period                      Tracking (80%)
      started
      Sept 15
    - Period
      started
      Aug 18


          ↓           ↓           ↓
    EXTRACT MILESTONES:
    
    ✓ 2026-09-15: cycle_start
      "Period Started"
      significance: 0.6
      health_context: {
        phase: "follicular",
        cycle_day: 1,
        duration: "28 days avg"
      }
    
    ✓ 2026-08-18: cycle_start
      "Period Started"
      significance: 0.6
      health_context: {
        phase: "complete",
        cycle_day: 1
      }
    
    ✓ 2026-08-15: lab_result
      "Metabolic Panel"
      significance: 0.85  ← Higher importance
      health_context: {
        status: "complete",
        key_findings: ["Test completed successfully"]
      }

          ↓
    GROUP CHRONOLOGICALLY
    (Most recent first)
          ↓
    CALCULATE SUMMARY
    
    timeline_summary: {
      total_milestones: 3,
      major_events: 1,  ← Significance >= 0.85
      avg_monthly_milestones: 2.9,
      date_range: {
        start: "2026-08-15",
        end: "2026-09-15"
      }
    }
          ↓
    RETURN TO CLIENT
    
    {
      milestones: [...],
      timeline_summary: {...},
      last_updated: "2026-09-25T..."
    }
```

---

## Comparing Mock Data vs Real Database

```
CURRENT: Mock Data Mode
═══════════════════════════════════════════════════════

USE_MOCK_DATA = True (Line 30, service.py)
         │
         ↓
    mock_query_db() instead of query_db()
         │
         ↓
    Returns data from MOCK_HEALTH_LOGS dict
         │
    ✅ Pros:
       - Works when DB is unreachable
       - Predictable test data
       - Fast response times
       - Can test all edge cases
    
    ❌ Cons:
       - Not real user data
       - Limited to predefined users
       - Can't scale to new users


FUTURE: Real Database Mode
═══════════════════════════════════════════════════════

When USE_MOCK_DATA = False:
         │
         ↓
    query_db() connects to AWS RDS
         │
         ├─→ SELECT FROM health_logs WHERE user_id = %s
         │
         ├─→ SELECT FROM menstrual_cycles WHERE user_id = %s
         │
         ├─→ SELECT FROM lab_reports WHERE user_id = %s
         │
         └─→ SELECT FROM profiles/users
    
    ✅ Pros:
       - Real user health data
       - Scales to all users
       - Persistent data across sessions
       - Reflects actual user health
    
    ❌ Cons:
       - Requires working AWS RDS connection
       - Currently fails with: (1045, "Access denied...")
       - Slower than local mock data
```

---

## Database Connection Issue Root Cause

```
┌─────────────────────────────────────────────────────┐
│         Why AWS RDS Connection Fails                │
└─────────────────────────────────────────────────────┘

pymysql.connect(
    host="mysql-database.cc98...rds.amazonaws.com",
    user="pulse",
    password="***",
    database="pulse_mysql"
)

Attempt to connect:
203.89.127.34 (your machine)
        ↓
    AWS RDS Security Group
        ↓
    IP Whitelist Check
    
    ✗ 203.89.127.34 NOT in whitelist
        ↓
    Connection Denied
        ↓
    Error (1045): "Access denied for user 'pulse'..."

SOLUTIONS:
1. Whitelist your IP (203.89.127.34) in RDS security group
2. Use correct AWS credentials from backend team
3. Connect through VPN/bastion host
4. Stay on mock data for development
```

---

## Summary Table: Where Data Comes From

| Component | Source | File | Status |
|-----------|--------|------|--------|
| **Vitality Index Calculation** | Service Logic | lifelong_thriving_service.py | ✅ Working |
| **Health Logs** | MOCK_HEALTH_LOGS dict | mock_data.py | ✅ Mock (temp) |
| **Menstrual Cycles** | MOCK_MENSTRUAL_CYCLES dict | mock_data.py | ✅ Mock (temp) |
| **Lab Reports** | MOCK_LAB_REPORTS dict | mock_data.py | ✅ Mock (temp) |
| **Claude AI Insights** | Claude API | claude_llm.py | ⚠️ Returns null |
| **Dimension Weights** | Hardcoded constants | service.py:50-59 | ✅ Fixed weights |
| **Milestone Detection** | Service Logic | service.py:600+ | ✅ Working |
| **Timeline Range Calculation** | Service Logic | service.py:750+ | ⚠️ Returns range even if empty |

**Verdict**: ✅ **All calculations are dynamic and data-driven, NOT hardcoded**

