from typing import Optional, List

from pydantic import BaseModel

from src.models.common.models import PageInfo, IndexingCallbackRequestMeta  # 공통 모델 import


class Result(BaseModel):
    """
    Represents the extracted result of an indexing operation.

    Attributes:
        doc_uid (str): The unique identifier of the document being indexed.
        step_cd (int): The step code indicating the stage of the indexing process.
        page_info (Optional[List[PageInfo]]): A list of page-related extraction details.
    """
    doc_uid: str  # 인덱싱 된 문서의 고유 ID
    step_cd: int  # 인덱싱 단계 코드
    page_info: Optional[List[PageInfo]] = None  # 문서 페이지 정보 (선택 사항)


class IndexingCallbackRequest(BaseModel):
    """
    Represents a request model for an indexing callback.

    This model is used when sending indexing results to a callback endpoint.

    Attributes:
        result_cd (int): The response code indicating success or failure.
        result_desc (str): A descriptive message about the indexing process.
        meta (IndexingCallbackRequestMeta): Metadata containing request details,
             including session and company information.
        result (Result): The extracted indexing result.

    Example:
        {
            "result_cd": 200,
            "result_desc": "Success",
            "meta": {
                "company_id": "mico",
                "dept_class": "dept1_dept2_dept3",
                "session_id": "session_id",
                "callback_url": "https://callback.url",
                "modify_flag": False
            },
            "result": {
                "doc_uid": "document_uuid",
                "step_cd": 1,
                "page_info": [
                    {"page_num": 1, "context": "Extracted content"}
                ]
            }
        }
    """
    result_cd: int  # 응답 코드 (예: 200 - 성공, 400 - 요청 오류, 500 - 서버 오류)
    result_desc: str  # 응답 메시지
    meta: IndexingCallbackRequestMeta  # 요청 메타데이터 (회사 ID, 세션 정보 포함)
    result: Result  # 인덱싱 결과 데이터

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
                        "callback_url": "https://callback.url",
                        "modify_flag": False
                    },
                    "result": {
                        "doc_uid": "document_uuid",
                        "step_cd": 1,
                        "page_info": [
                            {"page_num": 1, "context": "Extracted content"}
                        ]
                    }
                }
            ]
        }
    }


class IndexingCallbackResponse(BaseModel):
    """
    Represents the response model for an indexing callback.

    This model is returned after processing an indexing callback request.

    Attributes:
        result_cd (int): The response code indicating success or failure.
        result_desc (str): A descriptive message about the response status.
        doc_uid (str): The unique identifier of the document that was processed.

    Example:
        {
            "result_cd": 200,
            "result_desc": "Success",
            "doc_uid": "document_uuid"
        }
    """
    result_cd: int  # 응답 코드 (예: 200 - 성공, 400 - 요청 오류, 500 - 서버 오류)
    result_desc: str  # 응답 메시지
    doc_uid: str  # 처리된 문서의 고유 ID

    # FastAPI의 OpenAPI 문서에서 예제 데이터를 제공
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "result_cd": 200,
                    "result_desc": "Success",
                    "doc_uid": "document_uuid"
                }
            ]
        }
    }
