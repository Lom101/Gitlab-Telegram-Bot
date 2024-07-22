import requests
import logging

# Настройка логгирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


class GitlabService:
    def __init__(self, base_url: str, gitlab_token: str):
        self.base_url = base_url
        self.gitlab_token = gitlab_token

    def get_gitlab_merges_info(self):
        logging.info("Fetching GitLab merge requests information...")
        params = {
            'scope': 'all',
            'state': 'opened',
            'access_token': self.gitlab_token
        }

        try:
            url = f"{self.base_url}/api/v4//merge_requests"
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {e}")

        return None
