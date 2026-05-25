import re
from google.cloud import firestore
# Import the function we will create in your agent.py
from my_agent.agent import invoke_agent

db = firestore.Client()

def extract_all_mr_urls(agent_output: str) -> list[str]:
    """Pull all GitLab MR URLs from agent output text."""
    pattern = r'https://gitlab\.com/[\w\-]+/[\w\-]+/-/merge_requests/\d+'
    return list(set(re.findall(pattern, agent_output)))

def run_agent(job_id: str, repo_id: str, repo_name: str, branch: str):
    print(f"Starting Nightshift scan for {repo_name} on branch {branch}...")
    
    # 1. Format the new proactive Agent Input
    agent_input = f"""
    Scan this GitLab repository for bugs and open merge requests for each one.
    Repository ID: {repo_id}
    Repository name: {repo_name}
    Branch to scan: {branch}
    GitLab URL: https://gitlab.com
    Begin your scan now. Follow the steps in your system prompt exactly.
    """

    try:
        # 2. Call your Vertex AI Agent
        agent_output = invoke_agent(agent_input)
        
        # 3. Extract all MR URLs from the agent's response
        mr_urls = extract_all_mr_urls(agent_output)

        # 4. Update Firestore with the completed status
        db.collection("jobs").document(job_id).update({
            "status": "complete",
            "bugs_found": len(mr_urls),
            "mrs_opened": mr_urls,
            "completed_at": firestore.SERVER_TIMESTAMP
        })
        print(f"Scan complete. Found {len(mr_urls)} bugs.")
        
    except Exception as e:
        print(f"Agent failed: {e}")
        db.collection("jobs").document(job_id).update({
            "status": "failed",
            "error": str(e),
            "completed_at": firestore.SERVER_TIMESTAMP
        })