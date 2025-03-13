import logging
from typing import List

from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

upload = APIRouter(prefix='/upload', responses={404: {"description": "Not found"}})
templates = Jinja2Templates(directory="templates")


@upload.get(path='/', tags=['upload'], response_class=HTMLResponse)
async def upload_page(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})


@upload.post(path="/doc_upload", tags=['upload'])
def doc_upload(files: List[UploadFile] = File(...)):
    for file in files:
        try:
            contents = file.file.read()
            doc_path = "doc-files/" + file.filename
            with open(doc_path, 'wb') as f:
                f.write(contents)
        except Exception as e:
            logging.error(e)
            return {"message": "There was an error uploading the file(s)"}
        finally:
            file.file.close()

    return {"message": "Successfully uploaded"}
