from typing import Optional, List

from pydantic import BaseModel

from src.models.common.models import Payload, DocChatCommonMeta  # 공통 모델 import


class ChatLLMReq(BaseModel):
    """
    Represents a request message for an LLM-based chat system.

    Attributes:
        lang (str): The language of the request (default: "ko" for Korean).
        user (str): The user's chat input/query.
        category1 (Optional[str]): First-level category classification (if applicable).
        category2 (Optional[str]): Second-level category classification (if applicable).
        category3 (Optional[str]): Third-level category classification (if applicable).
        payload (Optional[List[Payload]]): Additional document-related information (if applicable).
    """
    lang: str = "ko"  # 기본 언어 (한국어 "ko" 기본값)
    user: str  # 사용자 입력 쿼리
    category1: Optional[str] = None  # 1차 카테고리 (선택 사항)
    category2: Optional[str] = None  # 2차 카테고리 (선택 사항)
    category3: Optional[str] = None  # 3차 카테고리 (선택 사항)
    payload: Optional[List[Payload]] = None  # 관련 문서 정보 (선택 사항)


class ChatLLMRequest(BaseModel):
    """
    Represents a top-level LLM-based chat request.

    Attributes:
        meta (DocChatCommonMeta): Metadata containing request details.
        chat (ChatLLMReq): The chat request message.

    Example:
        {
            "meta": {
                "company_id": "mico",
                "dept_class": "dept1_dept2_dept3",
                "rag_sys_info": "vectorDB info",
                "session_id": "session_id"
            },
            "chat": {
                "lang": "ko",
                "user": "test_user",
                "category1": "category1",
                "category2": "category2",
                "category3": "category3",
                "payload": [
                    {"doc_name": "doc1", "doc_page": "1", "content": "content1"}
                ]
            }
        }
    """
    meta: DocChatCommonMeta  # 채팅 요청 관련 메타데이터 (회사 ID, 세션 정보 포함)
    chat: ChatLLMReq  # 채팅 요청 메시지 데이터

    # FastAPI의 OpenAPI 문서에서 예제 데이터를 제공
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "meta": {
                        "company_id": "mico",
                        "dept_class": "dept1_dept2_dept3",
                        "rag_sys_info": "vectorDB info",
                        "session_id": "session_id"
                    },
                    "chat": {
                        "lang": "ko",
                        "user": "test_user",
                        "category1": "category1",
                        "category2": "category2",
                        "category3": "category3",
                        "payload": [
                            {"doc_name": "doc1", "doc_page": "1", "content": "content1"}
                        ]
                    }
                }
            ]
        }
    }


class ChatLLMRes(BaseModel):
    """
    Represents a response message from the LLM-based chat system.

    Attributes:
        user (str): The original user query.
        system (Optional[str]): The system-generated response message.
        category1 (Optional[str]): First-level category classification (if applicable).
        category2 (Optional[str]): Second-level category classification (if applicable).
        category3 (Optional[str]): Third-level category classification (if applicable).
        info (Optional[List[Payload]]): Additional document-related information (if applicable).
    """
    user: str  # 사용자 입력 쿼리
    system: Optional[str] = None  # 시스템 응답 메시지 (선택 사항)
    category1: Optional[str] = None  # 1차 카테고리 (선택 사항)
    category2: Optional[str] = None  # 2차 카테고리 (선택 사항)
    category3: Optional[str] = None  # 3차 카테고리 (선택 사항)
    info: Optional[List[Payload]] = None  # 관련 문서 정보 (선택 사항)


class ChatLLMResponse(BaseModel):
    """
    Represents a top-level LLM-based chat response.

    Attributes:
        result_cd (int): The response code indicating success or failure.
        result_desc (str): A descriptive message about the response status.
        meta (DocChatCommonMeta): Metadata containing response details.
        chat (ChatLLMRes): The chat response message.

    Example:
        {
            "result_cd": 200,
            "result_desc": "Success",
            "meta": {
                "company_id": "mico",
                "dept_class": "dept1_dept2_dept3",
                "rag_sys_info": "vectorDB info",
                "session_id": "session_id"
            },
            "chat": {
                "user": "test_user",
                "system": "response_message",
                "category1": "category1",
                "category2": "category2",
                "category3": "category3",
                "info": [
                    {"doc_name": "doc1", "doc_page": "1", "content": "content1"}
                ]
            }
        }
    """
    result_cd: int  # 응답 코드 (예: 200 - 성공, 400 - 요청 오류, 500 - 서버 오류)
    result_desc: str  # 응답 메시지
    meta: DocChatCommonMeta  # 응답 메타데이터 (회사 ID, 세션 정보 포함)
    chat: ChatLLMRes  # 채팅 응답 메시지 데이터

    # FastAPI의 OpenAPI 문서에서 예제 데이터를 제공
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "result_cd": 200,
                    "result_desc": "Success",
                    "meta": {
                        "company_id": "mico",
                        "dept_class": "dept1_dept2_dept3",
                        "rag_sys_info": "vectorDB info",
                        "session_id": "session_id"
                    },
                    "chat": {
                        "user": "test_user",
                        "system": "response_message",
                        "category1": "category1",
                        "category2": "category2",
                        "category3": "category3",
                        "info": [
                            {"doc_name": "doc1", "doc_page": "1", "content": "content1"}
                        ]
                    }
                }
            ]
        }
    }
