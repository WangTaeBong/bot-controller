import logging
from typing import Optional, List, Dict, Any

import aiohttp
import json
from fastapi import BackgroundTasks
from starlette.responses import StreamingResponse

from src.common.config_loader import ConfigLoader
from src.common.error_cd import ErrorCd
from src.common.restclient import rc
from src.models.common.models import PageInfo, Result, Payload, IndexingRequestMeta
from src.models.external.callback_dispatcher import CallbackRequest, CallbackResponse, CallbackRequestMeta
from src.models.external.chat_llm import ChatRequest, ChatRequestData, DocChatCommonMeta
from src.models.external.delete_documents import (
    DeleteDocResponse,
    DocDelDocuments,
    DeleteDocRequest,
    DocDelResDocuments
)
from src.models.external.modify_document import ModifyDocRequest, ModifyDocResponse, ModifyDocResponseMeta
from src.models.external.registry_documents import RegisterDocRequest
from src.models.external.search_documents import SearchDocRequest, SearchDocResponse, SearchDocResult, SearchRes
from src.models.internal.chat_llm import ChatLLMResponse, ChatLLMRequest, ChatLLMReq, ChatLLMRes
from src.models.internal.chat_retriever import ChatRetrieverResponse
from src.models.internal.extract_callback import ExtractCallbackRequest
from src.models.internal.extract_document import (
    ExtractDocRequest,
    Documents as ExtractDocuments,
    FileGetInfo as ExtractFileInfo,
    Files as ExtractFiles,
    ExtractDocRequestMeta
)
from src.models.internal.indexing_callback import IndexingCallbackRequest
from src.models.internal.indexing_document import (
    IndexingRequest,
    IndexingResponse,
    Data as IndexingData,
    Document as IndexingDocument,
    Document,
    Data
)

logger = logging.getLogger(__name__)

# Load configuration settings
config_loader = ConfigLoader()
settings = config_loader.get_settings()


def create_error_response(error_type: Any) -> Dict[str, Any]:
    """
    Create a standard error response dictionary based on the given error type.

    Args:
        error_type: An error code or error type identifier.

    Returns:
        dict: A dictionary containing 'result_cd' and 'result_desc'.
    """
    return {
        "result_cd": ErrorCd.get_code(error_type),
        "result_desc": ErrorCd.get_description(error_type)
    }


def _convert_page_info(pages: Optional[List]) -> List[PageInfo]:
    """
    Convert a list of page data into a list of PageInfo objects.

    Args:
        pages (Optional[List]): A list of page information objects,
        each containing attributes such as page_num and context.

    Returns:
        List[PageInfo]: A list of PageInfo objects.
    """
    return [PageInfo(page_num=p.page_num, context=p.context or "") for p in pages] if pages else []


def _build_callback_meta(source_meta: Any) -> CallbackRequestMeta:
    """
    Build a CallbackRequestMeta object from the source metadata.

    Args:
        source_meta: The original metadata containing attributes
        like company_id, dept_class, session_id, and modify_flag.

    Returns:
        CallbackRequestMeta: The constructed callback metadata object.
    """
    return CallbackRequestMeta(
        company_id=source_meta.company_id,
        dept_class=source_meta.dept_class,
        session_id=source_meta.session_id,
        modify_flag=source_meta.modify_flag
    )


def _build_callback_request(meta: CallbackRequestMeta, result_cd: int, result_desc: str,
                            doc_uid: str, step_cd: int, page_info: List[PageInfo]) -> CallbackRequest:
    """
    Build a CallbackRequest object required for the callback API request.

    Args:
        meta (CallbackRequestMeta): The callback metadata.
        result_cd (int): The result code.
        result_desc (str): The result description.
        doc_uid (str): The unique document identifier.
        step_cd (int): The processing step code.
        page_info (List[PageInfo]): A list of page information.

    Returns:
        CallbackRequest: The constructed callback request object.
    """
    return CallbackRequest(
        result_cd=result_cd,
        result_desc=result_desc,
        meta=meta,
        result=Result(
            doc_uid=doc_uid,
            step_cd=step_cd,
            page_info=page_info
        )
    )


