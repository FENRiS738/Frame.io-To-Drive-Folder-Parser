import os
import uuid
import json
import requests
import time

from fastapi import HTTPException, status
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry 
from dotenv import load_dotenv

from app.google_utils import create_folder, create_structure

load_dotenv()


FRAME_BASE_URL = "https://api.frame.io/v2"
FRAME_TOKEN = os.getenv('FRAME_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
session.mount('https://', HTTPAdapter(max_retries=retries))

# UTILITIES

def get_api_response(url, headers, params=None):
    try:
        response = session.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            print(f"Rate limit exceeded. Retrying after {retry_after} seconds.")
            time.sleep(retry_after)
            return get_api_response(url, headers, params)
        else:
            raise HTTPException(status_code=response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

def get_root_asset_id(project_id):
    url = FRAME_BASE_URL + "/projects/" + project_id
    query = {
    "include": "string",
    }
    headers = {"Authorization": f"Bearer {FRAME_TOKEN}"}
    result = requests.get(url, headers=headers, params=query)
    result.raise_for_status()
    response : dict = result.json()
    
    project = {
        "project_name" : response.get('name'),
        "project_id": response.get('id'),
        "root_asset_id": response.get('root_asset_id'),
        "type" : response.get('_type')
    }
    return project


def get_asset_children(asset_id):
    url = FRAME_BASE_URL + "/assets/" + asset_id + "/children"
    query = {
    "include_deleted": "false",
    "include": "children",
    }
    headers = {"Authorization": f"Bearer {FRAME_TOKEN}"}
    
    responses = get_api_response(url=url, headers=headers, params=query)

    children = []
    for response in responses:
        data = {
            "asset_id" : response.get('id'),
            "file_name" : response.get('name'),
            "file_type" : response.get('filetype'),
            "file_url" : response.get('original'),
            "_type" : response.get('_type'),
            "children" : get_asset_children(response.get('id'))
        }

        children.append(data)

    return children

def background_upload(project_id):
    try:
        project = get_root_asset_id(project_id)
        project['children'] = get_asset_children(project.get('root_asset_id'))

        current_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
        data_dir = os.path.join(base_dir, 'data')
        os.makedirs(data_dir, exist_ok=True)

        filename = str(uuid.uuid4())
        destination_path = os.path.join(data_dir, f"{filename}.json")

        with open(destination_path, 'w') as output:
            output.write(json.dumps(project))

        root_folder_id = create_folder(project.get('project_name'))
        create_structure(project.get('children'), root_folder_id)

        os.remove(destination_path)
        response = {
            "project_id": project_id,
            "project_name" : project.get('project_name'),
            "message": f"Your project: {project.get('name')} uploaded successfully to drive", 
            }

        notify_webhook(response)
    except Exception as ex:
        notify_webhook({"Error": str(ex)})

def notify_webhook(response):
    try:
        result = requests.post(WEBHOOK_URL, json=response)
        result.raise_for_status()
    except requests.exceptions.RequestException as ex:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(ex)
        )   
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(ex)
        )

# UNIT TESTING

if __name__ == "__main__":
    project_id = "be956f7a-0bb1-44ff-a0b6-2b4b988c4f85"
    project = get_root_asset_id(project_id)
    project['children'] = get_asset_children(project.get('root_asset_id'))

    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
    data_dir = os.path.join(base_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)

    filename = str(uuid.uuid4())
    destination_path = os.path.join(data_dir, f"{filename}.json")

    with open(destination_path, 'w') as output:
        output.write(json.dumps(project))

    print(f"File location: {destination_path}")