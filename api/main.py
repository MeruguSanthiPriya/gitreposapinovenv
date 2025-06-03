from fastapi import FastAPI
from pydantic import BaseModel
from github_scraper import scrape_github

app = FastAPI()

class GitHubRequest(BaseModel):
    github_id: str

@app.post("/scrape-github")
def scrape_github_api(request: GitHubRequest):
    return scrape_github(request.github_id)