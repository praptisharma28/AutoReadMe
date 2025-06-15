import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
    GITHUB_API_BASE_URL = 'https://api.github.com'
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    MAX_FILE_SIZE = 1024 * 1024  # 1MB
    MAX_ANALYSIS_DEPTH = 3
    SUPPORTED_LANGUAGES = [
        'Python', 'JavaScript', 'TypeScript', 'Java', 'C++', 'C#', 
        'Go', 'Rust', 'PHP', 'Ruby', 'Swift', 'Kotlin', 'Shell',
        'HTML', 'CSS', 'Markdown', 'YAML', 'JSON', 'XML'
    ]
    DEFAULT_SECTIONS = [
        'title', 'description', 'installation', 'usage', 
        'features', 'contributing', 'license', 'authors',
        'acknowledgements', 'changelog', 'support', 'faq'
    ]
