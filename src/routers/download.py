import logging
from urllib.parse import quote

from fastapi import APIRouter
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates

download = APIRouter(prefix='/download', responses={404: {"description": "Not found"}})
templates = Jinja2Templates(directory="templates")


@download.get("/doc-files/{filename}")
async def download_test_bytes(filename):
    logging.info("Downloading test")
    download_fname = './doc-files/' + filename
    with open(download_fname, "rb") as f:
        file_content = f.read()

    file_name = quote(filename)
    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{file_name}",
    }
    # return StreamingResponse(io.BytesIO(file_content), headers=headers, media_type="application/octet-stream")
    return FileResponse(path=download_fname, filename=file_name, headers=headers, media_type='application/octet-stream')
