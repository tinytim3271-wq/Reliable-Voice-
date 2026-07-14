# Reliable-Voice-
AI voice intake service for automotive/shop service calls.

## What this provides
This project includes a minimal Python HTTP service that accepts a call transcript and returns:
- A generated work order
- A preliminary estimate (labor + parts + total)
- Technician instructions for diagnosis and repair after root cause confirmation

## Run locally
```bash
python voice_service.py
```

Service endpoint:
- `POST /intake-call`

## Example request
```bash
curl -X POST http://127.0.0.1:8080/intake-call \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Alex Carter",
    "phone": "555-111-2222",
    "vehicle": "2018 Ford F-150",
    "call_transcript": "My truck wont start and I just hear clicking."
  }'
```

## Example response contents
- `work_order_id`
- `customer`
- `call_summary`
- `estimate`
- `technician_instructions.diagnostic_steps`
- `technician_instructions.repair_steps_after_root_cause_confirmed`

## Integration notes
Use the JSON response to populate your shop management software work-order and estimate records.
