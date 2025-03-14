import asyncio
import logging
from functools import wraps

from fastapi import APIRouter, BackgroundTasks
from starlette.responses import StreamingResponse

from src.common.config_loader import ConfigLoader
from src.common.error_cd import ErrorCd
from src.common.restclient import rc  # Global RestClient instance
from src.models.common.models import DocumentRegisterResponseMeta
from src.models.external.chat_llm import ChatRequest, ChatResponse
from src.models.external.delete_documents import DeleteDocRequest, DeleteDocResponse
from src.models.external.modify_document import ModifyDocRequest, ModifyDocResponse
from src.models.external.registry_documents import RegisterDocRequest, RegisterDocResponse
from src.models.external.search_documents import SearchDocRequest, SearchDocResponse
from src.process import data_handler

# ================================
#         Logging Configuration
# ================================
logger = logging.getLogger(__name__)

# Load settings
config_loader = ConfigLoader()
settings = config_loader.get_settings()

# FastAPI router setup
v1_external_router = APIRouter(prefix='/v1')


# ================================
#         Helper Functions
# ================================

def handle_exceptions(endpoint_func):
    """
    Decorator to handle exceptions in API endpoints.

    - Catches all exceptions in the decorated API function.
    - Logs error details and returns a standardized error response.

    Args:
        endpoint_func (Callable): The API function to be wrapped.

    Returns:
        Callable: The wrapped function with exception handling.
    """

    @wraps(endpoint_func)
    async def wrapper(*args, **kwargs):
        try:
            return await endpoint_func(*args, **kwargs)
        except Exception as e:
            logger.error(f"[ERROR] {endpoint_func.__name__} | Exception: {e}")
            return ErrorCd.get_error(ErrorCd.COMMON_EXCEPTION)

    return wrapper


def safe_log_request(api_name, request, max_length=300):
    """
    Logs API requests safely by truncating long request bodies.

    - Logs API name, RAG system info, and session ID.
    - Truncates long request bodies to avoid excessive logging.

    Args:
        api_name (str): The name of the API being logged.
        request (BaseModel): The incoming request object.
        max_length (int, optional): Maximum log length. Defaults to 300.
    """
    rag_info = request.meta.rag_sys_info if hasattr(request.meta, 'rag_sys_info') else "N/A"
    session_id = request.meta.session_id if hasattr(request.meta, 'session_id') else "N/A"
    request_data = request.model_dump_json()
    truncated_request = request_data[:max_length] + " ..." if len(request_data) > max_length else request_data

    logger.info(f"[API: {api_name}] [RAG: {rag_info}] [Session ID: {session_id}] invoked")
    logger.debug(f"[API: {api_name}] [RAG: {rag_info}] [Session ID: {session_id}] Request Data: {truncated_request}")


async def send_extract_requests(request, extract_requests, response_meta):
    """
    Sends multiple extract requests asynchronously and logs failures.

    - Uses `asyncio.gather()` for parallel execution.
    - Logs failed extract requests for debugging.

    Args:
        request (RegisterDocRequest): The document registration request.
        extract_requests (list): List of extract requests.
        response_meta (DocumentRegisterResponseMeta): The response meta.

    Returns:
        RegisterDocResponse: The response after processing extract requests.
    """
    extract_responses = await asyncio.gather(
        *[rc.restapi_post_async(settings.api_interface.extract_request_url, req.model_dump()) for req in
          extract_requests],
        return_exceptions=True
    )

    for extract_request, extract_response in zip(extract_requests, extract_responses):
        if isinstance(extract_response, Exception):
            logger.error(
                f"[RAG: {request.meta.rag_sys_info}] [Session ID: {request.meta.session_id}] "
                f"Extract request failed: {extract_request} - {extract_response}"
            )
            await data_handler.send_was_callback_extract_post_fail(extract_request, None, 1)
        elif extract_response.get("result_cd") != 200:
            logger.error(
                f"[RAG: {request.meta.rag_sys_info}] [Session ID: {request.meta.session_id}] "
                f"Extract error: {extract_request} - {extract_response['result_desc']}"
            )
            await data_handler.send_was_callback_extract_post_fail(extract_request, extract_response, 1)

    return RegisterDocResponse(
        meta=response_meta,
        result_cd=ErrorCd.get_code(ErrorCd.SUCCESS),
        result_desc=ErrorCd.get_description(ErrorCd.SUCCESS))


# ================================
#         API Endpoints
# ================================

