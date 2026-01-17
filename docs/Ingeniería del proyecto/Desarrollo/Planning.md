┌─────────────────────────────────────────────────────────┐
│  MOBILE APP                                                                                  │
│                                                                                                        │
│  1. Collect GPS + sensor readings locally                                       │
│  2. Every 30-60 seconds (or every 50-100 points):                         │
│     → Upload batch to API                                                              │
│     → On success: clear uploaded points from local                       │
│     → On failure: keep locally, retry next cycle                                │
│  3. On session end: upload any remaining points                         │
└─────────────────────────────────────────────────────────┘

```
# 1. Start recording
POST /recordings/?user_id=1
{"line_id": 42, "direction": "northbound", "device_model": "iPhone 15"}
# Returns: {"id": 123, "status": "in_progress", ...}

# 2. Upload GPS batches every 30-60 seconds
POST /recordings/123/locations/batch
{"points": [
  {"timestamp": "2026-01-15T10:00:00Z", "latitude": 40.7128, "longitude": -74.0060, "speed": 5.2},
  {"timestamp": "2026-01-15T10:00:01Z", "latitude": 40.7129, "longitude": -74.0061, "speed": 5.1},
  ...
]}
# Returns: {"added": 50, "first_timestamp": "...", "last_timestamp": "..."}

# 3. End recording
POST /recordings/123/end
# Returns: {"id": 123, "status": "completed", "computed_path": [[lng, lat], ...]}
```

```
┌─────────────────────────────────────────────────────────────────┐
│  Timeline                                                       │
│                                                                 │
│  10:00  Session starts (status: IN_PROGRESS)                    │
│  10:01  Batch uploaded → last_activity_at = 10:01               │
│  10:02  Batch uploaded → last_activity_at = 10:02               │
│  10:03  📱 App crashes / user enters tunnel                     │
│   ...   (no more batches)                                       │
│  10:35  Cron runs cleanup(inactive_minutes=30)                  │
│         → Session marked ABANDONED                              │
│         → Path computed from existing points                    │
│         → Data preserved!                                       │
│                                                                 │
│  OR                                                             │
│                                                                 │
│  10:20  User comes back, calls POST /resume                     │
│         → Session back to IN_PROGRESS                           │
│         → Recording continues                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Cron setup example

Run every 15 minutes to catch abandoned sessions:

```
*/15 * * * * curl -X POST "https://api.example.com/recordings/cleanup/stale?inactive_minutes=30"
```