import time
from fastapi import FastAPI, Request, BackgroundTasks
from google.cloud import firestore

# Import the runner we just created
from agent_runner import run_agent

db = firestore.Client()
app = FastAPI()

PROTECTED_BRANCHES = ["main", "master", "develop", "staging"]

@app.get("/")
async def root():
    return {"status": "running"}

@app.post("/webhook")
async def webhook(request: Request, background_tasks: BackgroundTasks):
    payload = await request.json()

    # Ensure it's a push event
    if payload.get("object_kind") != "push":
         return {"status": "skipped", "reason": "not a push event"}

    # Extract Push event fields
    repo_id = payload["project"]["id"]
    repo_name = payload["project"]["name"]
    branch = payload["ref"].replace("refs/heads/", "")
    pusher = payload["user_username"]

    # Infinite Loop Protection: Skip branches that are themselves Nightshift fix branches
    if branch.startswith("nightshift/"):
        return {"status": "skipped", "reason": "nightshift branch"}

    # Optional: Only scan protected branches
    if branch not in PROTECTED_BRANCHES:
        return {"status": "skipped", "reason": "not a protected branch"}

    # Scan Cooldown: Prevent multiple rapid pushes from spamming scans
    recent = db.collection("jobs")\
        .where("repo_id", "==", repo_id)\
        .where("status", "==", "scanning")\
        .limit(1).get()

    if len(recent) > 0:
        return {"status": "skipped", "reason": "scan already in progress"}

    # Save job to Firestore
    job_id = f"scan-{repo_id}-{int(time.time())}"
    db.collection("jobs").document(job_id).set({
        "job_id": job_id,
        "repo_id": repo_id,
        "repo_name": repo_name,
        "branch": branch,
        "pusher": pusher,
        "status": "scanning",
        "bugs_found": 0,
        "mrs_opened": [],
        "started_at": firestore.SERVER_TIMESTAMP
    })

    # Trigger agent in background
    background_tasks.add_task(run_agent, job_id, repo_id, repo_name, branch)

    return {"status": "accepted", "job_id": job_id}