@v1_external_router.post("/doc-register", response_model=RegisterDocResponse)
@handle_exceptions
async def register_doc_req(request: RegisterDocRequest):
    """
    Handles document registration requests.

    - Validates input data.
    - Sends extract requests asynchronously.
    """
    safe_log_request("doc-register", request)

    register_response_meta = DocumentRegisterResponseMeta(
        **{
            "company_id": request.meta.company_id,
            "dept_class": request.meta.dept_class,
            "session_id": request.meta.session_id
        }
    )

    if not request.documents.files:
        logger.error(
            f"[RAG: {request.meta.rag_sys_info}] [Session ID: {request.meta.session_id}] "
            f"Document registration failed: No file info"
        )
        return RegisterDocResponse(
            meta=register_response_meta,
            result_cd=ErrorCd.get_code(ErrorCd.NO_FILE_INFO),
            result_desc=ErrorCd.get_description(ErrorCd.NO_FILE_INFO)
        )

    if not request.meta.callback_url:
        logger.error(
            f"[RAG: {request.meta.rag_sys_info}] [Session ID: {request.meta.session_id}] "
            f"Document registration failed: No callback URL"
        )
        return RegisterDocResponse(
            meta=register_response_meta,
            result_cd=ErrorCd.get_code(ErrorCd.NO_CALLBACK_URL),
            result_desc=ErrorCd.get_description(ErrorCd.NO_CALLBACK_URL)
        )

    is_was_url = request.documents.file_get_type.lower() == "url"

    for doc in request.documents.files:
        if is_was_url and not doc.file_url:
            logger.error(
                f"[RAG: {request.meta.rag_sys_info}] [Session ID: {request.meta.session_id}] "
                f"Document registration failed: Missing file URL"
            )
            return RegisterDocResponse(
                meta=register_response_meta,
                result_cd=ErrorCd.get_code(ErrorCd.NO_FILE_INFO),
                result_desc=ErrorCd.get_description(ErrorCd.NO_FILE_INFO)
            )

    extract_requests = [data_handler.set_extract_doc_request(request, doc) for doc in request.documents.files]
    return await send_extract_requests(request, extract_requests, register_response_meta)


@v1_external_router.post("/doc-modify", response_model=ModifyDocResponse)
@handle_exceptions
async def modify_doc_req(request: ModifyDocRequest):
    """Handles document modification requests."""
    safe_log_request("doc-modify", request)
    return await data_handler.doc_modify(request)


@v1_external_router.post("/doc-delete", response_model=DeleteDocResponse)
@handle_exceptions
async def delete_doc_req(request: DeleteDocRequest):
    """Handles document deletion requests."""
    safe_log_request("doc-delete", request)
    return await data_handler.doc_delete(request)


@v1_external_router.post("/search-doc", response_model=SearchDocResponse)
@handle_exceptions
async def search_doc_req(request: SearchDocRequest):
    """Handles document search requests."""
    safe_log_request("search-doc", request)
    return await data_handler.doc_search(request)


@v1_external_router.post("/chat", response_model=ChatResponse)
@handle_exceptions
async def chat_req(request: ChatRequest):
    """Processes chat requests and retrieves responses."""
    safe_log_request("chat", request)
    return await data_handler.process_chat(request)


@v1_external_router.post("/chat/stream", response_class=StreamingResponse)
@handle_exceptions
async def chat_stream_req(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    Processes streaming chat requests and returns responses as Server-Sent Events (SSE).

    This endpoint handles streaming chat responses which are sent incrementally
    to the client as they are generated by the LLM.

    Args:
        request (ChatRequest): The chat request containing user query and metadata
        background_tasks (BackgroundTasks): FastAPI background tasks manager for async operations

    Returns:
        StreamingResponse: An SSE streaming response that incrementally sends generated text
    """
    safe_log_request("/chat/stream", request)

    try:
        # Call the process_chat_stream method
        streaming_response = await data_handler.process_chat_stream(request, background_tasks)

        # Make sure the response has the proper headers for SSE
        if isinstance(streaming_response, StreamingResponse):
            streaming_response.headers["Content-Type"] = "text/event-stream; charset=utf-8"
            streaming_response.headers["Cache-Control"] = "no-cache"
            streaming_response.headers["Connection"] = "keep-alive"

        return streaming_response

    except Exception as e:
        logger.error(f"[{request.meta.session_id}] Error processing streaming request: {str(e)}", exc_info=True)

        async def error_stream():
            error_msg = {"error": True, "text": f"Error processing streaming request: {str(e)}", "finished": True}
            yield f"data: {json.dumps(error_msg, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            error_stream(),
            media_type="text/event-stream; charset=utf-8"
        )
