from typing import Optional, List

from pydantic import BaseModel

from src.models.common.models import Meta, DocChatCommonMeta  # 공통 모델 import


class SearchReq(BaseModel):
    """
    Represents a request for document search.

    Attributes:
        content (str): The search query content.
        max_cnt (int): The maximum number of search results to retrieve.
        page_per_cnt (Optional[int]): The number of results per page (if applicable).
        page_num (Optional[int]): The page number for pagination.
        next_ids (Optional[str]): An identifier for fetching the next set of results.
    """
    content: str  # 검색할 내용
    max_cnt: int  # 검색 최대 개수
    page_per_cnt: Optional[int] = None  # 페이지 당 결과 개수 (선택 사항)
    page_num: Optional[int] = None  # 요청 페이지 번호 (선택 사항)
    next_ids: Optional[str] = None  # 다음 결과를 가져오기 위한 식별자 (선택 사항)


class SearchDocRequest(BaseModel):
    """
    Represents a request model for document search.

    Attributes:
        meta (Meta): Metadata containing request details.
        search (SearchReq): The search parameters.

    Example:
        {
            "meta": {
                "company_id": "mico",
                "dept_class": "dept1_dept2_dept3",
                "rag_sys_info": "vectorDB info",
                "session_id": "session_id"
            },
            "search": {
                "content": "search_content",
                "max_cnt": 10,
                "page_per_cnt": 10,
                "page_num": 1,
                "next_ids": "ids_value"
            }
        }
    """
    meta: Meta  # 검색 요청 관련 메타데이터 (회사 ID, 세션 정보 포함)
    search: SearchReq  # 검색 요청 데이터 (쿼리, 페이지 정보 등)

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
                    "search": {
                        "content": "search_content",
                        "max_cnt": 10,
                        "page_per_cnt": 10,
                        "page_num": 1,
                        "next_ids": "ids_value"
                    }
                }
            ]
        }
    }


class SearchDocResult(BaseModel):
    """
    Represents an individual search result for a document.

    Attributes:
        file_name (Optional[str]): The name of the file found in the search results.
        file_path (Optional[str]): The file path where the document is stored.
        doc_page (Optional[str]): The page number within the document that matches the search.
        data (Optional[str]): The text content matching the search query.
    """
    file_name: Optional[str] = None  # 검색된 문서 파일 이름
    file_path: Optional[str] = None  # 검색된 문서 파일 경로
    doc_page: Optional[str] = None  # 검색된 문서의 페이지 번호 (문자열 형식)
    data: Optional[str] = None  # 검색된 문서의 해당 페이지 내용


class SearchRes(BaseModel):
    """
    Represents the structured search response.

    Attributes:
        content (str): The original search query content.
        next_ids (Optional[str]): Identifier for fetching additional results (if applicable).
        search_cnt (int): The total number of search results.
        page_per_cnt (Optional[int]): The number of results per page.
        page_num (Optional[int]): The current page number.
        result (Optional[List[SearchDocResult]]): A list of document search results.
    """
    content: str  # 원본 검색 요청 내용
    next_ids: Optional[str] = None  # 추가 검색 결과를 가져오기 위한 식별자 (선택 사항)
    search_cnt: int  # 전체 검색 결과 개수
    page_per_cnt: Optional[int] = None  # 페이지 당 검색 결과 개수 (선택 사항)
    page_num: Optional[int] = None  # 현재 페이지 번호 (선택 사항)
    result: Optional[List[SearchDocResult]] = None  # 검색된 문서 목록


class SearchDocResponse(BaseModel):
    """
    Represents the response model for a document search request.

    Attributes:
        result_cd (int): The response code indicating success or failure.
        result_desc (Optional[str]): A description of the response status.
        meta (DocChatCommonMeta): Metadata related to the search request.
        search (Optional[SearchRes]): The search results, if available.

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
            "search": {
                "content": "차량일지",
                "next_ids": "ids value",
                "search_cnt": 25,
                "page_per_cnt": 10,
                "page_num": 2,
                "result": [
                    {
                        "file_name": "test.doc",
                        "file_path": "/test.doc",
                        "doc_page": "3",
                        "data": "차량일지는 3일 입니다"
                    }
                ]
            }
        }
    """
    result_cd: int  # 응답 코드 (예: 200 - 성공, 400 - 요청 오류, 500 - 서버 오류)
    result_desc: Optional[str]  # 응답 메시지 (선택 사항)
    meta: DocChatCommonMeta  # 검색 요청 관련 메타데이터 (회사 ID, 세션 정보 포함)
    search: Optional[SearchRes] = None  # 검색 결과 데이터 (선택 사항)

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
                    "search": {
                        "content": "차량일지",
                        "next_ids": "ids value",
                        "search_cnt": 25,
                        "page_per_cnt": 10,
                        "page_num": 2,
                        "result": [
                            {
                                "file_name": "test.doc",
                                "file_path": "/test.doc",
                                "doc_page": "3",
                                "data": "차량일지는 3일 입니다"
                            }
                        ]
                    }
                }
            ]
        }
    }
