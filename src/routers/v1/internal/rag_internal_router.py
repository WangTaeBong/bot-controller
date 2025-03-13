"""
Module for handling document callback endpoints with enhanced logging.

This module defines two FastAPI endpoints for processing document extraction and indexing callbacks.
Each endpoint logs the API invocation along with session identification and rag_sys_info.
In addition to info-level messages that mark the start/end of processing,
debug-level messages provide detailed request information.
In case of errors, exceptions are logged with full traceback.
"""

import logging
import traceback

from fastapi import APIRouter

from src.common.config_loader import ConfigLoader
from src.common.error_cd import ErrorCd
from src.models.external.callback_dispatcher import CallbackResponse, CallbackRequest
from src.models.internal.extract_callback import ExtractCallbackRequest, ExtractCallbackResponse
from src.models.internal.indexing_callback import IndexingCallbackRequest, IndexingCallbackResponse
from src.process import data_handler

# Configure module-level logger.
logger = logging.getLogger(__name__)

# Load configuration settings.
config_loader = ConfigLoader()
settings = config_loader.get_settings()

# Set up FastAPI router with prefix '/v1'
v1_internal_router = APIRouter(prefix='/v1')


def create_error_response(error_type: ErrorCd) -> dict:
    """
    Create a standardized error response dictionary.

    Args:
        error_type (str): An error code constant defined in ErrorCd.

    Returns:
        dict: A dictionary containing 'result_cd' and 'result_desc'.
    """
    return {
        "result_cd": ErrorCd.get_code(error_type),
        "result_desc": ErrorCd.get_description(error_type)
    }


def get_session_id(request) -> str:
    """
    Extract the session ID from the request's meta if available.

    Args:
        request: The incoming request which may include a meta attribute.

    Returns:
        str: The session ID if present, else "N/A".
    """
    try:
        return request.meta.session_id  # Assumes meta contains a session_id field.
    except AttributeError:
        return "N/A"


@v1_internal_router.post(
    path="/extract-callback",
    include_in_schema=False,
    response_model=ExtractCallbackResponse
)
async def doc_extract_callback(request: ExtractCallbackRequest) -> ExtractCallbackResponse:
    """
    Process a document extraction callback.

    This endpoint receives a callback request for document extraction. It performs the following steps:
      1. Logs the incoming request (with a length limit for readability).
      2. Validates the extraction result code:
         - If not successful, logs an error, triggers a failure callback, and returns a response.
      3. Checks if any page info contains context data.
      4. Depending on the 'modify_flag' in meta:
         - If set, triggers a callback for extraction.
         - Otherwise, attempts document indexing; if indexing fails, triggers an alternate extraction callback.
      5. Returns a standardized success response with the document UID.

    Args:
        request (ExtractCallbackRequest): The incoming extraction callback request data.

    Returns:
        ExtractCallbackResponse: The response with standardized result code, description, and document UID.

    Raises:
        Exception: Any exception is caught, logged (with traceback), and a common error response is returned.
    """
    session_id = get_session_id(request)
    logger.info(f"API [extract-callback] invoked. Session: {session_id}. doc_uid: {request.result.doc_uid}")

    try:
        # Detailed debug log for incoming request (trimmed for brevity)
        logger.debug(f"[extract-callback] Request: {request.model_dump_json()[:300]} ...")

        # Check if the extraction result indicates failure.
        if request.result_cd != ErrorCd.get_code(ErrorCd.SUCCESS):
            logger.error(f"[extract-callback] Extraction failed: [{request.result_cd}] {request.result_desc}")
            await data_handler.send_was_callback_extract_fail(request, request.result.step_cd)
            response = ExtractCallbackResponse(
                **create_error_response(ErrorCd.SUCCESS),
                doc_uid=request.result.doc_uid
            )
            logger.info(f"[extract-callback] Finished processing (failure branch). Session: {session_id}")
            return response

        # Check for presence of context data in page_info.
        context_exists = any(result.context for result in (request.result.page_info or []))
        if not context_exists:
            logger.debug("[extract-callback] No context found in page_info. (Processing may be skipped.)")

        # Process based on the modification flag.
        if request.meta.modify_flag:
            logger.info("[extract-callback] modify_flag is set; triggering extraction callback.")
            await data_handler.send_was_callback_extract(request, 1)
        else:
            logger.info("[extract-callback] modify_flag not set; initiating indexing process.")
            indexing_response = await data_handler.request_indexing(request)
            if indexing_response.result_cd != ErrorCd.get_code(ErrorCd.SUCCESS):
                logger.error("[extract-callback] Indexing failed; triggering alternate extraction callback.")
                await data_handler.send_was_callback_extract(request, 2, indexing_response)

        response = ExtractCallbackResponse(
            **create_error_response(ErrorCd.SUCCESS),
            doc_uid=request.result.doc_uid
        )
        logger.info(
            f"[extract-callback] Completed successfully. Session: {session_id}, doc_uid: {request.result.doc_uid}")
        return response

    except Exception as e:
        logger.error(f"[extract-callback] Exception: {e}\n{traceback.format_exc()}")
        return ExtractCallbackResponse(
            **create_error_response(ErrorCd.COMMON_EXCEPTION),
            doc_uid=request.result.doc_uid
        )


