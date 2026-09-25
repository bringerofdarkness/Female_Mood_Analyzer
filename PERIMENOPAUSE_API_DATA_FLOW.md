# Perimenopause API Data Flow

## Data Source

All data comes from **AWS RDS MySQL Database** (pulse_mysql):

| Table | What It Stores |
|-------|---|
| `health_logs` | User symptom logs (mood, energy, symptoms JSON, notes) |
| `menstrual_cycles` | Period dates, cycle status (regular/irregular/absent) |
| `users` | User profile information |

---

## API Endpoint

```
GET /api/v1/menopause/dashboard?user_id={id}&period={7d|30d|90d}
```

### Period Parameter
- `7d`: Last 7 days (2026-09-18 to 2026-09-25)
- `30d`: Last 30 days (2026-08-26 to 2026-09-25)
- `90d`: Last 90 days (2026-06-27 to 2026-09-25)

---

## Response Structure

### 1. **transition_stage_tracker**
```json
{
  "menopause_stage": "perimenopause|menopause|postmenopause|unknown",
  "is_in_perimenopause": true/false,
  "months_since_last_period": number,
  "last_period_date": "YYYY-MM-DD",
  "cycle_status": "regular|irregular|absent"
}
```
**Source:** `menstrual_cycles` table  
**Calculated:** Stage determined by months since last period + cycle irregularity

---

### 2. **vasomotor_tracker**
```json
{
  "total_events": 0,
  "avg_daily_frequency": 0.0,
  "hot_flash_events": 0,
  "night_sweat_events": 0,
  "events": [
    {
      "event_date": "2026-08-09",
      "event_type": "hot_flash",
      "severity": 6,
      "trigger": "caffeine",
      "duration_minutes": 10
    }
  ]
}
```
**Source:** `health_logs.symptoms` → `hot_flash` and `night_sweat` fields  
**How it works:**
1. Parse symptom list: `["Hot flashes", "Brain fog", ...]`
2. Normalize to dict: `{"hot_flashes": "moderate", ...}`
3. Extract vasomotor events
4. Calculate averages per day

**Result if no data:** `total_events: 0`, empty events array

---

### 3. **gsm_health** (Genitourinary Syndrome of Menopause)
```json
{
  "vaginal_dryness": {
    "level": "not_reported|mild|moderate|severe",
    "value": 0-8,
    "percentage": 0-100
  },
  "urinary_frequency": {...},
  "pelvic_discomfort": {...},
  "libido_impact": {...}
}
```
**Source:** `health_logs.symptoms` → GSM-specific fields  
**Note:** Most users return `"not_reported"` because list-format data doesn't contain GSM fields

---

### 4. **symptom_matrix**
```json
{
  "entries": [
    {
      "log_date": "2026-08-09",
      "mood": "🙂",
      "energy_level": "Very Low",
      "brain_fog": "mild",
      "fatigue": "moderate",
      "cramps": "moderate"
    }
  ],
  "most_common_symptoms": ["cramps", "headache", "insomnia", "brain_fog", "bloating"],
  "symptom_frequency": {
    "cramps": 1,
    "brain_fog": 0.5,
    "headache": 1
  },
  "symptom_correlations": [
    {
      "from": "Mood",
      "to": "Cramps",
      "percentage": 100,
      "description": "Mood and Cramps occur together."
    }
  ],
  "avg_sleep_hours": 7,
  "avg_mood_stability_percent": 50,
  "avg_energy_level_percent": 40
}
```
**Source:** `health_logs` (mood, energy_level, symptoms)  
**Calculated:**
- **Entries:** Each log date with parsed symptom data
- **Most Common Symptoms:** Top 5 symptoms by frequency
- **Symptom Frequency:** Count / number of logs (0-1 scale)
- **Correlations:** Symptoms that appear together
- **Averages:** Sleep (default 7 if not logged), mood stability, energy level

**Default values when no data:**
- `avg_sleep_hours: 7` (reasonable human average)
- `avg_mood_stability_percent: 50` (neutral)
- `avg_energy_level_percent: 50` (neutral)

---

## Data Processing Workflow

```
User Request (user_id=9, period=90d)
    ↓
Query AWS RDS Database
    ├─ health_logs WHERE user_id=9 AND log_date BETWEEN 2026-06-27 AND 2026-09-25
    └─ menstrual_cycles WHERE user_id=9 LIMIT 12
    ↓
Parse Symptoms
    ├─ Input: ["Cramps", "Brain fog", "Hot flashes"]
    ├─ Normalize: {"cramps": "moderate", "brain_fog": "mild", "hot_flashes": "moderate"}
    └─ Type check: Skip if still list format (old data only)
    ↓
Build Response
    ├─ Extract vasomotor events
    ├─ Calculate GSM health
    ├─ Build symptom matrix
    ├─ Calculate correlations
    └─ Determine menopause stage
    ↓
Return JSON Response
```

---

## Key Implementation Details

### Symptom Format Conversion
**Problem:** Database stores symptoms as JSON arrays (old format) or objects (new format)

**Solution:** `_normalize_symptoms()` function converts both to standard dict:
```python
Old: ["Cramps", "Brain fog"] 
    ↓ (via _normalize_symptoms)
New: {"cramps": "moderate", "brain_fog": "mild"}
```

### Date Range Filtering
- **7d endpoint:** Only includes logs from last 7 days
- **30d endpoint:** Only includes logs from last 30 days
- **90d endpoint:** Only includes logs from last 90 days
- **Result:** Different users return different data based on when they logged

### No Hardcoding
✅ All values from AWS database  
✅ All calculations dynamic (not manual values)  
✅ Works for any user_id, any date range  
✅ Handles missing data gracefully (returns 0, "not_reported", or defaults)

---

## Example: User 9, 90d Period

**Database has:**
- 2 health_logs (2026-08-09, 2026-08-11)
- Symptoms: `["Cramps", "Brain fog", "Headache", "Insomnia", "Bloating", "Fatigue", "Hot flashes"]`
- Mood: 🙂, Energy: "Very Low" / "High"

**API returns:**
- ✅ 2 entries in symptom_matrix
- ✅ 5 most common symptoms
- ✅ 5 symptom correlations
- ✅ avg_energy_level: 40% (calculated from Energy levels)
- ✅ avg_sleep_hours: 7 (no numeric data logged, uses default)
- ⚠️ Vasomotor events: 0 (no hot_flash/night_sweat count field in list format)

---

## Data Completeness by User

| User | Health Logs | Has Symptoms | 90d Events | 90d Symptoms |
|------|---|---|---|---|
| 1 | 0 | - | 0 | 0 |
| 9 | 2 | ✅ | 0 | 5 |
| 10 | 1 | ✅ | 0 | 5 |
| 11 | 1 | ✅ | 0 | 5 |

**Note:** All users return 0 vasomotor events because symptom list format doesn't include event counts.
