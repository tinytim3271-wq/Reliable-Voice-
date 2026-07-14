from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from uuid import uuid4


@dataclass
class Estimate:
    labor_hours: float
    labor_rate: float
    parts_cost: float

    @property
    def total(self) -> float:
        return round((self.labor_hours * self.labor_rate) + self.parts_cost, 2)


SYMPTOM_RULES: dict[str, dict[str, Any]] = {
    "no-start": {
        "keywords": ("won't start", "wont start", "no start", "clicking", "dead battery"),
        "summary": "No-start condition reported",
        "diagnostics": [
            "Perform battery state-of-charge and load test.",
            "Inspect starter circuit voltage drop and starter relay operation.",
            "Scan for powertrain fault codes and verify crank/cam signal during cranking.",
        ],
        "repairs": [
            "Replace failed battery/starter/relay component identified during testing.",
            "Repair high-resistance or open circuit wiring in start system.",
            "Clear fault codes and verify multiple successful restart cycles.",
        ],
        "labor_hours": 2.0,
        "parts_cost": 150.0,
    },
    "overheating": {
        "keywords": ("overheat", "overheating", "hot", "temp high", "coolant"),
        "summary": "Engine overheating concern reported",
        "diagnostics": [
            "Pressure test cooling system and inspect for external leaks.",
            "Verify coolant flow, thermostat function, and radiator fan operation.",
            "Check for combustion gas intrusion and confirm water pump performance.",
        ],
        "repairs": [
            "Replace failed cooling component(s) found during diagnosis.",
            "Repair leaks and refill/bleed cooling system to specification.",
            "Road test under load and confirm normal operating temperature.",
        ],
        "labor_hours": 2.5,
        "parts_cost": 220.0,
    },
    "brake-noise": {
        "keywords": ("brake noise", "squeal", "grinding", "brakes"),
        "summary": "Brake noise/performance concern reported",
        "diagnostics": [
            "Inspect pad/shoe thickness and rotor/drum condition.",
            "Measure rotor runout/thickness variation and caliper operation.",
            "Evaluate hydraulic system, fluid condition, and road-test brake response.",
        ],
        "repairs": [
            "Replace worn pads/rotors/shoes/drums as required.",
            "Service or replace seized caliper or slide hardware.",
            "Bleed brakes and verify stopping performance with post-repair road test.",
        ],
        "labor_hours": 2.0,
        "parts_cost": 280.0,
    },
}

DEFAULT_FLOW = {
    "summary": "General drivability concern reported",
    "diagnostics": [
        "Interview customer concerns and verify complaint during inspection.",
        "Perform full-system scan for stored/active diagnostic trouble codes.",
        "Execute guided pinpoint tests for failed subsystem based on scan and symptom data.",
    ],
    "repairs": [
        "Perform repair based on confirmed root cause from diagnostic process.",
        "Re-test repaired system and clear/verify no returning faults.",
        "Provide documented findings and recommendations to service advisor.",
    ],
    "labor_hours": 1.5,
    "parts_cost": 120.0,
}


def _match_symptom(transcript: str) -> dict[str, Any]:
    lowered = transcript.lower()
    for config in SYMPTOM_RULES.values():
        if any(keyword in lowered for keyword in config["keywords"]):
            return config
    return DEFAULT_FLOW


def build_work_order(payload: dict[str, Any], labor_rate: float = 120.0) -> dict[str, Any]:
    transcript = str(payload.get("call_transcript", "")).strip()
    if not transcript:
        raise ValueError("call_transcript is required")

    customer_name = str(payload.get("customer_name", "Unknown Customer")).strip() or "Unknown Customer"
    phone = str(payload.get("phone", "")).strip()
    vehicle = str(payload.get("vehicle", "Vehicle not provided")).strip() or "Vehicle not provided"

    symptom_plan = _match_symptom(transcript)
    estimate = Estimate(
        labor_hours=float(symptom_plan["labor_hours"]),
        labor_rate=float(labor_rate),
        parts_cost=float(symptom_plan["parts_cost"]),
    )

    return {
        "work_order_id": f"WO-{uuid4().hex.upper()}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "customer": {
            "name": customer_name,
            "phone": phone,
            "vehicle": vehicle,
        },
        "call_summary": symptom_plan["summary"],
        "customer_statement": transcript,
        "estimate": {
            **asdict(estimate),
            "total": estimate.total,
        },
        "technician_instructions": {
            "diagnostic_steps": symptom_plan["diagnostics"],
            "repair_steps_after_root_cause_confirmed": symptom_plan["repairs"],
        },
    }


class VoiceIntakeHandler(BaseHTTPRequestHandler):
    def _respond(self, code: int, body: dict[str, Any]) -> None:
        response = json.dumps(body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def do_POST(self) -> None:
        # BaseHTTPRequestHandler requires this exact method name.
        if self.path != "/intake-call":
            self._respond(404, {"error": "Not Found"})
            return

        try:
            raw_length = self.headers.get("Content-Length", "0")
            length = int(raw_length)
            raw_payload = self.rfile.read(length)
            payload = json.loads(raw_payload or b"{}")
            work_order = build_work_order(payload)
            self._respond(200, work_order)
        except ValueError as exc:
            self._respond(400, {"error": str(exc)})
        except json.JSONDecodeError:
            self._respond(400, {"error": "Invalid JSON payload"})


def run(host: str = "127.0.0.1", port: int = 8080) -> None:
    server = HTTPServer((host, port), VoiceIntakeHandler)
    print(f"Reliable-Voice- intake service running at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
