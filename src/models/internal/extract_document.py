from typing import Optional

from pydantic import BaseModel

from src.models.common.models import ExtractDocRequestMeta, ExtractDocResponseMeta  # 공통 모델 import


class FileGetInfo(BaseModel):
    """
    Represents file retrieval information.

    This model provides details about how to retrieve a file, including
    protocol, authentication credentials, and access tokens.

    Attributes:
        protocol (Optional[str]): The protocol used for file retrieval (e.g., "sftp", "http").
        host (Optional[str]): The hostname or IP address of the file server.
        port (Optional[int]): The port number for connecting to the file server.
        id (Optional[str]): The user ID for authentication.
        password (Optional[str]): The password for authentication.
        access_token (Optional[str]): The access token for authentication.
    """
    protocol: Optional[str] = None  # 파일 접근 프로토콜 (예: "sftp", "http")
    host: Optional[str] = None  # 파일이 저장된 서버의 호스트 주소
    port: Optional[int] = None  # 파일 접근을 위한 포트 번호
    id: Optional[str] = None  # 접근 ID (필요한 경우)
    password: Optional[str] = None  # 접근 비밀번호 (필요한 경우)
    access_token: Optional[str] = None  # 접근 토큰 (OAuth 등)


class Files(BaseModel):
    """
    Represents information about a document file.

    Attributes:
        doc_uid (str): The unique identifier of the document.
        doc_ext (str): The file extension (e.g., "pdf", "docx").
        doc_name (str): The name of the document file.
        doc_path (str): The file path where the document is stored.
        job_class (Optional[str]): The classification code of the document.
        file_url (Optional[str]): The URL from which the file can be accessed.
        new_reg_flag (bool): Indicates whether the document is newly registered.
        old_doc_uid (Optional[str]): The previous document ID if applicable.
    """
    doc_uid: str  # 문서의 고유 ID
    doc_ext: str  # 문서 파일 확장자 (예: "pdf", "docx")
    doc_name: str  # 문서 파일 이름
    doc_path: str  # 문서 파일 경로
    job_class: Optional[str] = None  # 업무 분류 코드 (선택 사항)
    file_url: Optional[str] = None  # 파일 접근 URL (선택 사항)
    new_reg_flag: bool = False  # 신규 등록 여부 (True: 신규, False: 기존)
    old_doc_uid: Optional[str] = None  # 기존 문서의 ID (선택 사항)


class Documents(BaseModel):
    """
    Represents the structure of a document for extraction.

    Attributes:
        file_get_type (str): The method used to retrieve the file (e.g., "local", "remote").
        file_get_info (Optional[FileGetInfo]): Additional details for file retrieval.
        files (Files): The file information for the document.
    """
    file_get_type: str  # 파일 가져오기 방식 (예: "local", "remote")
    file_get_info: Optional[FileGetInfo] = None  # 파일 접근 정보 (필요한 경우)
    files: Files  # 문서 파일 정보


class ExtractDocRequest(BaseModel):
    """
    Represents a request for document extraction.

    Attributes:
        meta (ExtractDocRequestMeta): Metadata related to the request.
        documents (Documents): The document data to be processed.

    Example:
        {
            "meta": {
                "company_id": "1234567890",
                "dept_class": "A_B_C",
                "session_id": "user_1234567890"
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
                "files": {
                    "doc_uid": "unique_uuid",
                    "doc_ext": "pdf",
                    "doc_name": "example.pdf",
                    "doc_path": "/path/to/document",
                    "job_class": "classification_code",
                    "file_url": "http://example.com/file.pdf",
                    "new_reg_flag": True,
                    "old_doc_uid": ""
                }
            }
        }
    """
    meta: ExtractDocRequestMeta  # 문서 추출 요청 관련 메타데이터
    documents: Documents  # 문서 정보

    # FastAPI의 OpenAPI 문서에서 예제 데이터를 제공
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "meta": {
                        "company_id": "1234567890",
                        "dept_class": "A_B_C",
                        "session_id": "user_1234567890"
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
                        "files": {
                            "doc_uid": "unique_uuid",
                            "doc_ext": "pdf",
                            "doc_name": "example.pdf",
                            "doc_path": "/path/to/document",
                            "job_class": "classification_code",
                            "file_url": "http://example.com/file.pdf",
                            "new_reg_flag": True,
                            "old_doc_uid": ""
                        }
                    }
                }
            ]
        }
    }


class ExtractDocResponse(BaseModel):
    """
    Represents the response for a document extraction request.

    Attributes:
        result_cd (int): The response code indicating success or failure.
        result_desc (str): A descriptive message about the response status.
        meta (ExtractDocResponseMeta): Metadata containing extraction details.

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
    meta: ExtractDocResponseMeta  # 응답 메타데이터 (회사 ID, 세션 정보 포함)

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
