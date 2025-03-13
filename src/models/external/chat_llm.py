from typing import Optional, List

from pydantic import BaseModel

from src.models.common.models import Payload, DocChatCommonMeta  # 공통 모델 import


class BaseChat(BaseModel):
    """
    Base model for chat data.

    This model defines common fields for chat requests and responses.

    Attributes:
        category1 (Optional[str]): First-level category classification (if applicable).
        category2 (Optional[str]): Second-level category classification (if applicable).
        category3 (Optional[str]): Third-level category classification (if applicable).
    """
    category1: Optional[str] = None  # 1차 분류 (선택 사항)
    category2: Optional[str] = None  # 2차 분류 (선택 사항)
    category3: Optional[str] = None  # 3차 분류 (선택 사항)


class ChatRequestData(BaseChat):
    """
    Model representing user chat request data.

    Attributes:
        lang (str): The language of the chat (default: "ko" for Korean).
        user (str): The user's chat input/query.
    """
    lang: str = "ko"  # 기본 언어는 한국어 ("ko")
    user: str  # 사용자 입력 쿼리


class ChatResponseData(BaseChat):
    """
    Model representing system response to a chat request.

    Attributes:
        user (str): The original user query.
        system (str): The system-generated response.
        info (Optional[List[Payload]]): Additional document-related information.
    """
    user: str  # 사용자 입력 쿼리
    system: str  # 시스템 응답 메시지
    info: Optional[List[Payload]] = None  # 관련 문서 정보 (선택 사항)


class ChatRequest(BaseModel):
    """
    Model representing a chat request.

    This model includes metadata and the chat request data.

    Attributes:
        meta (DocChatCommonMeta): Metadata containing company and session details.
        chat (ChatRequestData): User chat request details.

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
                "user": "user query",
                "category1": "category1",
                "category2": "category2",
                "category3": "category3"
            }
        }
    """
    meta: DocChatCommonMeta  # 문서 검색과 관련된 메타데이터
    chat: ChatRequestData  # 사용자의 채팅 요청 데이터

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
                        "user": "user query",
                        "category1": "category1",
                        "category2": "category2",
                        "category3": "category3"
                    }
                }
            ]
        }
    }


class ChatResponse(BaseModel):
    """
    Model representing the system's response to a chat request.

    Attributes:
        result_cd (int): The response status code (e.g., 200 for success).
        result_desc (Optional[str]): A descriptive message about the response.
        meta (DocChatCommonMeta): Metadata containing company and session details.
        chat (ChatResponseData): The chat response details.

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
                "user": "user query",
                "system": "system answer",
                "category1": "category1",
                "category2": "category2",
                "category3": "category3",
                "info": [
                    {
                        "doc_name": "test.doc",
                        "doc_path": "/test/doc",
                        "doc_page": 1
                    }
                ]
            }
        }
    """
    result_cd: int  # 결과 코드 (예: 200 - 성공, 400 - 오류)
    result_desc: Optional[str]  # 응답 메시지 (선택 사항)
    meta: DocChatCommonMeta  # 문서 검색과 관련된 메타데이터
    chat: ChatResponseData  # 시스템 응답 데이터

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
                        "user": "user query",
                        "system": "system answer",
                        "category1": "category1",
                        "category2": "category2",
                        "category3": "category3",
                        "info": [
                            {
                                "doc_name": "test.doc",
                                "doc_path": "/test/doc",
                                "doc_page": 1
                            }
                        ]
                    }
                }
            ]
        }
    }
