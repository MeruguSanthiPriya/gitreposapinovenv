import requests
from bs4 import BeautifulSoup
import re
import pandas as pd

def scrape_github(github_id):
    if not github_id or pd.isna(github_id) or str(github_id).strip().lower() == "none" or not str(github_id).strip():
        return {"error": "No GitHub ID provided", "count": 0, "repos": []}
    try:
        github_id = github_id.strip()
        if not re.match(r'^[a-zA-Z0-9\-]+$', github_id):
            return {"error": "Invalid GitHub ID format", "count": 0, "repos": []}
        
        url = f"https://github.com/{github_id}?tab=repositories"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")
        repo_list = soup.find("div", id="user-repositories-list")
        if not repo_list:
            return {"error": "No repositories found", "count": 0, "repos": []}

        repos = repo_list.find_all("li", class_="source")
        repo_data = []
        for repo in repos:
            name_elem = repo.find("a", itemprop="name codeRepository")
            name = name_elem.get_text().strip() if name_elem else "Unknown"
            link = f"https://github.com/{github_id}/{name}" if name != "Unknown" else ""
            language_elem = repo.find("span", itemprop="programmingLanguage")
            language = language_elem.get_text().strip() if language_elem else "Unknown"
            description_elem = repo.find("p", itemprop="description")
            description = description_elem.get_text().strip() if description_elem else ""
            repo_data.append({"name": name, "link": link, "language": language, "description": description})

        return {"repos": repo_data, "count": len(repo_data)}
    except requests.exceptions.RequestException as e:
        return {"error": f"Network error: {str(e)}", "count": 0, "repos": []}
    except Exception as e:
        return {"error": f"Scraping error: {str(e)}", "count": 0, "repos": []}