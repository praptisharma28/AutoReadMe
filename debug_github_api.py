import requests
import os
import re

def test_github_api():
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        token = input("\n   Enter your GitHub token to test: ").strip()
        if not token:
            return False
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    try:
        response = requests.get("https://api.github.com")
        if response.status_code != 200:
            return False
    except Exception:
        return False
    
    try:
        response = requests.get("https://api.github.com/user", headers=headers)
        if response.status_code != 200:
            return False
    except Exception:
        return False
    
    owner, repo = "octocat", "Hello-World"
    try:
        url = f"https://api.github.com/repos/{owner}/{repo}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return False
        return True
    except Exception:
        return False

def quick_repo_test(repo_url):
    match = re.search(r'github\.com/([^/]+)/([^/]+)', repo_url)
    if not match:
        return
    
    owner, repo = match.groups()
    repo = repo.rstrip('.git')
    
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        token = input("Enter your GitHub token: ").strip()
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    url = f"https://api.github.com/repos/{owner}/{repo}"
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
    except Exception:
        return None

if __name__ == "__main__":
    if test_github_api():
        test_url = input("\nEnter a GitHub repository URL to test (or press Enter for default): ").strip()
        if not test_url:
            test_url = "https://github.com/streamlit/streamlit"
        quick_repo_test(test_url)
