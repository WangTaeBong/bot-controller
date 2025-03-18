import asyncio
import json
from typing import Dict, Any, Optional
import logging
from starlette.responses import StreamingResponse

import aiohttp
import requests
from requests.adapters import HTTPAdapter, Retry

from src.common.config_loader import ConfigLoader

# ================================
#         Configuration
# ================================

# Load settings from configuration
config_loader = ConfigLoader()
settings = config_loader.get_settings()


class RestClient:
    """
    A REST client for making synchronous and asynchronous HTTP requests.
    Supports automatic retries, proper exception handling, and integration with FastAPI's aiohttp session.
    """

    _aio_session: Optional[aiohttp.ClientSession] = None  # Managed globally for FastAPI
    ssl_enabled = settings.ssl.use_https  # Enable or disable SSL verification

    def __init__(self, default_headers: Optional[Dict[str, str]] = None):
        """
        Initializes the RestClient with optional default headers.
        Configures an internal requests.Session() with retry logic.

        Args:
            default_headers (Optional[Dict[str, str]]): Default headers for all requests.
        """
        self.default_headers = default_headers or {"Content-Type": "application/json"}
        self.session = requests.Session()

        # Configure automatic retries for resilient HTTP requests
        retries = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods={"GET", "POST"}
        )
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    @staticmethod
    def _prepare_body(body: Any) -> str:
        """
        Prepares the request body for HTTP requests.

        Args:
            body (Any): The data to include in the request body.

        Returns:
            str: The JSON-encoded string of the request body.

        Raises:
            ValueError: If the body cannot be serialized to JSON.
        """
        try:
            if isinstance(body, dict):
                return json.dumps(body)
            elif hasattr(body, "json") and callable(body.json):
                return body.json()
            else:
                raise ValueError("The body must be a dictionary or have a callable `json()` method.")
        except Exception as e:
            raise ValueError(f"Failed to prepare body: {e}") from e

    def restapi_post(self, url: str, body: Any, headers: Optional[Dict[str, str]] = None,
                     timeout: int = 120) -> requests.Response:
        """
        Sends a synchronous POST request.

        This method sends a HTTP POST request to the specified URL with a given payload.
        It includes automatic error handling for common HTTP issues such as timeouts,
        connection failures, and HTTP status errors.

        Args:
            url (str): The endpoint URL to send the request to.
            body (Any): The request payload, typically a dictionary.
            headers (Optional[Dict[str, str]]): Custom headers for the request. Defaults to `self.default_headers`.
            timeout (int): The maximum time (in seconds) to wait for a response before timing out. Default is 120 seconds.

        Returns:
            requests.Response: The HTTP response object, if the request is successful.

        Raises:
            RuntimeError: Raised in case of network failure, timeout, or HTTP error.
                - `TimeoutError`: If the request exceeds the specified timeout.
                - `ConnectionError`: If the server is unreachable.
                - `RequestException`: For any other unexpected request failure.
        """
        try:
            # Prepare the request body (convert dictionary to JSON format)
            body_data = self._prepare_body(body)

            # Send the POST request with headers and timeout settings
            response = self.session.post(url, headers=headers or self.default_headers,
                                         data=body_data, timeout=timeout, verify=self.ssl_enabled)

            # Raise an error for HTTP status codes in the 4xx and 5xx range
            response.raise_for_status()
            return response

        except requests.exceptions.Timeout:
            # Handle timeout errors when the server takes too long to respond
            raise RuntimeError(f"⏳ Request Timeout: POST {url} exceeded {timeout} seconds.")
        except requests.exceptions.ConnectionError:
            # Handle network-related errors (e.g., no internet, server down)
            raise RuntimeError(f"❌ Connection Error: Unable to reach {url}. Check network or server status.")
        except requests.exceptions.RequestException as e:
            # Handle any other unexpected request failures
            raise RuntimeError(f"🚨 Unexpected Error in POST {url}: {str(e)}") from e

    def restapi_get(self, url: str, timeout: int = 60) -> requests.Response:
        """
        Sends a synchronous GET request.

        This method performs an HTTP GET request to the specified URL.
        It includes error handling for common HTTP issues such as timeouts,
        connection failures, and HTTP response errors.

        Args:
            url (str): The endpoint URL to send the request to.
            timeout (int): The maximum time (in seconds) to wait for a response before timing out. Default is 60 seconds.

        Returns:
            requests.Response: The HTTP response object, if the request is successful.

        Raises:
            RuntimeError: Raised in case of network failure, timeout, or HTTP error.
                - `TimeoutError`: If the request exceeds the specified timeout.
                - `ConnectionError`: If the server is unreachable.
                - `RequestException`: For any other unexpected request failure.
        """
        try:
            # Send the GET request with headers and timeout settings
            response = self.session.get(url, headers=self.default_headers, allow_redirects=True,
                                        timeout=timeout, verify=self.ssl_enabled)

            # Raise an error for HTTP status codes in the 4xx and 5xx range
            response.raise_for_status()
            return response

        except requests.exceptions.Timeout:
            # Handle timeout errors when the server takes too long to respond
            raise RuntimeError(f"⏳ Request Timeout: GET {url} exceeded {timeout} seconds.")
        except requests.exceptions.ConnectionError:
            # Handle network-related errors (e.g., no internet, server down)
            raise RuntimeError(f"❌ Connection Error: Unable to reach {url}. Check network or server status.")
        except requests.exceptions.RequestException as e:
            # Handle any other unexpected request failures
            raise RuntimeError(f"🚨 Unexpected Error in GET {url}: {str(e)}") from e

    async def restapi_post_async(self, url: str, body: Any) -> Dict[str, Any]:
        """
        Sends an asynchronous POST request using FastAPI-managed aiohttp session.

        This method performs an HTTP POST request asynchronously.
        It includes error handling for common HTTP issues such as timeouts,
        connection failures, and HTTP response errors.

        Args:
            url (str): The endpoint URL to send the request to.
            body (Any): The request payload (JSON format).

        Returns:
            Dict[str, Any]: The JSON-decoded response body if the request is successful.

        Raises:
            RuntimeError: Raised in case of network failure, timeout, or HTTP error.
                - `TimeoutError`: If the request exceeds the specified timeout.
                - `ClientConnectorError`: If the server is unreachable.
                - `ClientResponseError`: If the server returns an HTTP error response (4xx, 5xx).
                - `Exception`: For any other unexpected failure.
        """
        if RestClient._aio_session is None:
            raise RuntimeError("🚨 aiohttp.ClientSession is not initialized. Ensure FastAPI is running.")

        try:
            # Send an asynchronous POST request using aiohttp session
            async with RestClient._aio_session.post(url, json=body, headers=self.default_headers,
                                                    timeout=120, ssl=self.ssl_enabled) as response:
                # Raise an error for HTTP status codes in the 4xx and 5xx range
                response.raise_for_status()
                return await response.json()

        except aiohttp.ClientResponseError as http_err:
            # Handle HTTP response errors (e.g., 404 Not Found, 500 Internal Server Error)
            raise RuntimeError(f"🔴 HTTP Error: POST {url} returned status {http_err.status} - {http_err.message}")
        except aiohttp.ClientConnectorError:
            # Handle connection errors when the server is unreachable
            raise RuntimeError(f"❌ Connection Error: Unable to reach {url}. Check network or server status.")
        except asyncio.TimeoutError:
            # Handle timeout errors when the server takes too long to respond
            raise RuntimeError(f"⏳ Request Timeout: POST {url} exceeded 120 seconds.")
        except aiohttp.ClientError as e:
            # Handle any other client-side aiohttp error
            raise RuntimeError(f"🚨 Async Client Error in POST {url}: {str(e)}") from e
        except Exception as e:
            # Handle unexpected errors
            raise RuntimeError(f"🚨 Unexpected error during async POST {url}: {str(e)}") from e

    @classmethod
    def set_global_session(cls, session: aiohttp.ClientSession):
        """
        Sets the global aiohttp.ClientSession for asynchronous requests.

        Args:
            session (aiohttp.ClientSession): The aiohttp session instance.
        """
        cls._aio_session = session

    @classmethod
    async def restapi_stream_request_async(cls, url, body_data, headers=None, background_tasks=None):
        session_id = body_data.get('meta', {}).get('session_id', 'unknown')
        logging.info(f"[{session_id}] 스트리밍 요청 시작: {url}")

        req_headers = {
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream'
        }
        if headers:
            req_headers.update(headers)

        async def stream_generator():
            try:
                timeout = aiohttp.ClientTimeout(total=7200, connect=120, sock_read=1200, sock_connect=30)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    logging.info(f"[{session_id}] 스트리밍 세션 생성됨")

                    async with session.post(url, json=body_data, headers=req_headers) as response:
                        if response.status != 200:
                            logging.error(f"[{session_id}] 스트리밍 요청 실패: HTTP {response.status}")
                            error_text = await response.text()
                            error_data = {
                                "error": True,
                                "text": f"Server error: {response.status} - {error_text[:100]}",
                                "finished": True
                            }
                            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
                            return

                        logging.info(f"[{session_id}] 스트리밍 연결 성공, 데이터 수신 대기 중")

                        # 디버깅을 위한 카운터
                        chunk_count = 0

                        # SSE 형식 수신 버퍼
                        buffer = ""

                        # 마지막 complete_response 확인 플래그
                        complete_response_received = False

                        # 빈 텍스트 카운트
                        empty_text_count = 0

                        # 청크 처리 개선
                        async for chunk in response.content:
                            if not chunk:
                                continue

                            chunk_count += 1
                            chunk_text = chunk.decode('utf-8')

                            # 버퍼에 추가
                            buffer += chunk_text

                            # 완전한 JSON 객체 검색
                            while buffer.strip():
                                # 1. data: 접두사 확인
                                if buffer.lstrip().startswith('data: '):
                                    # SSE 형식의 데이터
                                    if '\n\n' in buffer:
                                        # 완전한 SSE 이벤트 발견
                                        parts = buffer.split('\n\n', 1)
                                        event = parts[0].strip()
                                        buffer = parts[1]

                                        # data: 부분 추출
                                        event_data = event[6:].strip()  # 'data: ' 제거

                                        try:
                                            # JSON 파싱 시도
                                            json_obj = json.loads(event_data)

                                            # 1. complete_response 확인
                                            if "complete_response" in json_obj:
                                                complete_response_received = True
                                                yield f"data: {event_data}\n\n"
                                                continue

                                            # 2. 빈 텍스트 필터링
                                            if json_obj.get("text", "") == "" and json_obj.get("finished", False):
                                                # 마지막 종료 신호이고 complete_response를 이미 받았으면 무시
                                                if complete_response_received:
                                                    continue

                                                # 마지막 종료 신호는 한 번만 보냄
                                                empty_text_count += 1
                                                if empty_text_count > 1:
                                                    continue

                                            # 유효한 데이터 전송
                                            yield f"data: {event_data}\n\n"
                                            logging.debug(f"[{session_id}] 이벤트 전송: {event_data[:50]}...")
                                        except json.JSONDecodeError:
                                            # JSON이 아니지만 SSE 형식이면 그대로 전달
                                            yield f"data: {event_data}\n\n"
                                    else:
                                        # 불완전한 이벤트, 더 많은 데이터 대기
                                        break
                                else:
                                    # 2. 일반 JSON 데이터
                                    try:
                                        # JSON 객체를 찾기 위한 시도
                                        json_str = buffer.strip()
                                        json_obj = json.loads(json_str)

                                        # complete_response 확인
                                        if "complete_response" in json_obj:
                                            complete_response_received = True
                                            yield f"data: {json_str}\n\n"
                                            buffer = ""
                                            continue

                                        # 빈 텍스트 필터링
                                        if json_obj.get("text", "") == "" and json_obj.get("finished", False):
                                            # 마지막 종료 신호이고 complete_response를 이미 받았으면 무시
                                            if complete_response_received:
                                                buffer = ""
                                                continue

                                            # 마지막 종료 신호는 한 번만 보냄
                                            empty_text_count += 1
                                            if empty_text_count > 1:
                                                buffer = ""
                                                continue

                                        # 유효한 데이터 전송
                                        yield f"data: {json_str}\n\n"
                                        buffer = ""
                                    except json.JSONDecodeError:
                                        # JSON 파싱 실패, 더 많은 데이터가 필요하거나 형식이 잘못됨
                                        if len(buffer) > 1024:
                                            # 버퍼가 너무 크면 텍스트로 전송하고 비움
                                            if buffer.strip():  # 비어있지 않은 경우만
                                                yield f"data: {json.dumps({'text': buffer.strip()}, ensure_ascii=False)}\n\n"
                                            buffer = ""
                                        break

                        # 남은 버퍼 처리 (비어있지 않은 경우만)
                        if buffer.strip():
                            try:
                                json_obj = json.loads(buffer.strip())

                                # complete_response 또는 빈 텍스트 종료 신호 필터링
                                if not ("complete_response" in json_obj or
                                        (json_obj.get("text", "") == "" and json_obj.get("finished", False) and
                                         (complete_response_received or empty_text_count > 0))):
                                    yield f"data: {json.dumps(json_obj, ensure_ascii=False)}\n\n"
                            except json.JSONDecodeError:
                                # JSON이 아니고 비어있지 않은 경우만 전송
                                if buffer.strip():
                                    yield f"data: {json.dumps({'text': buffer.strip()}, ensure_ascii=False)}\n\n"

                        # 종료 이벤트는 complete_response를 받지 않았고 아직 보내지 않은 경우에만 전송
                        if not complete_response_received and empty_text_count == 0:
                            logging.info(f"[{session_id}] 종료 이벤트 전송")
                            yield f"data: {json.dumps({'text': '', 'finished': True}, ensure_ascii=False)}\n\n"

                        logging.info(f"[{session_id}] 모든 청크({chunk_count}개) 처리 완료")

            except Exception as e:
                logging.error(f"[{session_id}] 스트리밍 오류: {str(e)}", exc_info=True)
                error_data = {
                    "error": True,
                    "text": f"스트리밍 오류: {str(e)}",
                    "finished": True
                }
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream; charset=utf-8",
            headers={
                "Cache-Control": "no-cache, no-transform",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )


# ================================
#       Global Instance
# ================================

# Initialize a global RestClient instance
rc = RestClient()
