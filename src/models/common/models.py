from typing import Optional, List

from pydantic import BaseModel, Field


class Policy(BaseModel):
    """
    Represents a policy with a key-value pair.

    Attributes:
        key (str): The policy key.
        value (str): The corresponding policy value.
    """
    key: str = Field(..., description="Policy key")
    value: str = Field(..., description="Policy value")


class MetaBase(BaseModel):
    """
    Base metadata model containing essential attributes.

    Attributes:
        company_id (str): The ID of the company.
        dept_class (Optional[str]): The department classification (if applicable).
    """
    company_id: str = Field(..., description="Company ID")
    dept_class: Optional[str] = Field(None, description="Department classification")


class Meta(MetaBase):
    """
    Extended metadata model containing additional attributes.

    Attributes:
        rag_sys_info (Optional[str]): Information about the RAG system.
        session_id (Optional[str]): Unique session identifier.
        callback_url (Optional[str]): URL for callback processing.
        modify_flag (bool): Indicates whether this is a modification request.
    """
    rag_sys_info: Optional[str] = Field(None, description="RAG system information")
    session_id: Optional[str] = Field(None, description="Session ID")
    callback_url: Optional[str] = Field(None, description="Callback URL")
    modify_flag: bool = Field(False, description="Modification flag (False: insert, True: update)")


class CallbackRequestMeta(MetaBase):
    """
    Metadata for callback requests.

    Attributes:
        session_id (Optional[str]): Unique session identifier.
        modify_flag (bool): Indicates whether this is a modification request.
    """
    session_id: Optional[str] = Field(None, description="Session ID")
    modify_flag: bool = Field(False, description="Modification flag (False: insert, True: update)")


class DocChatCommonMeta(MetaBase):
    """
    Metadata for document-based chat requests.

    Attributes:
        rag_sys_info (Optional[str]): Information about the RAG system.
        session_id (Optional[str]): Unique session identifier.
    """
    rag_sys_info: Optional[str] = Field(None, description="RAG system information")
    session_id: Optional[str] = Field(None, description="Session ID")


class ModifyDocResponseMeta(MetaBase):
    """
    Metadata for document modification response.

    Attributes:
        session_id (Optional[str]): Unique session identifier.
        doc_uid (Optional[str]): Unique document identifier.
    """
    session_id: Optional[str] = Field(None, description="Session ID")
    doc_uid: Optional[str] = Field(None, description="Document Unique ID")


class DocumentRegisterRequestMeta(Meta):
    """
    Metadata for document registration requests.

    Attributes:
        policy (List[Policy]): List of policies related to the document.
        param1 (Optional[str]): Additional parameter 1.
        param2 (Optional[str]): Additional parameter 2.
        param3 (Optional[str]): Additional parameter 3.
    """
    policy: List[Policy] = Field(default_factory=list, description="List of policies associated with the document")
    param1: Optional[str] = Field(None, description="Additional parameter 1")
    param2: Optional[str] = Field(None, description="Additional parameter 2")
    param3: Optional[str] = Field(None, description="Additional parameter 3")


class DocumentRegisterResponseMeta(MetaBase):
    """
    Metadata for document registration responses.

    Attributes:
        session_id (Optional[str]): Unique session identifier.
    """
    session_id: Optional[str] = Field(None, description="Session ID")


class ExtractDocRequestMeta(DocumentRegisterRequestMeta):
    """
    Metadata for document extraction requests.

    Attributes:
        extract_callback_url (str): URL to be called upon extraction completion.
    """
    extract_callback_url: str = Field(..., description="Document extraction callback URL")


class ExtractDocResponseMeta(MetaBase):
    """
    Metadata for document extraction responses.

    Attributes:
        session_id (Optional[str]): Unique session identifier.
    """
    session_id: Optional[str] = Field(None, description="Session ID")


class IndexingCallbackRequestMeta(MetaBase):
    """
    Metadata for indexing callback requests.

    Attributes:
        session_id (Optional[str]): Unique session identifier.
        callback_url (Optional[str]): URL for callback processing.
        modify_flag (bool): Indicates whether this is a modification request.
    """
    session_id: Optional[str] = Field(None, description="Session ID")
    callback_url: Optional[str] = Field(None, description="Callback URL")
    modify_flag: bool = Field(False, description="Modification flag (False: insert, True: update)")


class IndexingRequestMeta(Meta):
    """
    Metadata for indexing requests.

    Attributes:
        indexing_callback_url (Optional[str]): URL for indexing completion callback.
    """
    indexing_callback_url: Optional[str] = Field(None, description="Indexing callback URL")


class PageInfo(BaseModel):
    """
    Represents document page information.

    Attributes:
        page_num (int): The page number.
        context (Optional[str]): The content of the page.
    """
    page_num: int = Field(..., description="Page number")
    context: Optional[str] = Field(None, description="Page content")


class Result(BaseModel):
    """
    Represents document processing results.

    Attributes:
        doc_uid (str): Unique identifier for the document.
        step_cd (int): Step code for processing.
        page_info (Optional[List[PageInfo]]): List of page information.
    """
    doc_uid: str = Field(..., description="Document Unique ID")
    step_cd: int = Field(..., description="Processing step code")
    page_info: Optional[List[PageInfo]] = Field(None, description="List of document page information")


class Payload(BaseModel):
    """
    Represents document information.

    Attributes:
        doc_name (str): The name of the document.
        doc_page (str): The number of pages in the document.
        content (str): The content of the document.
        doc_path (Optional[str]): The file path where the document is stored.
    """
    doc_name: str = Field(..., description="Document name")
    doc_page: str = Field(..., description="Number of pages in the document")
    content: str = Field(..., description="Document content")
    doc_path: Optional[str] = Field(None, description="Document storage path")
