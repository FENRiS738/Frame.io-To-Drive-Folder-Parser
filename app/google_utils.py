import requests
import os
import re

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from app.connections import google_cloud_connect


# UTILITIES

def get_source_file_path(source_file_name, source_file_url):

    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
    downloads_dir = os.path.join(base_dir, 'downloads')
    os.makedirs(downloads_dir, exist_ok=True)

    invalid_chars = r'[/\\:*?"<>|]'
    source_file_name = re.sub(invalid_chars, '_', source_file_name)

    file_path = os.path.join(downloads_dir, source_file_name)

    # Download the file
    data = requests.get(source_file_url, stream=True)
    data.raise_for_status()

    with open(file_path, 'wb') as file:
        for chunk in data.iter_content(chunk_size=10*1024):
            file.write(chunk)
    
    return file_path
            

def create_folder(source_folder_name, parent_id = None):
    
    creds = google_cloud_connect()

    try:
        # create drive api client
        service = build("drive", "v3", credentials=creds)

        folder_metadata = {
            "name": source_folder_name,
            "mimeType": "application/vnd.google-apps.folder",
        }

        if parent_id:
            folder_metadata["parents"] = [parent_id]

        folder = service.files().create(body=folder_metadata, fields="id").execute()
        print(f'Folder ID: "{folder["id"]}".')
        return folder["id"]

    except HttpError as error:
        print(f"An error occurred: {error}")
        return(f"An error occurred: {error}")


def upload_with_conversion(source_file_name, source_file_url, source_file_type, parent_id):

    creds = google_cloud_connect()

    try:
        # create drive api clientsource_file_type
        service = build("drive", "v3", credentials=creds)

        file_metadata = {
            "name": source_file_name,
            "parents": [parent_id]
        }

        source_file_path = get_source_file_path(source_file_name, source_file_url)

        media : MediaFileUpload = MediaFileUpload(source_file_path, mimetype=source_file_type, resumable=True)

        file = (
            service.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )
        print(f'File with ID: "{file["id"]}" has been uploaded.')
        return file["id"], source_file_path

    except HttpError as error:
        print(f"An error occurred: {error}")
        file = None
        return(f"An error occurred: {error}")


def create_structure(data, parent_id= None):
    if isinstance(data, dict):
        if data['_type'] == 'folder':
            folder_id = create_folder(data['file_name'], parent_id)
            for child in data.get('children', []):
                create_structure(child, folder_id)
        
        if data['_type'] == 'file':
            file, local_file_path = upload_with_conversion(data['file_name'], data['file_url'], data['file_type'], parent_id)
            os.remove(local_file_path)

        if data['_type'] == 'version_stack':
            latest_version = data['children'][1]
            file, local_file_path = upload_with_conversion(latest_version['file_name'], latest_version['file_url'], latest_version['file_type'], parent_id)
            os.remove(local_file_path)
        
    elif isinstance(data, list):
        for item in data:
            create_structure(item, parent_id)


# UNIT TESTING

if __name__ == "__main__":
    source_file_name = "From sweet to sour_0.30_9:16_V2.mp4"
    source_file_url = "https://assets.frame.io/uploads/e22fa659-d42a-4bf8-a84d-e0c15b013ee6/original.mp4?response-content-disposition=attachment%3B+filename%3D%22From+sweet+to+sour_0.30_9%3A16_V2.mp4%22%3B+filename%2A%3D%22From+sweet+to+sour_0.30_9%3A16_V2.mp4%22&x-amz-meta-request_id=F-gr2GOPPfwq4vIK0_SB&x-amz-meta-project_id=5e7d4b51-7a19-47fb-9a7d-aaab15d6ed72&x-amz-meta-resource_type=asset&x-amz-meta-resource_id=001c6c1c-334d-4084-893c-43f290678be4&Expires=1722729600&Signature=FRlH3vbAR3s1W8CdKOf7Zhl4miEt3yash36fPKcQoGL9FVSjUuDMnopAbStT0u1xamr3655AFK7HDfn8kHPHj3XBTzAUHOqmGt-V4vhsO0fW2aDsglq84b0r7pQG~XKWr6UCYAJb9syq5-mQmNk1-5iwPl7xeGiusuc7ZtcIIHvnHrz-WCreCd0q5~mW5E8qinOueBJU2uTdlSNL8yULh0xxJ01jlLVlIirhydJXTOrcaNaTXqfiwT6mUB4Z6ew4dH1Pm3J8~y-aohLAjDlsGYXa1rMBg814O0-JHP4y9E-uj~JAlBDkisE8RJZYrp0dVjdjIAdSU5IiItVs4ScAhA__&Key-Pair-Id=K1XW5DOJMY1ET9"
    source_file_type = "video/mp4"
    upload_with_conversion(source_file_name, source_file_url, source_file_type)
    # create_folder()
    # get_source_file_path(source_file_name, source_file_url)