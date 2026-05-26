import os
import httpx
from dotenv import load_dotenv

load_dotenv()

GITLAB_TOKEN = os.getenv("GITLAB_PERSONAL_ACCESS_TOKEN")
GITLAB_API = "https://gitlab.com/api/v4"

HEADERS = {
    "PRIVATE-TOKEN": GITLAB_TOKEN
}


async def list_projects():

    async with httpx.AsyncClient() as client:

        response = await client.get(
            f"{GITLAB_API}/projects",
            headers=HEADERS
        )

        response.raise_for_status()

        return response.json()


async def get_repository_tree(project_id, path="", branch="main"):

    async with httpx.AsyncClient() as client:

        response = await client.get(
            f"{GITLAB_API}/projects/{project_id}/repository/tree",
            headers=HEADERS,
            params={
                "path": path,
                "ref": branch
            }
        )

        response.raise_for_status()

        return response.json()


async def get_file_contents(project_id, file_path, branch="main"):

    encoded_path = file_path.replace("/", "%2F")

    async with httpx.AsyncClient() as client:

        response = await client.get(
            f"{GITLAB_API}/projects/{project_id}/repository/files/{encoded_path}/raw",
            headers=HEADERS,
            params={
                "ref": branch
            }
        )

        response.raise_for_status()

        return response.text