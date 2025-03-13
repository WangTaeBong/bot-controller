from typing import Optional, List

from pydantic import BaseModel

from src.models.common.models import DocumentRegisterRequestMeta, DocumentRegisterResponseMeta  # 공통 모델 import
from src.models.internal.extract_document import Files  # 내부 파일 모델 import


class FileGetInfo(BaseModel):
    """
    Represents the access information required to retrieve a file.

    Attributes:
        protocol (Optional[str]): The file transfer protocol (e.g., "sftp", "http").
        host (Optional[str]): The host address where the file is stored.
        port (Optional[int]): The port number for file access.
        id (Optional[str]): The user ID for authentication (if required).
        password (Optional[str]): The password for authentication (if required).
        access_token (Optional[str]): An access token for authorization (if applicable).
    """
    protocol: Optional[str] = None  # 파일 접근 프로토콜 (예: "sftp", "http")
    host: Optional[str] = None  # 파일이 저장된 서버의 호스트 주소
    port: Optional[int] = None  # 파일 접근을 위한 포트 번호
    id: Optional[str] = None  # 접근 ID (필요한 경우)
    password: Optional[str] = None  # 접근 비밀번호 (필요한 경우)
    access_token: Optional[str] = None  # 접근 토큰 (OAuth 등)


class Documents(BaseModel):
    """
    Represents document information for registration.

    Attributes:
        file_get_type (str): The type of file retrieval method (e.g., "local", "remote").
        file_get_info (Optional[FileGetInfo]): Additional access details if required.
        files (List[Files]): A list of file metadata objects.
    """
    file_get_type: str  # 파일을 가져오는 방식 (예: "local", "url")
    file_get_info: Optional[FileGetInfo] = None  # 파일 접근 정보 (필요한 경우)
    files: List[Files]  # 문서 파일 목록


class RegisterDocRequest(BaseModel):
    """
    Represents a request to register a document.

    Attributes:
        meta (DocumentRegisterRequestMeta): Metadata for the document registration request.
        documents (Documents): The document details including access information and file list.

    Example:
        {
            "meta": {
                "company_id": "mico",
                "dept_class": "dept1_dept2_dept3",
                "rag_sys_info": "vectorDB info",
                "session_id": "session_id",
                "callback_url": "/data_extract_callback.do",
                "modify_flag": False,
                "policy": [{"key": "p_key", "value": "p_value"}],
                "param1": "",
                "param2": "",
                "param3": ""
            },
            "documents": {
                "file_get_type": "url",
                "file_get_info": {
                    "protocol": "sftp",
                    "host": "127.0.0.1",
                    "port": 22,
                    "id": "test",
                    "password": "test",
                    "access_token": "token_value"
                },
                "files": [
                    {
                        "doc_uid": "고유 uuid",
                        "doc_ext": "file extension",
                        "doc_name": "/abc.doc",
                        "doc_path": "/uuid 포맷",
                        "job_class": "업무구분code",
                        "file_url": "http://127.0.0.1/files/uuid",
                        "new_reg_flag": True,
                        "old_doc_uid": ""
                    }
                ]
            }
        }
    """
    meta: DocumentRegisterRequestMeta  # 문서 등록 요청에 대한 메타데이터
    documents: Documents  # 문서 및 파일 접근 정보 포함

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
                        "modify_flag": False,
                        "policy": [{"key": "p_key", "value": "p_value"}],
                        "param1": "",
                        "param2": "",
                        "param3": ""
                    },
                    "documents": {
                        "file_get_type": "local",
                        "file_get_info": {
                            "protocol": "sftp",
                            "host": "127.0.0.1",
                            "port": 22,
                            "id": "test",
                            "password": "test",
                            "access_token": "token_value"
                        },
                        "files": [
                            {
                                "doc_uid": "고유 uuid",
                                "doc_ext": "file extension",
                                "doc_name": "/abc.doc",
                                "doc_path": "/uuid 포맷",
                                "job_class": "업무구분code",
                                "file_url": "http://127.0.0.1/files/uuid",
                                "new_reg_flag": True,
                                "old_doc_uid": ""
                            }
                        ]
                    }
                }
            ]
        }
    }


class RegisterDocResponse(BaseModel):
    """
    Represents a response to a document registration request.

    Attributes:
        result_cd (int): The response code indicating success or failure.
        result_desc (str): A descriptive message about the response.
        meta (DocumentRegisterResponseMeta): Metadata containing the registration result.

    Example:
        {
            "result_cd": 200,
            "result_desc": "Success",
            "meta": {
                "company_id": "1234567890",
                "dept_class": "A_B_C",
                "session_id": "user_1234567890"
            }
        }
    """
    result_cd: int  # 응답 코드 (예: 200 - 성공, 400 - 요청 오류, 500 - 서버 오류)
    result_desc: str  # 응답 메시지
    meta: DocumentRegisterResponseMeta  # 문서 등록 응답 관련 메타데이터

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
                        "session_id": "user_1234567890"
                    }
                }
            ]
        }
    }
