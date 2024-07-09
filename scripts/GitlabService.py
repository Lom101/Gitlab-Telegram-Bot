import requests

def get_gitlab_projects_info(GITLAB_TOKEN: str):
    response = requests.get(f"https://gitlab.infra.tatneftm.ru/api/v4/projects?private_token={GITLAB_TOKEN}")
    # Отладочная информация
    print(f"HTTP Status Code: {response.status_code}")
    print(f"Response Content: {response.text}")
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
        return None
    try:
        return response.json()
    except requests.exceptions.JSONDecodeError as err:
        print(f"JSON decode error: {err}")
        return None

def get_gitlab_merges_info(url: str, GITLAB_TOKEN: str):
    try:
        response = requests.get(f"{url}?private_token={GITLAB_TOKEN}")
        print(f"HTTP Status Code: {response.status_code}")
        print(f"Response Content: {response.text}")
        response.raise_for_status()
        merges = response.json()
        return merges
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None
    except ValueError as ve:
        print(f"Invalid JSON response: {ve}")
        return None