def set_extract_doc_request(doc_request: RegisterDocRequest, doc_info: ExtractFiles) -> ExtractDocRequest:
    """
    Create an extract document request.

    Args:
        doc_request (RegisterDocRequest): The original document registration request.
        doc_info (ExtractFiles): The file information object.

    Returns:
        ExtractDocRequest: The constructed extract document request.
    """
    logger.debug("[set_extract_doc_request] invoked")

    # If file_get_info exists, validate it using the Pydantic model
    file_get_info = (ExtractFileInfo.model_validate(doc_request.documents.file_get_info)
                     if doc_request.documents.file_get_info else None)

    # Build metadata for the extract request
    meta = ExtractDocRequestMeta(
        company_id=doc_request.meta.company_id,
        dept_class=doc_request.meta.dept_class,
        rag_sys_info=doc_request.meta.rag_sys_info,
        session_id=doc_request.meta.session_id,
        callback_url=doc_request.meta.callback_url,
        extract_callback_url=settings.api_interface.extract_callback_url,
        modify_flag=doc_request.meta.modify_flag,
        policy=doc_request.meta.policy,
        param1=doc_request.meta.param1,
        param2=doc_request.meta.param2,
        param3=doc_request.meta.param3,
    )

    extract_doc_request = ExtractDocRequest(
        meta=meta,
        documents=ExtractDocuments(
            file_get_type=doc_request.documents.file_get_type.lower(),
            file_get_info=file_get_info,
            files=ExtractFiles.model_validate(doc_info)
        )
    )
    logger.debug(f"ExtractDocRequest JSON: {extract_doc_request.model_dump_json()[:300]}...")
    return extract_doc_request


async def request_indexing(request: ExtractCallbackRequest) -> IndexingResponse:
    """
    Process an asynchronous indexing request.

    Args:
        request (ExtractCallbackRequest): The extract callback request object containing the data needed for indexing.

    Returns:
        IndexingResponse: The response from the indexing API.
    """
    logger.debug(f"[request_indexing] invoked: [session_id]: {request.meta.session_id}, "
                 f"[doc_id]: {request.result.doc_uid}({request.result.doc_name})")
    try:
        # Convert page information (if none, return an empty list)
        page_info = _convert_page_info(request.result.page_info)

        # Construct the indexing request object
        indexing_request = IndexingRequest(
            meta=IndexingRequestMeta(
                **request.meta.dict(),
                indexing_callback_url=settings.api_interface.indexing_callback_url
            ),
            data=IndexingData(
                document=IndexingDocument(
                    doc_uid=request.result.doc_uid,
                    doc_name=request.result.doc_name,
                    job_class=request.result.job_class
                ),
                page_info=page_info
            )
        )
        logger.debug(f"[request_indexing] request json: {indexing_request.model_dump_json()[:300]}...")

        # Call the indexing API asynchronously
        response_json = await rc.restapi_post_async(
            settings.api_interface.indexing_request_url,
            indexing_request.model_dump()
        )
        return IndexingResponse.model_validate(response_json)

    except aiohttp.ClientError as e:
        logger.error(f"[request_indexing] API call error: {e}\n[session_id]: {request.meta.session_id}, "
                     f"[doc_id]: {request.result.doc_uid}")
    except Exception as e:
        logger.error(f"[request_indexing] Exception occurred: {e}\n[session_id]: {request.meta.session_id}, "
                     f"[doc_id]: {request.result.doc_uid}")

    # Return an error response if an exception occurs
    return IndexingResponse(**create_error_response(ErrorCd.INDEXING_REQ_EXCEPT))


async def send_was_callback_extract_fail(request: ExtractCallbackRequest, step_cd: int) -> Optional[CallbackResponse]:
    """
    Send a callback to the WAS when document extraction fails.

    Args:
        request (ExtractCallbackRequest): The original extract callback request object.
        step_cd (int): The processing step code indicating failure.

    Returns:
        Optional[CallbackResponse]: The callback response object (or None if failed).
    """
    logger.debug(f"[send_was_callback_extract_fail] invoked: [session_id]: {request.meta.session_id}, "
                 f"[doc_id]: {request.result.doc_uid}({request.result.doc_name})")

    # Build callback metadata
    meta = _build_callback_meta(request.meta)
    # Create the CallbackRequest object
    callback_request = _build_callback_request(
        meta=meta,
        result_cd=request.result_cd,
        result_desc=request.result_desc,
        doc_uid=request.result.doc_uid,
        step_cd=step_cd,
        page_info=[]
    )
    logger.debug(f"[send_was_callback_extract_fail] request json: {callback_request.model_dump_json()[:300]}...")

    try:
        callback_response = await rc.restapi_post_async(
            request.meta.callback_url,
            callback_request.model_dump()
        )
        return CallbackResponse.model_validate(callback_response)
    except Exception as e:
        logger.error(f"[send_was_callback_extract_fail] error: {e}\n[session_id]: {request.meta.session_id}, "
                     f"[doc_id]: {request.result.doc_uid}")
        return None


