from my_agent.gitlab_tools import (
    list_projects,
    get_repository_tree,
    get_file_contents,
    create_branch,
    create_commit,
    create_merge_request
)
import os
from google.adk.agents.llm_agent import Agent

PROMPT_PATH = os.path.join(os.path.dirname(__file__), "system_prompt.txt")
with open(PROMPT_PATH, "r") as f:
    nightshift_instructions = f.read()

nightshift_agent = Agent(
    model='gemini-2.5-flash', # Upgraded to Pro as per the PDF documentation
    name='nightshift_scanner',
    description="Autonomous proactive code scanner that finds bugs and opens GitLab Merge Requests.",
    instruction=nightshift_instructions,
    tools=[
        list_projects,
        get_repository_tree,
        get_file_contents,
        create_branch,
        create_commit,
        create_merge_request
    ]
)

def invoke_agent(user_input: str) -> str:
    """
    Passes the repository details to the agent and returns its text output.
    """
    print("Invoking Vertex AI Agent...")
    response = nightshift_agent.run(user_input) 
    
    return response.text if hasattr(response, 'text') else str(response)