import httpx
from google.adk.tools import tool

MCP_PROXY_URL = "http://localhost:8001"

@tool
async def list_projects():
    """
    List GitLab projects accessible to the token.
    """

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{MCP_PROXY_URL}/tools/list_projects",
            json={}
        )

    return response.json()


@tool
async def get_repository_tree(project_id: str, path: str = ""):
    """
    Get all files in a GitLab repository.
    """

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{MCP_PROXY_URL}/tools/get_repository_tree",
            json={
                "project_id": project_id,
                "path": path
            }
        )

    return response.json()


@tool
async def get_file_contents(project_id: str, file_path: str, ref: str = "main"):
    """
    Read a file from a GitLab repository.
    """

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{MCP_PROXY_URL}/tools/get_file_contents",
            json={
                "project_id": project_id,
                "file_path": file_path,
                "ref": ref
            }
        )

    return response.json()


@tool
async def create_branch(project_id: str, branch_name: str, ref: str = "main"):
    """
    Create a GitLab branch.
    """

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{MCP_PROXY_URL}/tools/create_branch",
            json={
                "project_id": project_id,
                "branch_name": branch_name,
                "ref": ref
            }
        )

    return response.json()


@tool
async def create_commit(
    project_id: str,
    branch_name: str,
    commit_message: str,
    actions: list
):
    """
    Commit code changes to GitLab.
    """

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{MCP_PROXY_URL}/tools/create_commit",
            json={
                "project_id": project_id,
                "branch_name": branch_name,
                "commit_message": commit_message,
                "actions": actions
            }
        )

    return response.json()


@tool
async def create_merge_request(
    project_id: str,
    source_branch: str,
    target_branch: str,
    title: str,
    description: str
):
    """
    Open a GitLab Merge Request.
    """

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{MCP_PROXY_URL}/tools/create_merge_request",
            json={
                "project_id": project_id,
                "source_branch": source_branch,
                "target_branch": target_branch,
                "title": title,
                "description": description
            }
        )

    return response.json()