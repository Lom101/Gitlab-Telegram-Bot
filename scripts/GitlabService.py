import requests
import logging

# Настройка логгирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


class GitlabService:
    def __init__(self, base_url: str, gitlab_token: str):
        self.base_url = base_url
        self.gitlab_token = gitlab_token

    def get_gitlab_projects_info(self):
        url = f"{self.base_url}/api/v4/projects?access_token={self.gitlab_token}"
        logging.info("Fetching GitLab projects information...")
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as err:
            logging.error(f"HTTP error occurred: {err}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {e}")
        except ValueError as ve:
            logging.error(f"Invalid JSON response: {ve}")
        return None

    def get_gitlab_merges_info(self, url: str):
        logging.info("Fetching GitLab merge requests information...")
        try:
            response = requests.get(f"{url}?access_token={self.gitlab_token}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as err:
            logging.error(f"HTTP error occurred: {err}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {e}")
        except ValueError as ve:
            logging.error(f"Invalid JSON response: {ve}")
        return None
