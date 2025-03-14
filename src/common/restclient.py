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
        """
        Make an asynchronous POST request to a streaming API endpoint and return the StreamingResponse.

        Enhanced with better error handling and recovery mechanisms for connection issues.

        Args:
            url (str): The URL to send the request to
            body_data (dict): The request body data
            headers (dict, optional): Additional headers to include
            background_tasks (BackgroundTasks, optional): FastAPI background tasks manager

        Returns:
            StreamingResponse: The streaming response from the upstream service
        """
        session_id = body_data.get('meta', {}).get('session_id', 'unknown')

        # Prepare headers - 기본 헤더 직접 준비
        if headers is None:
            headers = {}

        # JSON 컨텐츠를 위한 기본 헤더
        req_headers = {
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream'
        }

        # 사용자 지정 헤더 추가
        if headers:
            req_headers.update(headers)

        # 스트리밍 응답을 처리하는 함수
        async def process_streaming_response():
            max_retries = 2
            retry_count = 0

            while retry_count <= max_retries:
                try:
                    # 타임아웃 설정 증가 (연결 유지 시간)
                    timeout = aiohttp.ClientTimeout(
                        total=3600,  # 전체 타임아웃 (1시간)
                        sock_connect=30,  # 소켓 연결 타임아웃
                        sock_read=300  # 소켓 읽기 타임아웃
                    )

                    logging.info(
                        f"[{session_id}] Connecting to streaming endpoint (attempt {retry_count + 1}/{max_retries + 1})")

                    # Connect to the upstream endpoint with TCP keepalive
                    connector = aiohttp.TCPConnector(keepalive_timeout=60)
                    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
                        async with session.post(url, json=body_data, headers=req_headers) as response:
                            # Check if response is successful
                            if response.status != 200:
                                logging.error(f"[{session_id}] Stream request failed with status {response.status}")
                                error_text = await response.text()
                                logging.error(f"[{session_id}] Error response: {error_text[:500]}")

                                async def error_stream():
                                    error_data = {
                                        "error": True,
                                        "text": f"Upstream service error: {response.status} - {error_text[:100] if error_text else 'No details'}",
                                        "finished": True
                                    }
                                    yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"

                                return StreamingResponse(
                                    error_stream(),
                                    media_type="text/event-stream; charset=utf-8"
                                )

                            # Create a buffer to accumulate partial chunks
                            buffer = ""

                            # Create a stream that properly handles SSE format
                            async def stream_response():
                                nonlocal buffer

                                try:
                                    logging.info(
                                        f"[{session_id}] Stream connection established, starting to receive data")

                                    # Process each chunk from the upstream service
                                    async for chunk in response.content:
                                        chunk_text = chunk.decode('utf-8')
                                        logging.error(chunk_text)
                                        buffer += chunk_text

                                        # SSE 형식 처리: data: {...}\n\n 패턴 찾기
                                        while '\n\n' in buffer:
                                            parts = buffer.split('\n\n', 1)
                                            event = parts[0]
                                            buffer = parts[1]

                                            if event.startswith('data: '):
                                                # 완전한 이벤트 찾음, 클라이언트에 전달
                                                yield event + '\n\n'
                                            elif event.strip():
                                                # 알 수 없는 형식의 이벤트이지만 내용이 있음
                                                logging.warning(f"[{session_id}] Unknown event format: {event[:50]}")
                                                # JSON으로 래핑해서 전달
                                                data = {
                                                    "text": event.strip(),
                                                    "finished": False
                                                }
                                                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

                                        # 남은 버퍼가 너무 길면 (불완전한 이벤트) 바로 전송
                                        if len(buffer) > 1024:
                                            data = {
                                                "text": buffer,
                                                "finished": False
                                            }
                                            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                                            buffer = ""

                                    # 스트림 종료 처리
                                    logging.info(f"[{session_id}] Stream completed normally")

                                    # 남은 버퍼 처리
                                    if buffer.strip():
                                        data = {
                                            "text": buffer.strip(),
                                            "finished": False
                                        }
                                        yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

                                    # 완료 신호 전송
                                    data = {
                                        "text": "",
                                        "finished": True
                                    }
                                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

                                except (aiohttp.ClientError, asyncio.CancelledError) as e:
                                    logging.error(f"[{session_id}] Connection error during streaming: {str(e)}")

                                    if 'Connection closed' in str(e):
                                        # 연결이 예기치 않게 닫힌 경우
                                        if buffer.strip():
                                            # 남은 버퍼가 있으면 먼저 전송
                                            data = {
                                                "text": buffer.strip() + "\n\n[연결이 종료되었습니다]",
                                                "finished": False
                                            }
                                            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

                                        # 완료 메시지 전송
                                        data = {
                                            "error": True,
                                            "text": "서버와의 연결이 종료되었습니다. 일부 응답이 누락되었을 수 있습니다.",
                                            "finished": True
                                        }
                                        yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                                    else:
                                        # 기타 클라이언트 오류
                                        data = {
                                            "error": True,
                                            "text": f"스트리밍 오류: {str(e)}",
                                            "finished": True
                                        }
                                        yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                                except Exception as e:
                                    logging.error(f"[{session_id}] Unexpected error in stream processing: {str(e)}",
                                                 exc_info=True)
                                    data = {
                                        "error": True,
                                        "text": f"스트리밍 처리 오류: {str(e)}",
                                        "finished": True
                                    }
                                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

                            # Return the streaming response
                            return StreamingResponse(
                                stream_response(),
                                media_type="text/event-stream; charset=utf-8"
                            )

                except aiohttp.ClientConnectorError as e:
                    logging.error(f"[{session_id}] Connection error: {str(e)}")
                    retry_count += 1

                    if retry_count <= max_retries:
                        # 재시도 전 잠시 대기
                        wait_time = retry_count * 2  # 점진적으로 대기 시간 증가
                        logging.info(f"[{session_id}] Retrying in {wait_time} seconds...")
                        await asyncio.sleep(wait_time)
                    else:
                        # 최대 재시도 횟수 초과
                        async def connection_error_stream():
                            error_data = {
                                "error": True,
                                "text": f"연결 오류 (재시도 실패): {str(e)}",
                                "finished": True
                            }
                            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"

                        return StreamingResponse(
                            connection_error_stream(),
                            media_type="text/event-stream; charset=utf-8"
                        )

                except Exception as e:
                    logging.error(f"[{session_id}] Unexpected error: {str(e)}", exc_info=True)

                    async def general_error_stream():
                        error_data = {
                            "error": True,
                            "text": f"오류: {str(e)}",
                            "finished": True
                        }
                        yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"

                    return StreamingResponse(
                        general_error_stream(),
                        media_type="text/event-stream; charset=utf-8"
                    )

        # 메인 처리 호출
        return await process_streaming_response()


# ================================
#       Global Instance
# ================================

# Initialize a global RestClient instance
rc = RestClient()