async def send_was_callback_extract_post_fail(request: ExtractDocRequest, response: Optional[Dict[str, Any]],
                                              step_cd: int) -> None:
    """
    Send a callback to the WAS for post-processing when document extraction fails.

    Args:
        request (ExtractDocRequest): The extract document request object.
        response (Optional[Dict[str, Any]]): The API response containing error code and description.
        step_cd (int): The processing step code indicating failure.

    Returns:
        None
    """
    logger.debug(f"[send_was_callback_extract_post_fail]: [session_id]: {request.meta.session_id}, "
                 f"[doc_id]: {request.result.doc_uid}({request.result.doc_name})")

    try:
        meta = _build_callback_meta(request.meta)
        # Extract the document UID from request.documents.files
        doc_uid = request.documents.files.doc_uid
        callback_request = _build_callback_request(
            meta=meta,
            result_cd=response['result_cd'],
            result_desc=response['result_desc'],
            doc_uid=doc_uid,
            step_cd=step_cd,
            page_info=[]
        )
        logger.debug(
            f"[send_was_callback_extract_post_fail] request json: {callback_request.model_dump_json()[:300]}...")
        return await rc.restapi_post_async(
            request.meta.callback_url,
            callback_request.model_dump()
        )
    except Exception as err:
        logger.error(f"[send_was_callback_extract_post_fail] error: {err}\n[session_id]: {request.meta.session_id}, "
                     f"[doc_id]: {request.result.doc_uid}")
        return None


async def send_was_callback_extract(request: ExtractCallbackRequest, step_cd: int,
                                    indexing_response: Optional[IndexingResponse] = None) -> Optional[CallbackResponse]:
    """
    Send a callback to the WAS after document extraction.

    Args:
        request (ExtractCallbackRequest): The extract callback request object.
        step_cd (int): The processing step code.
        indexing_response (Optional[IndexingResponse], optional): If available, use the indexing response details.

    Returns:
        Optional[CallbackResponse]: The callback response object (or None if failed).
    """
    logger.debug(f"[send_was_callback_extract] invoked: [session_id]: {request.meta.session_id}, "
                 f"[doc_id]: {request.result.doc_uid}({request.result.doc_name})")
    try:
        # Convert page information
        page_info = _convert_page_info(request.result.page_info)

        # Use the indexing response if available; otherwise use the original values
        result_cd = indexing_response.result_cd if indexing_response else request.result_cd
        result_desc = indexing_response.result_desc if indexing_response else request.result_desc

        meta = _build_callback_meta(request.meta)
        callback_request = _build_callback_request(
            meta=meta,
            result_cd=result_cd,
            result_desc=result_desc,
            doc_uid=request.result.doc_uid,
            step_cd=step_cd,
            page_info=page_info
        )
        logger.debug(f"[send_was_callback_extract] request JSON: {callback_request.model_dump_json()[:300]}...")

        callback_response = await rc.restapi_post_async(
            request.meta.callback_url,
            callback_request.model_dump()
        )
        callback_response_obj = CallbackResponse.model_validate(callback_response)
        return callback_response_obj

    except Exception as err:
        logger.error(f"[send_was_callback_extract] error: {err}\n[session_id]: {request.meta.session_id}, "
                     f"[doc_id]: {request.result.doc_uid}")
        return None