@v1_internal_router.post(
    path="/indexing-callback",
    include_in_schema=False,
    response_model=IndexingCallbackResponse
)
async def doc_indexing_callback(request: IndexingCallbackRequest) -> IndexingCallbackResponse:
    """
    Process a document indexing callback with enhanced logging.

    Logs include:
      - API name ("indexing-callback")
      - Session ID extracted from request.meta (if available)
      - rag_sys_info from the configuration
      - Detailed request dump at debug level (limited in length)
      - Error details with full traceback on exception
      - Callback success status

    Args:
        request (IndexingCallbackRequest): The incoming indexing callback request data.

    Returns:
        IndexingCallbackResponse: The standardized response including result code, description, and document UID.
    """
    session_id = get_session_id(request)
    logger.info(f"API [indexing-callback] invoked. Session: {session_id}. doc_uid: {request.result.doc_uid}")

    is_callback_success = False
    try:
        # Log incoming request details at debug level.
        logger.debug(f"[indexing-callback] Request: {request.model_dump_json()[:300]} ...")

        # Attempt to process indexing callback and capture success status.
        is_callback_success = await data_handler.send_was_callback_indexing(request, 2, True)

        response = IndexingCallbackResponse(
            **create_error_response(ErrorCd.SUCCESS),
            doc_uid=request.result.doc_uid
        )
        logger.info(
            f"[indexing-callback] Completed successfully. Session: {session_id}, doc_uid: {request.result.doc_uid}")
        return response

    except Exception as err:
        logger.error(f"[indexing-callback] Exception: {err}\n{traceback.format_exc()}")
        # If the callback process was not successful, trigger a failure callback.
        if not is_callback_success:
            await data_handler.send_was_callback_indexing(request, 2, False)
        response = IndexingCallbackResponse(
            **create_error_response(ErrorCd.INDEXING_CALLBACK_EXCEPT),
            doc_uid=request.result.doc_uid
        )
        logger.info(
            f"[indexing-callback] Completed with error. Session: {session_id}, doc_uid: {request.result.doc_uid}")
        return response


@v1_internal_router.post(
    path="/dummy-callback",
    include_in_schema=False,
    response_model=CallbackResponse
)
async def dummy_callback(request: CallbackRequest) -> CallbackResponse:
    """
    테스트용 dummy callback 엔드포인트.

    이 엔드포인트는 CallbackRequest 모델의 요청 데이터를 받아 로그에 기록하고,
    정상 처리 여부를 확인한 후 CallbackResponse 모델 형식의 성공 응답을 반환합니다.

    Args:
        request (CallbackRequest): 테스트용 요청 데이터.

    Returns:
        CallbackResponse: 표준 성공 응답 (result_cd, result_desc)와 요청에 포함된 doc_uid.
    """
    # 요청의 meta에서 session_id 추출
    session_id = get_session_id(request)
    logger.info(f"API [dummy-callback] invoked. Session: {session_id}, doc_uid: {request.result.doc_uid}")

    # 요청 데이터의 일부를 디버그 로그에 기록 (최대 300자)
    logger.debug(f"[dummy-callback] Request data: {request.model_dump_json()}")

    # 성공 응답 생성 (여기서는 result_cd 200, result_desc "Success"로 고정)
    response = CallbackResponse(
        result_cd=200,
        result_desc="Success",
        doc_uid=request.result.doc_uid
    )

    logger.info(f"[dummy-callback] Completed successfully. Session: {session_id}")
    return response

