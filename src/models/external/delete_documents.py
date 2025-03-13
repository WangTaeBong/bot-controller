from typing import Optional, List

from pydantic import BaseModel

from src.models.common.models import DocChatCommonMeta  # 공통 모델 import


class DocDelDocuments(BaseModel):
    """
    Represents a document to be deleted.

    Attributes:
        doc_uid (str): The unique identifier of the document to be deleted.
    """
    doc_uid: str  # 삭제할 문서의 고유 ID


class DocDelResDocuments(BaseModel):
    """
    Represents the result of a document deletion attempt.

    Attributes:
        doc_uid (str): The unique identifier of the deleted document.
        success (bool): Indicates whether the document was successfully deleted.
    """
    doc_uid: str  # 삭제된 문서의 고유 ID
    success: bool  # 삭제 성공 여부 (True: 성공, False: 실패)


class DeleteDocRequest(BaseModel):
    """
    Represents a request to delete one or more documents.

    Attributes:
        meta (DocChatCommonMeta): Metadata related to the deletion request, including company and session details.
        documents (List[DocDelDocuments]): A list of documents to be deleted.

    Example:
        {
            "meta": {
                "company_id": "mico",
                "dept_class": "dept1_dept2_dept3",
                "rag_sys_info": "rag_info",
                "session_id": "session_id"
            },
            "documents": [
                {"doc_uid": "Document UUID1"},
                {"doc_uid": "Document UUID2"}
            ]
        }
    """
    meta: DocChatCommonMeta  # 요청 메타데이터 (회사 ID, 세션 정보 포함)
    documents: List[DocDelDocuments]  # 삭제할 문서 목록

    # FastAPI의 OpenAPI 문서에서 예제 데이터를 제공
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "meta": {
                        "company_id": "mico",
                        "dept_class": "dept1_dept2_dept3",
                        "rag_sys_info": "rag_info",
                        "session_id": "session_id"
                    },
                    "documents": [
                        {"doc_uid": "Document UUID1"},
                        {"doc_uid": "Document UUID2"}
                    ]
                }
            ]
        }
    }


class DeleteDocResponse(BaseModel):
    """
    Represents a response to a document deletion request.

    Attributes:
        result_cd (int): The response code indicating the success or failure of the request.
        result_desc (Optional[str]): A descriptive message about the response status.
        meta (DocChatCommonMeta): Metadata related to the deletion response.
        documents (List[DocDelResDocuments]): A list of deletion results for each document.

    Example:
        {
            "result_cd": 200,
            "result_desc": "Success",
            "meta": {
                "company_id": "mico",
                "dept_class": "dept1_dept2_dept3",
                "rag_sys_info": "rag_info",
                "session_id": "session_id"
            },
            "documents": [
                {"doc_uid": "Document UUID1", "success": True},
                {"doc_uid": "Document UUID2", "success": False}
            ]
        }
    """
    result_cd: int  # 응답 코드 (예: 200 - 성공, 400 - 요청 오류, 500 - 서버 오류)
    result_desc: Optional[str]  # 응답 메시지 (선택 사항)
    meta: DocChatCommonMeta  # 응답 메타데이터 (회사 ID, 세션 정보 포함)
    documents: List[DocDelResDocuments]  # 문서 삭제 결과 목록

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
                        "rag_sys_info": "rag_info",
                        "session_id": "session_id"
                    },
                    "documents": [
                        {"doc_uid": "Document UUID1", "success": True},
                        {"doc_uid": "Document UUID2", "success": False}
                    ]
                }
            ]
        }
    }