async def send_was_callback_indexing(request: IndexingCallbackRequest, step_cd: int, no_except: bool) -> bool:
    """
    Send a callback to the WAS after indexing is completed.

    Args:
        request (IndexingCallbackRequest): The indexing callback request object.
        step_cd (int): The processing step code.
        no_except (bool): Determines the result code based on whether an exception occurred.

    Returns:
        bool: True if the callback was sent successfully; otherwise, False.
    """
    logger.debug(f"[send_was_callback_indexing] invoked: [session_id]: {request.meta.session_id}, "
                 f"[doc_id]: {request.result.doc_uid}")
    try:
        # Determine result code based on exception status
        result_cd = request.result_cd if no_except else ErrorCd.get_code(ErrorCd.INDEXING_CALLBACK_EXCEPT)
        result_desc = request.result_desc if no_except else ErrorCd.get_description(ErrorCd.INDEXING_CALLBACK_EXCEPT)

        page_info = _convert_page_info(request.result.page_info)
        meta = _build_callback_meta(request.meta)
        callback_request = _build_callback_request(
            meta=meta,
            result_cd=result_cd,
            result_desc=result_desc,
            doc_uid=request.result.doc_uid,
            step_cd=step_cd,
            page_info=page_info
        )
        logger.debug(f"[send_was_callback_indexing] request json: {callback_request.model_dump_json()[:300]}...")

        await rc.restapi_post_async(request.meta.callback_url, callback_request.model_dump())
        return True
    except Exception as err:
        logger.error(f"[send_was_callback_indexing] error: {err}\n[session_id]: {request.meta.session_id}, "
                     f"[doc_id]: {request.result.doc_uid}")
        return False


def optimize_category_faq_query(request: ChatRequest) -> str:
    """
    Generate an optimized FAQ query based on categories.

    For FAQ systems, filter out specified categories and combine them with the user's input;
    otherwise, return the user's input only.

    Args:
        request (ChatRequest): The chat request object.

    Returns:
        str: The optimized FAQ query string.
    """
    logger.info(f"[optimize_category_faq_query] invoked: [session_id]: {request.meta.session_id}")

    # Convert target FAQ categories to a set for fast lookup
    faq_category_rag_target_list = set(settings.retriever_type.faq_type.split(','))
    # Categories to exclude
    excluded_categories = {"담당자 메일 문의", "AI 직접 질문", "챗봇 문의"}

    # If the system is not targeted, return the user's input only
    if request.meta.rag_sys_info not in faq_category_rag_target_list:
        return request.chat.user

    # Combine category1, category2, category3 into a single list and filter them
    categories = [
        request.chat.category1,
        request.chat.category2,
        request.chat.category3
    ]

    filtered_categories = [
        category if idx == 2 else f"'{category}'"
        for idx, category in enumerate(categories)
        if category and category not in excluded_categories
    ]

    query = ", ".join(filtered_categories)
    return f"{query}, {request.chat.user}" if query else request.chat.user


