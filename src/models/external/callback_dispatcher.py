from pydantic import BaseModel

from src.models.common.models import Result, CallbackRequestMeta  # 공통 모델 import


class CallbackRequest(BaseModel):
    """
    Represents a callback request model.

    This model is used to send callback data to an external system after processing a request.

    Attributes:
        result_cd (int): The result code of the callback request (e.g., 200 for success).
        result_desc (str): A descriptive message about the result.
        meta (CallbackRequestMeta): Metadata related to the callback, such as company and session details.
        result (Result): The document processing result, including document ID and step details.

    Example:
        {
            "result_cd": 200,
            "result_desc": "Success",
            "meta": {
                "company_id": "mico",
                "dept_class": "dept1_dept2_dept3",
                "session_id": "session_id",
                "modify_flag": True
            },
            "result": {
                "doc_uid": "Document UUID",
                "step_cd": 1,
                "page_info": [
                    {
                        "page_num": 1,
                        "context": "Test page\n Hello"
                    }
                ]
            }
        }
    """
    result_cd: int  # 결과 코드 (예: 200 - 성공, 400 - 오류)
    result_desc: str  # 결과 설명 메시지
    meta: CallbackRequestMeta  # 콜백 요청의 메타데이터 (회사 ID, 세션 정보 등)
    result: Result  # 문서 처리 결과 정보 (문서 UUID, 처리 단계 코드 등)

    # OpenAPI 문서에서 예제 데이터를 제공하기 위한 설정
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
                        "modify_flag": True
                    },
                    "result": {
                        "doc_uid": "Document UUID",
                        "step_cd": 1,
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


class CallbackResponse(BaseModel):
    """
    Represents a callback response model.

    This model defines the response returned after processing a callback request.

    Attributes:
        result_cd (int): The result code indicating the status of the callback response.
        result_desc (str): A descriptive message about the callback processing result.
        doc_uid (str): The unique document identifier related to the callback response.

    Example:
        {
            "result_cd": 200,
            "result_desc": "Success",
            "doc_uid": "document uuid"
        }
    """
    result_cd: int  # 응답 결과 코드 (예: 200 - 성공, 500 - 서버 오류)
    result_desc: str  # 응답 메시지
    doc_uid: str  # 콜백과 연결된 문서의 고유 ID

    # OpenAPI 문서에서 예제 데이터를 제공하기 위한 설정
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "result_cd": 200,
                    "result_desc": "Success",
                    "doc_uid": "document uuid"
                }
            ]
        }
    }
