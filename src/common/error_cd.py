from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class ErrorDetail:
    code: int
    desc: str


class ErrorCd(Enum):
    """
    Enum class for managing error codes and descriptions.
    """
    SUCCESS = ErrorDetail(200, "Success")
    COMMON_EXCEPTION = ErrorDetail(500, "Internal Server Error")
    NO_FILE_INFO = ErrorDetail(460, "File information does not exist")
    NO_CALLBACK_URL = ErrorDetail(461, "Callback URL does not exist")
    INDEXING_REQ_EXCEPT = ErrorDetail(462, "An error occurred while calling the indexing API.")
    INDEXING_CALLBACK_EXCEPT = ErrorDetail(463, "Error while processing indexing callback.")
    DELETE_DOC_EXCEPT = ErrorDetail(464, "Document delete failed (exception).")
    SEARCH_DOC_EXCEPT = ErrorDetail(465, "Document search failed (exception).")

    @classmethod
    def get_code(cls, error: "ErrorCd") -> int:
        """
        Get the code for a given ErrorCd member.

        Args:
            error (ErrorCd): The ErrorCd member.

        Returns:
            int: Error code.
        """
        return error.value.code

    @classmethod
    def get_description(cls, error: "ErrorCd") -> str:
        """
        Get the description for a given ErrorCd member.

        Args:
            error (ErrorCd): The ErrorCd member.

        Returns:
            str: Error description.
        """
        return error.value.desc

    @classmethod
    def get_error(cls, error: "ErrorCd") -> dict:
        """
        Get the full error information (code and description) for a given error type.

        Args:
            error (ErrorCd): The error type.

        Returns:
            dict: Dictionary containing error code and description.
        """
        return {"code": error.value.code, "desc": error.value.desc}