async def process_chat(request: ChatRequest) -> ChatLLMResponse:
    """
    Process a chat request by interacting with the Retriever and LLM APIs to generate a response.

    The process involves:
      1. Reconstructing the request metadata.
      2. Applying FAQ query optimization.
      3. Optionally calling the Retriever API to generate a payload.
      4. Calling the LLM API to obtain the final chatbot response.

    Args:
        request (ChatRequest): The chat request object.

    Returns:
        ChatLLMResponse: The chatbot response as returned by the LLM API.
    """
    logger.info(f"[process_chat] invoked: [session_id]: {request.meta.session_id}")

    meta = DocChatCommonMeta(
        company_id=request.meta.company_id,
        session_id=request.meta.session_id,
        dept_class=request.meta.dept_class,
        rag_sys_info=request.meta.rag_sys_info,
    )

    try:
        # Build the request data for the Retriever API (excluding 'lang')
        retriever_chat_data = request.chat.dict(exclude={"lang"})
        chat_request = ChatRequest(
            meta=meta,
            chat=ChatRequestData.model_validate(retriever_chat_data)
        )
        logger.debug(f"[process_chat] lang:{request.chat.lang}, "
                     f"was chat request json: {chat_request.model_dump_json()[:300]}...")

        # Apply FAQ query optimization
        faq_query = optimize_category_faq_query(request)
        if faq_query:
            chat_request.chat.user = faq_query

        payloads: List[Payload] = []

        # Optionally call the Retriever API (based on chat history settings)
        if not settings.chat_history.enabled:
            retriever_response = await rc.restapi_post_async(
                settings.api_interface.retriever_request_url,
                chat_request.model_dump()
            )
            retriever_response_obj = ChatRetrieverResponse.model_validate(retriever_response)
            logger.debug(f"[process_chat] retriever response json: {retriever_response_obj.model_dump_json()[:300]}...")
            if retriever_response_obj.chat.payload:
                payloads = [
                    Payload(
                        doc_name=doc.doc_name,
                        doc_page=doc.doc_page,
                        content=doc.content
                    )
                    for doc in retriever_response_obj.chat.payload
                ]

        # Build the ChatLLMRequest object for the LLM API
        chat_llm_request = ChatLLMRequest(
            meta=meta,
            chat=ChatLLMReq(
                lang=request.chat.lang,
                user=request.chat.user,
                category1=request.chat.category1,
                category2=request.chat.category2,
                category3=request.chat.category3,
                payload=payloads
            )
        )
        logger.debug(f"[process_chat] lang:{request.chat.lang}, "
                     f"llm request json: {chat_llm_request.model_dump_json()[:300]}...")

        chat_llm_response = await rc.restapi_post_async(
            settings.api_interface.chat_llm_request_url,
            chat_llm_request.model_dump()
        )
        return chat_llm_response

    except Exception as err:
        logger.error(f"[process_chat] error: {err}\n[session_id]: {request.meta.session_id}")

        # Default system messages by language
        system_messages = {
            "ko": "죄송합니다. 지금 답변을 드릴 수 없습니다.",
            "jp": "申し訳ありませんが、現在回答することができません。",
            "en": "Sorry, we cannot provide an answer at this time.",
            "cn": "抱歉，我们目前无法提供答案。"
        }
        system_message = system_messages.get(
            request.chat.lang,
            "죄송합니다. 지금 답변을 드릴 수 없습니다."
        )
        return ChatLLMResponse(
            result_cd=ErrorCd.get_code(ErrorCd.COMMON_EXCEPTION),
            result_desc=ErrorCd.get_description(ErrorCd.COMMON_EXCEPTION),
            meta=meta,
            chat=ChatLLMRes(
                user=request.chat.user,
                system=system_message,
                category1=request.chat.category1,
                category2=request.chat.category2,
                category3=request.chat.category3,
                info=[]
            )
        )


