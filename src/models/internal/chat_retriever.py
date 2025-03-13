from typing import Optional, List

from pydantic import BaseModel

from src.models.common.models import Payload, DocChatCommonMeta  # 공통 모델 import


class ChatRetriever(BaseModel):
    """
    Represents a retriever model for chat interactions.

    This model is used for retrieving chat-related data based on user queries.

    Attributes:
        user (str): The user input query.
        category1 (Optional[str]): First-level category classification (if applicable).
        category2 (Optional[str]): Second-level category classification (if applicable).
        category3 (Optional[str]): Third-level category classification (if applicable).
        payload (Optional[List[Payload]]): Additional document-related information (if applicable).
    """
    user: str  # 사용자 입력 쿼리
    category1: Optional[str] = None  # 1차 카테고리 (선택 사항)
    category2: Optional[str] = None  # 2차 카테고리 (선택 사항)
    category3: Optional[str] = None  # 3차 카테고리 (선택 사항)
    payload: Optional[List[Payload]] = None  # 관련 문서 정보 (선택 사항)


class ChatRetrieverResponse(BaseModel):
    """
    Represents a response model for the Chat Retriever.

    This model provides structured information in response to a retrieval request.

    Attributes:
        result_cd (int): The response code indicating success or failure.
        result_desc (str): A descriptive message about the response status.
        meta (DocChatCommonMeta): Metadata containing response details.
        chat (ChatRetriever): The chat retriever response data.

    Example:
        {
            "result_cd": 200,
            "result_desc": "Success",
            "meta": {
                "company_id": "mico",
                "dept_class": "dept1_dept2_dept3",
                "session_id": "session_id",
                "rag_sys_info": "retriever_info"
            },
            "chat": {
                "user": "user123",
                "category1": "finance",
                "category2": "investment",
                "category3": "stocks",
                "payload": [
                    {
                        "doc_name": "report.pdf",
                        "doc_page": "1",
                        "content": "Extracted financial report summary."
                    }
                ]
            }
        }
    """
    result_cd: int  # 응답 코드 (예: 200 - 성공, 400 - 요청 오류, 500 - 서버 오류)
    result_desc: str  # 응답 메시지
    meta: DocChatCommonMeta  # 응답 메타데이터 (회사 ID, 세션 정보 포함)
    chat: ChatRetriever  # 채팅 검색 응답 데이터

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
                        "session_id": "session_id",
                        "rag_sys_info": "retriever_info"
                    },
                    "chat": {
                        "user": "user123",
                        "category1": "finance",
                        "category2": "investment",
                        "category3": "stocks",
                        "payload": [
                            {
                                "doc_name": "report.pdf",
                                "doc_page": "1",
                                "content": "Extracted financial report summary."
                            }
                        ]
                    }
                }
            ]
        }
    }
