"""Dependency-free local demo server for the static dashboard."""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

from .pipeline import result_to_dict, run_demo_pipeline, graph

from dataclasses import asdict, is_dataclass

def to_dict(obj):
    if obj is None:
        return None
    if is_dataclass(obj):
        return asdict(obj)
    if isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_dict(v) for v in obj]
    return obj


ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = ROOT / "web"


class DemoHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    def do_GET(self) -> None:
        if self.path.startswith("/api/health"):
            self.write_json({"status": "ok"})
            return

        if self.path == "/api/competitors":
            try:
                from .db_client import DBClient
                db = DBClient()
                conn = db.get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM competitors")
                rows = cursor.fetchall()
                conn.close()
                competitors = [row["name"] for row in rows]
                self.write_json(competitors)
            except Exception as exc:
                import traceback
                traceback.print_exc()
                self.write_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        if self.path.startswith("/api/graph/start"):
            from urllib.parse import urlparse, parse_qs
            import uuid
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            competitor = params.get("competitor", ["HubSpot"])[0]

            thread_id = str(uuid.uuid4())

            if graph is None:
                try:
                    res = run_demo_pipeline(competitor)
                    self.write_json({
                        "competitor_name": competitor,
                        "footprint": [to_dict(f) for f in res.footprint],
                        "signals": [to_dict(s) for s in res.signals],
                        "hypotheses": [to_dict(h) for h in res.hypotheses if h.status != "suppressed"],
                        "generated_at": res.generated_at,
                        "thread_id": thread_id,
                        "status": "interrupted",
                        "recommendations": [],
                        "executive_summary": res.executive_summary,
                        "intelligence_pillars": res.intelligence_pillars,
                        "strategic_risks": res.strategic_risks,
                        "strategic_opportunities": res.strategic_opportunities,
                        "watch_list": res.watch_list
                    })
                except ValueError as exc:
                    self.write_json({"error": str(exc)}, status=HTTPStatus.NOT_FOUND)
                return

            config = {"configurable": {"thread_id": thread_id}}
            try:
                events = []
                for event in graph.stream({"competitor_name": competitor}, config):
                    events.append(event)
                
                state = graph.get_state(config)
                
                # Check state values and run demo pipeline to fallback load the pillar details
                res_demo = run_demo_pipeline(competitor)
                
                footprint = [to_dict(f) for f in state.values.get("footprint", [])]
                signals = [to_dict(s) for s in state.values.get("signals", [])]
                hypotheses = [to_dict(h) for h in state.values.get("hypotheses", []) if h.status != "suppressed"]
                
                from .schemas import utc_now_iso
                self.write_json({
                    "competitor_name": competitor,
                    "footprint": footprint,
                    "signals": signals,
                    "hypotheses": hypotheses,
                    "generated_at": utc_now_iso(),
                    "thread_id": thread_id,
                    "status": "interrupted" if state.next else "completed",
                    "recommendations": [],
                    "executive_summary": res_demo.executive_summary,
                    "intelligence_pillars": res_demo.intelligence_pillars,
                    "strategic_risks": res_demo.strategic_risks,
                    "strategic_opportunities": res_demo.strategic_opportunities,
                    "watch_list": res_demo.watch_list
                })
            except Exception as exc:
                import traceback
                traceback.print_exc()
                self.write_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        if self.path.startswith("/api/graph/resume"):
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            thread_id = params.get("thread_id", [None])[0]

            if not thread_id:
                self.write_json({"error": "Missing thread_id query parameter"}, status=HTTPStatus.BAD_REQUEST)
                return

            if graph is None:
                try:
                    res = run_demo_pipeline("HubSpot")
                    self.write_json({
                        "recommendations": [to_dict(r) for r in res.recommendations],
                        "status": "completed"
                    })
                except ValueError as exc:
                    self.write_json({"error": str(exc)}, status=HTTPStatus.NOT_FOUND)
                return

            config = {"configurable": {"thread_id": thread_id}}
            try:
                state_before = graph.get_state(config)
                if not state_before.next:
                    self.write_json({
                        "recommendations": [to_dict(r) for r in state_before.values.get("recommendations", [])],
                        "status": "completed"
                    })
                    return

                events = []
                for event in graph.stream(None, config):
                    events.append(event)
                
                state_after = graph.get_state(config)
                recs = [to_dict(r) for r in state_after.values.get("recommendations", [])]
                self.write_json({
                    "recommendations": recs,
                    "status": "completed"
                })
            except Exception as exc:
                import traceback
                traceback.print_exc()
                self.write_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        if self.path.startswith("/api/competitors/compare"):
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            comp1 = params.get("comp1", [None])[0]
            comp2 = params.get("comp2", [None])[0]

            if not comp1 or not comp2:
                self.write_json({"error": "Missing comp1 or comp2 query parameter"}, status=HTTPStatus.BAD_REQUEST)
                return

            try:
                res1 = run_demo_pipeline(comp1)
                res2 = run_demo_pipeline(comp2)
                self.write_json({
                    "comp1": {
                        "competitor_name": comp1,
                        "hypotheses": [to_dict(h) for h in res1.hypotheses if h.status != "suppressed"]
                    },
                    "comp2": {
                        "competitor_name": comp2,
                        "hypotheses": [to_dict(h) for h in res2.hypotheses if h.status != "suppressed"]
                    }
                })
            except ValueError as exc:
                self.write_json({"error": str(exc)}, status=HTTPStatus.NOT_FOUND)
            return

        if self.path.startswith("/api/competitors/") and self.path.endswith("/run"):
            competitor_name = unquote(self.path.removeprefix("/api/competitors/").removesuffix("/run"))
            try:
                self.write_json(to_dict(run_demo_pipeline(competitor_name)))
            except ValueError as exc:
                self.write_json({"error": str(exc)}, status=HTTPStatus.NOT_FOUND)
            return

        super().do_GET()

    def do_POST(self) -> None:
        if self.path == "/api/feedback":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8"))
                competitor_name = data.get("competitor_name")
                hypothesis_id = data.get("hypothesis_id")
                vote = data.get("vote")
                comments = data.get("comments", "")
                
                if vote not in ("thumbs_up", "thumbs_down") or not competitor_name or not hypothesis_id:
                    self.write_json({"error": "invalid feedback record fields"}, status=HTTPStatus.BAD_REQUEST)
                    return
                
                from .db_client import DBClient
                from .schemas import utc_now_iso
                db = DBClient()
                conn = db.get_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO feedback (competitor_name, hypothesis_id, vote, comments, timestamp) VALUES (?, ?, ?, ?, ?)",
                    (competitor_name, hypothesis_id, vote, comments, utc_now_iso())
                )
                conn.commit()
                conn.close()
                self.write_json({"status": "success"})
            except Exception as exc:
                import traceback
                traceback.print_exc()
                self.write_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        self.send_error(HTTPStatus.NOT_IMPLEMENTED, "Unsupported method")

    def write_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> int:
    ports = [8000, 8080, 8085]
    server = None
    last_err = None
    for port in ports:
        try:
            server = ThreadingHTTPServer(("localhost", port), DemoHandler)
            print(f"Serving Competitive Intelligence Agent at http://localhost:{port}")
            server.serve_forever()
            return 0
        except Exception as e:
            print(f"[Warning] Failed to bind to port {port}: {e}")
            last_err = e
    if last_err:
        raise last_err
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