async def process_chat_stream(request: ChatRequest, background_tasks: BackgroundTasks = None) -> StreamingResponse:
    """
    Process a streaming chat request by connecting to the LLM service's streaming functionality.

    This process involves:
      1. Reconstructing the request metadata
      2. Applying FAQ query optimization
      3. Connecting to the LLM service's streaming endpoint
      4. Returning a StreamingResponse for Server-Sent Events (SSE)

    Args:
        request (ChatRequest): The chat request object
        background_tasks (BackgroundTasks): FastAPI background tasks for async operations

    Returns:
        StreamingResponse: A streaming response that sends text incrementally as SSE
    """
    session_id = request.meta.session_id
    logger.info(f"[DEBUG] [process_chat_stream] 함수 시작: [session_id]: {session_id}")

    try:
        # 메타데이터 구성
        meta = DocChatCommonMeta(
            company_id=request.meta.company_id,
            session_id=session_id,
            dept_class=request.meta.dept_class,
            rag_sys_info=request.meta.rag_sys_info,
        )

        logger.info(
            f"[DEBUG] [process_chat_stream] 메타데이터 생성 완료: company_id={meta.company_id}, rag_sys_info={meta.rag_sys_info}")

        # 채팅 데이터 준비
        logger.info(f"[DEBUG] [process_chat_stream] 원본 요청 데이터: {request.model_dump_json()[:300]}...")

        try:
            chat_data = request.chat.dict(exclude={"lang"})
            logger.info(f"[DEBUG] [process_chat_stream] 채팅 데이터 추출 완료: {chat_data}")

            chat_request = ChatRequest(
                meta=meta,
                chat=ChatRequestData.model_validate(chat_data)
            )
            logger.info(f"[DEBUG] [process_chat_stream] 채팅 요청 객체 생성 완료")

        except Exception as e:
            logger.error(f"[DEBUG] [process_chat_stream] 채팅 데이터 변환 중 오류: {str(e)}")
            raise

        # FAQ 쿼리 최적화
        try:
            original_query = request.chat.user
            logger.info(f"[DEBUG] [process_chat_stream] FAQ 쿼리 최적화 전 원본 쿼리: {original_query}")

            faq_query = optimize_category_faq_query(request)
            if faq_query and faq_query != original_query:
                logger.info(f"[DEBUG] [process_chat_stream] FAQ 쿼리 최적화 결과: {faq_query}")
                chat_request.chat.user = faq_query
            else:
                logger.info("[DEBUG] [process_chat_stream] FAQ 쿼리 최적화 적용되지 않음")

        except Exception as e:
            logger.error(f"[DEBUG] [process_chat_stream] FAQ 쿼리 최적화 중 오류: {str(e)}")
            # FAQ 최적화 실패해도 계속 진행
            pass

        # LLM 요청 구성
        try:
            chat_llm_request = ChatLLMRequest(
                meta=meta,
                chat=ChatLLMReq(
                    lang=request.chat.lang,
                    user=chat_request.chat.user,
                    category1=request.chat.category1,
                    category2=request.chat.category2,
                    category3=request.chat.category3,
                    payload=[]  # For streaming, we'll use the LLM's retriever directly
                )
            )
            logger.info(f"[DEBUG] [process_chat_stream] LLM 요청 객체 생성 완료: lang={request.chat.lang}")
            logger.info(f"[DEBUG] [process_chat_stream] LLM 요청 JSON: {chat_llm_request.model_dump_json()[:300]}...")

        except Exception as e:
            logger.error(f"[DEBUG] [process_chat_stream] LLM 요청 객체 생성 중 오류: {str(e)}")
            raise

        # 스트리밍 URL 결정
        try:
            # 설정에서 스트리밍 URL 확인
            streaming_url = getattr(settings.api_interface, 'chat_llm_stream_request_url', None)
            logger.info(f"[DEBUG] [process_chat_stream] 설정의 스트리밍 URL: {streaming_url}")

            if not streaming_url:
                # 기본 LLM URL에 "/stream" 추가
                base_llm_url = getattr(settings.api_interface, 'chat_llm_request_url', None)
                logger.info(f"[DEBUG] [process_chat_stream] 기본 LLM URL: {base_llm_url}")

                if not base_llm_url:
                    logger.error("[DEBUG] [process_chat_stream] 오류: LLM URL이 설정되지 않음")
                    raise ValueError("LLM URL configuration missing")

                streaming_url = f"{base_llm_url}/stream"

            logger.info(f"[DEBUG] [process_chat_stream] 최종 스트리밍 URL: {streaming_url}")

        except Exception as e:
            logger.error(f"[DEBUG] [process_chat_stream] 스트리밍 URL 결정 중 오류: {str(e)}")
            raise

        # 스트리밍 요청 전송
        try:
            logger.info(f"[DEBUG] [process_chat_stream] 스트리밍 요청 시작: URL={streaming_url}")

            # RestClient를 통해 스트리밍 요청 전송
            request_data = chat_llm_request.model_dump()
            logger.info(f"[DEBUG] [process_chat_stream] 요청 데이터: {str(request_data)[:300]}...")

            # 실제 스트리밍 요청 전송
            stream_response = await rc.restapi_stream_request_async(
                streaming_url,
                request_data,
                background_tasks=background_tasks
            )

            logger.info(f"[DEBUG] [process_chat_stream] 스트리밍 응답 객체 받음: {type(stream_response)}")
            logger.info(f"[DEBUG] [process_chat_stream] 스트리밍 응답 객체 받음: {stream_response}")

            # 응답에 추가 헤더 설정
            if hasattr(stream_response, 'headers'):
                stream_response.headers["Cache-Control"] = "no-cache"
                stream_response.headers["Connection"] = "keep-alive"
                logger.info("[DEBUG] [process_chat_stream] 응답 헤더 설정 완료")

            return stream_response

        except Exception as e:
            logger.error(f"[DEBUG] [process_chat_stream] 스트리밍 요청 중 오류: {str(e)}", exc_info=True)
            raise

    except Exception as err:
        logger.error(f"[DEBUG] [process_chat_stream] 치명적 오류: {err}", exc_info=True)

        # 사용자에게 보여줄 오류 스트림 생성
        async def error_stream():
            # 언어별 오류 메시지
            system_messages = {
                "ko": "죄송합니다. 지금 답변을 드릴 수 없습니다.",
                "jp": "申し訳ありませんが、現在回答することができません。",
                "en": "Sorry, we cannot provide an answer at this time.",
                "cn": "抱歉，我们目前无法提供答案。"
            }
            error_message = system_messages.get(
                request.chat.lang,
                "죄송합니다. 지금 답변을 드릴 수 없습니다."
            )

            # 오류 JSON 생성
            error_data = {
                "error": True,
                "text": f"{error_message} (오류: {str(err)})",
                "finished": True
            }

            logger.info(f"[DEBUG] [process_chat_stream] 오류 응답 생성: {json.dumps(error_data, ensure_ascii=False)}")

            # SSE 형식으로 오류 전송
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            error_stream(),
            media_type="text/event-stream; charset=utf-8"
        )

    except Exception as err:
        logger.error(f"[process_chat_stream] error: {err}\n[session_id]: {request.meta.session_id}", exc_info=True)

        # Create an error response stream
        async def error_stream():
            # Get appropriate error message based on language
            system_messages = {
                "ko": "죄송합니다. 지금 답변을 드릴 수 없습니다.",
                "jp": "申し訳ありませんが、現在回答することができません。",
                "en": "Sorry, we cannot provide an answer at this time.",
                "cn": "抱歉，我们目前无法提供答案。"
            }
            error_message = system_messages.get(
                request.chat.lang,
                "죄송합니다. 지금 답변을 드릴 수 없습니다."
            )

            # Send error as SSE
            error_data = {
                "error": True,
                "text": f"{error_message} ({str(err)})",
                "finished": True
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            error_stream(),
            media_type="text/event-stream; charset=utf-8"
        )


