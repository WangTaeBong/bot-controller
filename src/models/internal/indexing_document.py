from typing import Optional, List

from pydantic import BaseModel

from src.models.common.models import PageInfo, IndexingRequestMeta, ModifyDocResponseMeta  # 공통 모델 import


class Document(BaseModel):
    """
    Represents document information required for indexing.

    Attributes:
        doc_uid (str): The unique identifier of the document.
        doc_name (str): The name of the document.
        job_class (Optional[str]): The classification code of the document.
    """
    doc_uid: str  # 문서의 고유 ID
    doc_name: str  # 문서 이름
    job_class: Optional[str] = None  # 업무 분류 코드 (선택 사항)


class Data(BaseModel):
    """
    Represents the data model containing a document and its associated pages.

    Attributes:
        document (Document): The document details.
        page_info (Optional[List[PageInfo]]): The extracted content of the document pages.
    """
    document: Document  # 문서 정보
    page_info: Optional[List[PageInfo]] = None  # 문서 페이지 정보 (선택 사항)


class IndexingRequest(BaseModel):
    """
    Represents the top-level indexing request model.

    Attributes:
        meta (IndexingRequestMeta): Metadata containing request details.
        data (Data): The document and page-related information.

    Example:
        {
            "meta": {
                "company_id": "mico",
                "dept_class": "dept1_dept2_dept3",
                "session_id": "session_id",
                "callback_url": "https://callback.url",
                "indexing_callback_url": "https://indexing.callback.url",
                "modify_flag": False
            },
            "data": {
                "document": {
                    "doc_uid": "document_uuid",
                    "doc_name": "document.pdf",
                    "job_class": "classification"
                },
                "page_info": [
                    {"page_num": 1, "context": "Extracted content"}
                ]
            }
        }
    """
    meta: IndexingRequestMeta  # 인덱싱 요청 관련 메타데이터
    data: Data  # 인덱싱 할 문서 및 페이지 정보

    # FastAPI의 OpenAPI 문서에서 예제 데이터를 제공
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "meta": {
                        "company_id": "mico",
                        "dept_class": "dept1_dept2_dept3",
                        "session_id": "session_id",
                        "callback_url": "https://callback.url",
                        "indexing_callback_url": "https://indexing.callback.url",
                        "modify_flag": False
                    },
                    "data": {
                        "document": {
                            "doc_uid": "document_uuid",
                            "doc_name": "document.pdf",
                            "job_class": "classification"
                        },
                        "page_info": [
                            {"page_num": 1, "context": "Extracted content"}
                        ]
                    }
                }
            ]
        }
    }


class IndexingResponse(BaseModel):
    """
    Represents the response model for an indexing request.

    Attributes:
        result_cd (int): The response code indicating success or failure.
        result_desc (str): A descriptive message about the response status.
        meta (ModifyDocResponseMeta): Metadata containing indexing response details.

    Example:
        {
            "result_cd": 200,
            "result_desc": "Success",
            "meta": {
                "company_id": "mico",
                "dept_class": "dept1_dept2_dept3",
                "session_id": "session_id",
                "doc_uid": "document_uuid"
            }
        }
    """
    result_cd: int  # 응답 코드 (예: 200 - 성공, 400 - 요청 오류, 500 - 서버 오류)
    result_desc: str  # 응답 메시지
    meta: ModifyDocResponseMeta  # 인덱싱 요청에 대한 응답 메타데이터

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
                        "doc_uid": "document_uuid"
                    }
                }
            ]
        }
    }
