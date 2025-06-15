import os
import requests
import json
import base64
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import re

@dataclass
class RepoAnalysis:
    name: str
    description: str
    language: str
    languages: Dict[str, int]
    framework: str
    has_docker: bool
    has_requirements: bool
    has_package_json: bool
    has_setup_py: bool
    has_makefile: bool
    has_tests: bool
    license: Optional[str]
    topics: List[str]
    setup_instructions: List[str]
    dependencies: Dict[str, List[str]]
    file_structure: Dict[str, Any]

class GitHubRepoAnalyzer:
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/vnd.github.v3+json',
            'X-GitHub-Api-Version': '2022-11-28'
        }
        self.base_url = 'https://api.github.com'
    
    def test_token(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/user", headers=self.headers)
            return response.status_code == 200
        except Exception:
            return False
    
    def parse_github_url(self, url: str) -> tuple:
        url = url.rstrip('.git')
        patterns = [
            r'github\.com/([^/]+)/([^/]+)/?$',
            r'github\.com/([^/]+)/([^/]+)/.*',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1), match.group(2)
        
        raise ValueError(f"Invalid GitHub URL format: {url}")
    
    def get_repo_info(self, owner: str, repo: str) -> Dict:
        url = f"{self.base_url}/repos/{owner}/{repo}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 404:
            raise Exception(f"Repository not found: {owner}/{repo}")
        elif response.status_code == 403:
            raise Exception(f"Access denied. Check your token permissions: {response.status_code}")
        elif response.status_code != 200:
            raise Exception(f"Failed to fetch repo info: {response.status_code} - {response.text}")
        
        return response.json()
    
    def get_repo_contents(self, owner: str, repo: str, path: str = "") -> List[Dict]:
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            return []
        
        return response.json()
    
    def get_file_content(self, owner: str, repo: str, path: str) -> Optional[str]:
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        if data.get('encoding') == 'base64':
            try:
                content = base64.b64decode(data['content']).decode('utf-8')
                return content
            except Exception:
                return None
        
        return data.get('content')
    
    def get_languages(self, owner: str, repo: str) -> Dict[str, int]:
        url = f"{self.base_url}/repos/{owner}/{repo}/languages"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            return {}
        
        return response.json()
    
    def detect_framework(self, files: List[str], file_contents: Dict[str, str]) -> str:
        frameworks = []
        
        if 'package.json' in file_contents:
            try:
                package_data = json.loads(file_contents['package.json'])
                dependencies = {**package_data.get('dependencies', {}), 
                              **package_data.get('devDependencies', {})}
                
                if 'react' in dependencies: frameworks.append('React')
                if 'vue' in dependencies: frameworks.append('Vue.js')
                if '@angular/core' in dependencies: frameworks.append('Angular')
                if 'express' in dependencies: frameworks.append('Express.js')
                if 'next' in dependencies: frameworks.append('Next.js')
            except Exception:
                pass
        
        if 'requirements.txt' in file_contents:
            content = file_contents['requirements.txt'].lower()
            if 'django' in content: frameworks.append('Django')
            if 'flask' in content: frameworks.append('Flask')
            if 'fastapi' in content: frameworks.append('FastAPI')
            if 'streamlit' in content: frameworks.append('Streamlit')
        
        if 'manage.py' in files: frameworks.append('Django')
        if 'pom.xml' in files or 'build.gradle' in files: frameworks.append('Spring Boot')
        if 'composer.json' in files: frameworks.append('Laravel/PHP')
        if 'Gemfile' in files: frameworks.append('Ruby on Rails')
        
        return ', '.join(frameworks) if frameworks else 'Unknown'
    
    def extract_dependencies(self, file_contents: Dict[str, str]) -> Dict[str, List[str]]:
        dependencies = {}
        
        if 'requirements.txt' in file_contents:
            deps = []
            for line in file_contents['requirements.txt'].split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    package = re.split(r'[>=<!=]', line)[0].strip()
                    if package:
                        deps.append(package)
            dependencies['Python'] = deps
        
        if 'package.json' in file_contents:
            try:
                package_data = json.loads(file_contents['package.json'])
                deps = list(package_data.get('dependencies', {}).keys())
                dev_deps = list(package_data.get('devDependencies', {}).keys())
                if deps:
                    dependencies['Node.js'] = deps
                if dev_deps:
                    dependencies['Node.js Dev'] = dev_deps
            except Exception:
                pass
        
        if 'pom.xml' in file_contents:
            artifacts = re.findall(r'<artifactId>([^<]+)</artifactId>', file_contents['pom.xml'])
            if artifacts:
                dependencies['Java (Maven)'] = artifacts
        
        return dependencies
    
    def generate_setup_instructions(self, analysis: 'RepoAnalysis') -> List[str]:
        instructions = []
        
        instructions.append("Clone the repository:")
        instructions.append(f"```bash\ngit clone <repository-url>\ncd {analysis.name}\n```")
        
        if 'Python' in analysis.languages:
            instructions.append("Set up Python environment:")
            instructions.append("```bash\npython -m venv venv\nsource venv/bin/activate  # On Windows: venv\\Scripts\\activate\n```")
            
            if analysis.has_requirements:
                instructions.append("Install Python dependencies:")
                instructions.append("```bash\npip install -r requirements.txt\n```")
            elif analysis.has_setup_py:
                instructions.append("Install the package:")
                instructions.append("```bash\npip install -e .\n```")
        
        if 'JavaScript' in analysis.languages or analysis.has_package_json:
            instructions.append("Install Node.js dependencies:")
            instructions.append("```bash\nnpm install\n# or\nyarn install\n```")
        
        if analysis.has_docker:
            instructions.append("Docker setup:")
            instructions.append("```bash\ndocker build -t app .\ndocker run -p 3000:3000 app\n```")
        
        if 'Django' in analysis.framework:
            instructions.append("Run Django migrations:")
            instructions.append("```bash\npython manage.py migrate\npython manage.py runserver\n```")
        elif 'Flask' in analysis.framework:
            instructions.append("Run Flask application:")
            instructions.append("```bash\nflask run\n# or\npython app.py\n```")
        elif 'Streamlit' in analysis.framework:
            instructions.append("Run Streamlit application:")
            instructions.append("```bash\nstreamlit run app.py\n```")
        elif 'React' in analysis.framework or 'Next.js' in analysis.framework:
            instructions.append("Start development server:")
            instructions.append("```bash\nnpm start\n# or\nnpm run dev\n```")
        
        return instructions
    
    def build_file_structure(self, owner: str, repo: str, path: str = "", max_depth: int = 3, current_depth: int = 0) -> Dict[str, Any]:
        if current_depth >= max_depth:
            return {}
        
        structure = {}
        contents = self.get_repo_contents(owner, repo, path)
        
        for item in contents:
            name = item['name']
            if item['type'] == 'dir' and not name.startswith('.') and name not in ['node_modules', '__pycache__', 'venv']:
                structure[name] = self.build_file_structure(owner, repo, item['path'], max_depth, current_depth + 1)
            elif item['type'] == 'file':
                structure[name] = {'type': 'file', 'size': item.get('size', 0)}
        
        return structure
    
    def analyze_repository(self, github_url: str) -> RepoAnalysis:
        try:
            owner, repo_name = self.parse_github_url(github_url)
            repo_info = self.get_repo_info(owner, repo_name)
            languages = self.get_languages(owner, repo_name)
            primary_language = repo_info.get('language', 'Unknown')
            
            root_contents = self.get_repo_contents(owner, repo_name)
            file_names = [item['name'] for item in root_contents if item['type'] == 'file']
            
            has_docker = any(f in file_names for f in ['Dockerfile', 'docker-compose.yml', 'docker-compose.yaml'])
            has_requirements = 'requirements.txt' in file_names
            has_package_json = 'package.json' in file_names
            has_setup_py = 'setup.py' in file_names
            has_makefile = any(f in file_names for f in ['Makefile', 'makefile'])
            has_tests = any('test' in f.lower() for f in file_names) or \
                       any(item['name'] in ['tests', 'test'] for item in root_contents if item['type'] == 'dir')
            
            important_files = ['package.json', 'requirements.txt', 'pom.xml', 'setup.py']
            file_contents = {}
            
            for file_name in important_files:
                if file_name in file_names:
                    content = self.get_file_content(owner, repo_name, file_name)
                    if content:
                        file_contents[file_name] = content
            
            framework = self.detect_framework(file_names, file_contents)
            dependencies = self.extract_dependencies(file_contents)
            file_structure = self.build_file_structure(owner, repo_name)
            
            analysis = RepoAnalysis(
                name=repo_info['name'],
                description=repo_info.get('description', 'No description available'),
                language=primary_language,
                languages=languages,
                framework=framework,
                has_docker=has_docker,
                has_requirements=has_requirements,
                has_package_json=has_package_json,
                has_setup_py=has_setup_py,
                has_makefile=has_makefile,
                has_tests=has_tests,
                license=repo_info.get('license', {}).get('name') if repo_info.get('license') else None,
                topics=repo_info.get('topics', []),
                setup_instructions=[],
                dependencies=dependencies,
                file_structure=file_structure
            )
            
            analysis.setup_instructions = self.generate_setup_instructions(analysis)
            
            return analysis
            
        except Exception as e:
            raise Exception(f"Error analyzing repository: {str(e)}")

def main():
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    
    if not GITHUB_TOKEN:
        GITHUB_TOKEN = input("GitHub Token: ").strip()
    
    if not GITHUB_TOKEN:
        return
    
    analyzer = GitHubRepoAnalyzer(GITHUB_TOKEN)
    
    if not analyzer.test_token():
        return
    
    repo_url = input("Enter GitHub repository URL: ").strip()
    if not repo_url:
        repo_url = "https://github.com/streamlit/streamlit"
    
    try:
        analysis = analyzer.analyze_repository(repo_url)
        
        if analysis.file_structure:
            with open('file_structure.json', 'w') as f:
                json.dump(analysis.file_structure, f, indent=2)
        
    except Exception:
        pass

if __name__ == "__main__":
    main()
