import os
import time
import hmac
import hashlib
import asyncio

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from google.cloud import firestore
from dotenv import load_dotenv

load_dotenv()

db = firestore.Client()

SKIP_PREFIXES = ["nightshift/", "fix/", "hotfix/"]

PROTECTED_BRANCHES = ["main", "master", "develop", "staging"]


def verify_webhook_secret(payload_bytes: bytes, signature: str) -> bool:
    secret = os.getenv("GITLAB_WEBHOOK_SECRET", "")

    if not secret:
        return True

    expected = hmac.new(
        secret.encode(),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(
        f"sha256={expected}",
        signature
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Nightshift backend started")
    yield
    print("Nightshift backend stopped")


app = FastAPI(
    title="Nightshift Backend",
    lifespan=lifespan
)


@app.get("/")
async def health():
    return {
        "status": "ok",
        "service": "nightshift"
    }
from gitlab_service import list_projects


@app.get("/test-gitlab")
async def test_gitlab():

    projects = await list_projects()

    clean_projects = []
    for project in projects [:5]:
        clean_projects.append({
            "id": project.get("id"),
            "name": project.get("name"),
            "url": project.get("web_url")
        })
    return{
        "count": len(projects),
        "projects":clean_projects
    }

@app.post("/webhook")
async def webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    payload = await request.json()
    raw_body = await request.body()

    event_type = request.headers.get("X-Gitlab-Event", "")

    if event_type != "Push Hook":
        return {
            "status": "ignored",
            "reason": f"event type {event_type} not handled"
        }

    repo_id = str(payload["project"]["id"])
    repo_name = payload["project"]["name"]
    repo_url = payload["project"]["web_url"]
    branch = payload["ref"].replace("refs/heads/", "")
    pusher = payload.get("user_username", "unknown")

    if any(branch.startswith(p) for p in SKIP_PREFIXES):
        return {
            "status": "skipped",
            "reason": "nightshift branch"
        }

    if PROTECTED_BRANCHES and branch not in PROTECTED_BRANCHES:
        return {
            "status": "skipped",
            "reason": f"branch '{branch}' not in scan list"
        }

    running = (
        db.collection("jobs")
        .where("repo_id", "==", repo_id)
        .where("status", "==", "scanning")
        .limit(1)
        .get()
    )

    if len(running) > 0:
        return {
            "status": "skipped",
            "reason": "scan already in progress"
        }

    job_id = f"scan-{repo_id}-{int(time.time())}"

    db.collection("jobs").document(job_id).set({
        "job_id": job_id,
        "repo_id": repo_id,
        "repo_name": repo_name,
        "repo_url": repo_url,
        "branch": branch,
        "pusher": pusher,
        "status": "scanning",
        "bugs_found": 0,
        "mrs_opened": [],
        "started_at": firestore.SERVER_TIMESTAMP,
    })

    from agent_runner import run_agent

    background_tasks.add_task(
        run_agent,
        job_id,
        repo_id,
        repo_name,
        branch
    )

    return {
        "status": "accepted",
        "job_id": job_id
    }


@app.get("/jobs")
async def list_jobs(limit: int = 20):
    docs = (
        db.collection("jobs")
        .order_by(
            "started_at",
            direction=firestore.Query.DESCENDING
        )
        .limit(limit)
        .get()
    )

    return [
        {**d.to_dict(), "job_id": d.id}
        for d in docs
    ]


@app.get("/jobs/{job_id}")
async def get_job(job_id: str):
    doc = db.collection("jobs").document(job_id).get()

    if not doc.exists:
        raise HTTPException(
            status_code=404,
            detail="job not found"
        )

    return {
        **doc.to_dict(),
        "job_id": doc.id
    }