async def doc_delete(request) -> DeleteDocResponse:
    """
    Process a document deletion request.

    Args:
        request: The document deletion request object containing meta and documents attributes.

    Returns:
        DeleteDocResponse: The response from the document deletion API.
    """
    logger.info(f"[doc_delete] called: [session_id]: {request.meta.session_id}")

    meta = DocChatCommonMeta(
        company_id=request.meta.company_id,
        session_id=request.meta.session_id,
        dept_class=request.meta.dept_class,
        rag_sys_info=request.meta.rag_sys_info,
    )

    try:
        # Convert each document into a DocDelDocuments object
        documents = [DocDelDocuments(doc_uid=document.doc_uid) for document in request.documents]
        delete_request = DeleteDocRequest(
            meta=meta,
            documents=documents
        )
        logger.debug(f"[doc_delete] request json: {delete_request.model_dump_json()[:300]}...")

        del_doc_response = await rc.restapi_post_async(
            settings.api_interface.doc_del_request_url,
            delete_request.model_dump()
        )
        return del_doc_response

    except Exception as err:
        logger.error(f"[doc_delete] error: {err}\n[session_id]: {request.meta.session_id}")
        # If deletion fails, mark each document as unsuccessful
        documents = [DocDelResDocuments(doc_uid=document.doc_uid, success=False) for document in request.documents]
        return DeleteDocResponse(
            result_cd=ErrorCd.get_code(ErrorCd.DELETE_DOC_EXCEPT),
            result_desc=ErrorCd.get_description(ErrorCd.DELETE_DOC_EXCEPT),
            meta=meta,
            documents=documents
        )


