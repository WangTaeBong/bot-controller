from typing import Optional, List

from pydantic import BaseModel

from src.models.common.models import Meta, PageInfo  # 공통 모델 import


class Result(BaseModel):
    """
    Represents the extracted result of a document processing step.

    Attributes:
        doc_uid (str): The unique identifier of the document.
        doc_name (str): The name of the document.
        doc_path (str): The file path where the document is stored.
        job_class (Optional[str]): The classification of the job associated with this document.
        step_cd (int): The step code indicating the processing stage of the document.
        page_info (Optional[List[PageInfo]]): A list of page-related extraction information.
    """
    doc_uid: str  # 문서의 고유 ID
    doc_name: str  # 문서 이름
    doc_path: str  # 문서 저장 경로
    job_class: Optional[str] = None  # 업무 구분 코드 (선택 사항)
    step_cd: int  # 문서 처리 단계 코드
    page_info: Optional[List[PageInfo]] = None  # 문서 페이지 정보 (선택 사항)


class ExtractCallbackRequest(BaseModel):
    """
    Represents the request model for an extract callback.

    This model is used when sending extraction results to a callback endpoint.

    Attributes:
        result_cd (int): The response code indicating success or failure.
        result_desc (str): A descriptive message about the extraction result.
        meta (Meta): Metadata containing request details, including session and company information.
        result (Result): The extracted document processing result.

    Example:
        {
            "result_cd": 200,
            "result_desc": "Success",
            "meta": {
                "company_id": "1234567890",
                "dept_class": "A_B_C",
                "session_id": "user_1234567890",
                "callback_url": "https://callback.url",
                "modify_flag": False
            },
            "result": {
                "doc_uid": "document_uuid",
                "doc_name": "document.pdf",
                "doc_path": "/path/to/document",
                "step_cd": 1,
                "page_info": [
                    {"page_num": 1, "context": "Extracted content"}
                ]
            }
        }
    """
    result_cd: int  # 응답 코드 (예: 200 - 성공, 400 - 요청 오류, 500 - 서버 오류)
    result_desc: str  # 응답 메시지
    meta: Meta  # 요청 메타데이터 (회사 ID, 세션 정보 포함)
    result: Result  # 문서 추출 결과 데이터

    # FastAPI의 OpenAPI 문서에서 예제 데이터를 제공
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "result_cd": 200,
                    "result_desc": "Success",
                    "meta": {
                        "company_id": "1234567890",
                        "dept_class": "A_B_C",
                        "session_id": "user_1234567890",
                        "callback_url": "https://callback.url",
                        "modify_flag": False
                    },
                    "result": {
                        "doc_uid": "document_uuid",
                        "doc_name": "document.pdf",
                        "doc_path": "/path/to/document",
                        "step_cd": 1,
                        "page_info": [
                            {"page_num": 1, "context": "Extracted content"}
                        ]
                    }
                }
            ]
        }
    }


class ExtractCallbackResponse(BaseModel):
    """
    Represents the response model for an extract callback.

    This model is returned after processing an extract callback request.

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
