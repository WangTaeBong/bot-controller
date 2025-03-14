from pathlib import Path
from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates

maichat_test_router = APIRouter()
templates = Jinja2Templates(directory="templates")


@maichat_test_router.get("/maichat_test_ui", include_in_schema=False, response_class=HTMLResponse)
async def maichat_test_page(request: Request):
    return templates.TemplateResponse("maichat_test_ui.html", {"request": request})


@maichat_test_router.get("/maichat_stream_test_ui", include_in_schema=False, response_class=HTMLResponse)
async def maichat_test_page(request: Request):
    return templates.TemplateResponse("chat_stream.html", {"request": request})


# 파일 업로드 엔드포인트
documents_dir = Path("uploaded_documents").resolve()
documents_dir.mkdir(parents=True, exist_ok=True)


@maichat_test_router.post("/upload_document", include_in_schema=False)
async def upload_document(file: UploadFile = File(...)):
    file_path = documents_dir / file.filename
    with open(file_path, "wb") as f:
        f.write(file.file.read())

    return JSONResponse(content={"message": "파일 업로드 성공", "download_url": f"/download_document/{file.filename}"})


# 파일 다운로드 엔드포인트
@maichat_test_router.get("/download_document/{file_name}", include_in_schema=False)
async def download_document(file_name: str):
    file_path = documents_dir / file_name
    if not file_path.exists():
        return JSONResponse(content={"message": "파일을 찾을 수 없습니다."}, status_code=404)
    return FileResponse(file_path, filename=file_name)
