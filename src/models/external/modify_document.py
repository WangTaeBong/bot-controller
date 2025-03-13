from typing import Optional, List
from pydantic import BaseModel
from src.models.common.models import Meta, PageInfo, ModifyDocResponseMeta  # 공통 모델 import


class ModifyReqDocument(BaseModel):
    """
    Represents the document to be modified.

    Attributes:
        doc_uid (str): The unique identifier of the document.
        doc_name (Optional[str]): The name of the document (if applicable).
        job_class (Optional[str]): The job classification related to the document.
    """
    doc_uid: str  # 수정할 문서의 고유 ID
    doc_name: Optional[str] = None  # 문서 이름 (선택 사항)
    job_class: Optional[str] = None  # 업무 구분 코드 (선택 사항)


class ModifyReqData(BaseModel):
    """
    Represents the data for a document modification request.

    Attributes:
        document (ModifyReqDocument): The document details to be modified.
        page_info (Optional[List[PageInfo]]): The list of pages with content updates.
    """
    document: ModifyReqDocument  # 수정할 문서 정보
    page_info: Optional[List[PageInfo]] = None  # 문서 페이지 정보 (선택 사항)


class ModifyDocRequest(BaseModel):
    """
    Represents a request to modify a document.

    Attributes:
        meta (Meta): Metadata related to the modification request.
        data (ModifyReqData): The modification data, including document details and page info.

    Example:
        {
            "meta": {
                "company_id": "mico",
                "dept_class": "dept1_dept2_dept3",
                "rag_sys_info": "vectorDB info",
                "session_id": "session_id",
                "callback_url": "/data_extract_callback.do",
                "modify_flag": True
            },
            "data": {
                "document": {
                    "doc_uid": "고유 uuid",
                    "doc_name": "/abc.doc",
                    "job_class": "업무구분 code"
                },
                "page_info": [
                    {
                        "page_num": 1,
                        "context": "Test page\n Hello"
                    }
                ]
            }
        }
    """
    meta: Meta  # 문서 수정 요청 관련 메타데이터
    data: ModifyReqData  # 문서 수정 관련 데이터 (문서 정보 및 페이지 정보 포함)

    # FastAPI의 OpenAPI 문서에서 예제 데이터를 제공
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "meta": {
                        "company_id": "mico",
                        "dept_class": "dept1_dept2_dept3",
                        "rag_sys_info": "vectorDB info",
                        "session_id": "session_id",
                        "callback_url": "/data_extract_callback.do",
                        "modify_flag": True
                    },
                    "data": {
                        "document": {
                            "doc_uid": "고유 uuid",
                            "doc_name": "/abc.doc",
                            "job_class": "업무구분 code"
                        },
                        "page_info": [
                            {
                                "page_num": 1,
                                "context": "Test page\n Hello"
                            }
                        ]
                    }
                }
            ]
        }
    }


class ModifyDocResponse(BaseModel):
    """
    Represents a response to a document modification request.

    Attributes:
        result_cd (int): The response code indicating the success or failure of the request.
        result_desc (Optional[str]): A descriptive message about the response status.
        meta (ModifyDocResponseMeta): Metadata related to the modification response.

    Example:
        {
            "result_cd": 200,
            "result_desc": "Success",
            "meta": {
                "company_id": "mico",
                "dept_class": "dept1_dept2_dept3",
                "session_id": "session_id",
                "doc_uid": "document uuid"
            }
        }
    """
    result_cd: int  # 응답 코드 (예: 200 - 성공, 400 - 요청 오류, 500 - 서버 오류)
    result_desc: Optional[str]  # 응답 메시지 (선택 사항)
    meta: ModifyDocResponseMeta  # 응답 메타데이터 (회사 ID, 세션 정보, 문서 ID 포함)

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
                        "doc_uid": "document uuid"
                    }
                }
            ]
        }
    }