async def doc_search(request: SearchDocRequest) -> SearchDocResponse:
    """
    Process a document search request.

    Args:
        request (SearchDocRequest): The document search request object.

    Returns:
        SearchDocResponse: The response from the search API.
    """
    logger.info(f"[doc_search] invoked: [session_id]: {request.meta.session_id}")

    meta = DocChatCommonMeta(
        company_id=request.meta.company_id,
        session_id=request.meta.session_id,
        dept_class=request.meta.dept_class,
        rag_sys_info=request.meta.rag_sys_info,
    )

    try:
        search_doc_response = await rc.restapi_post_async(
            settings.api_interface.doc_search_request_url,
            request.model_dump()
        )
        search_doc_response_obj = SearchDocResponse.model_validate(search_doc_response)

        search_docs = search_doc_response_obj.search.result
        search_docs_cnt = search_doc_response_obj.search.search_cnt

        # Assign reverse order numbers to search results and convert them into a list
        eval_search_docs = [
            SearchDocResult(
                search_seq=search_docs_cnt - idx,
                file_name=result.file_name,
                file_path=result.file_path,
                doc_page=result.doc_page,
                data=result.data
            )
            for idx, result in enumerate(search_docs)
        ]

        # Calculate pagination indices
        get_search_start_idx = (request.search.page_num - 1) * request.search.page_per_cnt
        get_search_end_idx = get_search_start_idx + request.search.page_per_cnt
        research_docs = eval_search_docs[get_search_start_idx:get_search_end_idx]

        final_search_doc_response = SearchDocResponse(
            result_cd=search_doc_response_obj.result_cd,
            result_desc=search_doc_response_obj.result_desc,
            meta=meta,
            search=SearchRes(
                content=request.search.content,
                next_ids=search_doc_response_obj.search.next_ids,
                search_cnt=search_doc_response_obj.search.search_cnt,
                page_per_cnt=request.search.page_per_cnt,
                page_num=request.search.page_num,
                result=research_docs
            )
        )
        logger.debug(f"[doc_search] response json: {final_search_doc_response.model_dump_json()[:300]}...")
        return final_search_doc_response

    except Exception as err:
        logger.error(f"[doc_search] error: {err}\n[session_id]: {request.meta.session_id}")
        return SearchDocResponse(
            result_cd=ErrorCd.get_code(ErrorCd.SEARCH_DOC_EXCEPT),
            result_desc=ErrorCd.get_description(ErrorCd.SEARCH_DOC_EXCEPT),
            meta=meta,
            search=SearchRes(
                content=request.search.content,
                next_ids="",
                search_cnt=0,
                page_per_cnt=request.search.page_per_cnt,
                page_num=request.search.page_num,
                result=[]
            )
        )


async def doc_modify(request: ModifyDocRequest) -> ModifyDocResponse:
    """
    Process a document modification request.

    Differentiates between modification and non-modification cases to call the indexing API and
    returns a ModifyDocResponse based on the result.

    Args:
        request (ModifyDocRequest): The document modification request object.

    Returns:
        ModifyDocResponse: The response from the indexing API or an error response.
    """
    logger.info(f"[doc_modify] invoked: [session_id]: {request.meta.session_id}, "
                f"[doc_id]: {request.data.document.doc_uid}")
    # Log differently based on the modify_flag
    logging.debug(
        "[doc_modify] request_indexing(modify) called" if request.meta.modify_flag else "request_indexing called")
    from pydantic.v1 import ValidationError
    try:
        # If page_info exists, convert it into a list of PageInfo objects
        page_info = [PageInfo(page_num=page.page_num, context=page.context)
                     for page in request.data.page_info] if request.data.page_info else []

        # Build meta, document, and data objects for the indexing request
        indexing_meta = IndexingRequestMeta(
            company_id=request.meta.company_id,
            dept_class=request.meta.dept_class,
            rag_sys_info=request.meta.rag_sys_info,
            session_id=request.meta.session_id,
            callback_url=request.meta.callback_url,
            indexing_callback_url=settings.api_interface.indexing_callback_url,
            modify_flag=request.meta.modify_flag
        )
        indexing_document = Document(
            doc_uid=request.data.document.doc_uid,
            doc_name=request.data.document.doc_name,
            job_class=request.data.document.job_class
        )
        indexing_data = Data(document=indexing_document, page_info=page_info)

        indexing_request = IndexingRequest(meta=indexing_meta, data=indexing_data)
        logger.debug(f"[doc_modify] request json: {indexing_request.model_dump_json()[:300]}...")

        # Call the indexing API asynchronously
        indexing_response = await rc.restapi_post_async(
            settings.api_interface.indexing_request_url,
            indexing_request.model_dump()
        )
        indexing_response_obj = ModifyDocResponse.model_validate(indexing_response)
        logging.debug(f"[doc_modify] response json: {indexing_response_obj.model_dump_json()[:300]}...")
        return indexing_response_obj

    except (ValidationError, Exception) as err:
        logging.error(f"[doc_modify] error: {err}\n[session_id]: {request.meta.session_id}, "
                      f"[doc_id]: {request.data.document.doc_uid}")
        return ModifyDocResponse(
            result_cd=ErrorCd.get_code(ErrorCd.INDEXING_REQ_EXCEPT),
            result_desc=ErrorCd.get_description(ErrorCd.INDEXING_REQ_EXCEPT),
            meta=ModifyDocResponseMeta(
                company_id=request.meta.company_id,
                dept_class=request.meta.dept_class,
                session_id=request.meta.session_id,
                doc_uid=request.result.doc_uid
            )
        )
