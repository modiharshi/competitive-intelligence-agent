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


def create_app():
    try:
        from fastapi import FastAPI
        from fastapi.staticfiles import StaticFiles
    except ModuleNotFoundError as exc:
        raise RuntimeError("Install project dependencies to run the API: fastapi uvicorn") from exc

    app = FastAPI(title="Competitive Intelligence Agent")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/competitors/{competitor_name}/run")
    def run_competitor(competitor_name: str) -> dict:
        from .pipeline import run_demo_pipeline
        return to_dict(run_demo_pipeline(competitor_name))

    @app.get("/api/competitors")
    def list_competitors() -> list[str]:
        from .db_client import DBClient
        db = DBClient()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM competitors")
        rows = cursor.fetchall()
        conn.close()
        return [row["name"] for row in rows]

    @app.get("/api/competitors/compare")
    def compare_competitors(comp1: str, comp2: str) -> dict:
        from fastapi import HTTPException
        from .pipeline import run_demo_pipeline
        try:
            res1 = run_demo_pipeline(comp1)
            res2 = run_demo_pipeline(comp2)
            return {
                "comp1": {
                    "competitor_name": comp1,
                    "hypotheses": [to_dict(h) for h in res1.hypotheses if h.status != "suppressed"]
                },
                "comp2": {
                    "competitor_name": comp2,
                    "hypotheses": [to_dict(h) for h in res2.hypotheses if h.status != "suppressed"]
                }
            }
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc))

    @app.get("/api/graph/start")
    def graph_start(competitor: str = "HubSpot") -> dict:
        from fastapi import HTTPException
        import uuid
        from .pipeline import graph, run_demo_pipeline

        thread_id = str(uuid.uuid4())
        if graph is None:
            try:
                res = run_demo_pipeline(competitor)
                return {
                    "competitor_name": competitor,
                    "footprint": [to_dict(f) for f in res.footprint],
                    "signals": [to_dict(s) for s in res.signals],
                    "hypotheses": [to_dict(h) for h in res.hypotheses if h.status != "suppressed"],
                    "generated_at": res.generated_at,
                    "thread_id": thread_id,
                    "status": "completed",
                    "recommendations": [to_dict(r) for r in res.recommendations]
                }
            except ValueError as exc:
                raise HTTPException(status_code=404, detail=str(exc))

        config = {"configurable": {"thread_id": thread_id}}
        try:
            for event in graph.stream({"competitor_name": competitor}, config):
                pass
            
            # Auto-resume the graph immediately on the backend to bypass HITL interruption
            state = graph.get_state(config)
            if state.next:
                for event in graph.stream(None, config):
                    pass
            
            state = graph.get_state(config)
            footprint = [to_dict(f) for f in state.values.get("footprint", [])]
            signals = [to_dict(s) for s in state.values.get("signals", [])]
            hypotheses = [to_dict(h) for h in state.values.get("hypotheses", []) if h.status != "suppressed"]
            recs = [to_dict(r) for r in state.values.get("recommendations", [])]
            
            from .schemas import utc_now_iso
            return {
                "competitor_name": competitor,
                "footprint": footprint,
                "signals": signals,
                "hypotheses": hypotheses,
                "generated_at": utc_now_iso(),
                "thread_id": thread_id,
                "status": "completed",
                "recommendations": recs
            }
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))

    @app.get("/api/graph/resume")
    def graph_resume(thread_id: str) -> dict:
        from fastapi import HTTPException
        from .pipeline import graph, run_demo_pipeline

        if graph is None:
            try:
                res = run_demo_pipeline("HubSpot")
                return {
                    "recommendations": [to_dict(r) for r in res.recommendations],
                    "status": "completed"
                }
            except ValueError as exc:
                raise HTTPException(status_code=404, detail=str(exc))

        config = {"configurable": {"thread_id": thread_id}}
        try:
            state_before = graph.get_state(config)
            if not state_before.next:
                return {
                    "recommendations": [to_dict(r) for r in state_before.values.get("recommendations", [])],
                    "status": "completed"
                }

            events = []
            for event in graph.stream(None, config):
                events.append(event)
            
            state_after = graph.get_state(config)
            recs = [to_dict(r) for r in state_after.values.get("recommendations", [])]
            return {
                "recommendations": recs,
                "status": "completed"
            }
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))

    from pydantic import BaseModel
    class FeedbackInput(BaseModel):
        competitor_name: str
        hypothesis_id: str
        vote: str
        comments: str = ""

    @app.post("/api/feedback")
    def log_feedback(data: FeedbackInput) -> dict:
        from .db_client import DBClient
        from .schemas import utc_now_iso
        from fastapi import HTTPException
        if data.vote not in ("thumbs_up", "thumbs_down"):
            raise HTTPException(status_code=400, detail="invalid vote")
        
        db = DBClient()
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO feedback (competitor_name, hypothesis_id, vote, comments, timestamp) VALUES (?, ?, ?, ?, ?)",
                (data.competitor_name, data.hypothesis_id, data.vote, data.comments, utc_now_iso())
            )
            conn.commit()
        except Exception as exc:
            conn.close()
            raise HTTPException(status_code=500, detail=str(exc))
        conn.close()
        return {"status": "success"}

    app.mount("/", StaticFiles(directory="web", html=True), name="web")
    return app


app = create_app()
