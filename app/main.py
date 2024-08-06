import requests
import logging

from fastapi import FastAPI, status, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from app.frame_utils import background_upload

app = FastAPI()

# APIS

@app.get('/')
async def root():
    return JSONResponse(content={"data": "Server is running!"}, status_code=200)

@app.get('/upload/{project_id}')
async def get_project_structure(project_id: str, background_tasks : BackgroundTasks):
    try:
        background_tasks.add_task(background_upload, project_id)
        return JSONResponse(content={"message": "Folder structure creation is started."}, status_code=200)
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
 