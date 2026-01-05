"""Tests for system invocation."""

import httpx
import pytest
from pytest_httpx import HTTPXMock

from engine.systems import SystemConfig, invoke_case, InvokeError


class TestSystemConfig:
    """Tests for SystemConfig model."""
    
    def test_valid_config(self):
        """Create a valid system config."""
        config = SystemConfig(name="test_system", endpoint="http://localhost:8000/api")
        assert config.name == "test_system"
        assert config.endpoint == "http://localhost:8000/api"
    
    def test_empty_name_rejected(self):
        """Empty name is rejected."""
        with pytest.raises(ValueError):
            SystemConfig(name="", endpoint="http://localhost:8000")
    
    def test_empty_endpoint_rejected(self):
        """Empty endpoint is rejected."""
        with pytest.raises(ValueError):
            SystemConfig(name="test", endpoint="")


class TestInvokeCase:
    """Tests for invoke_case function."""
    
    # --- Successful invocations ---
    
    def test_successful_json_response(self, httpx_mock: HTTPXMock):
        """Successfully invoke and parse JSON response."""
        httpx_mock.add_response(json={"answer": "4"})
        
        system = SystemConfig(name="test", endpoint="http://test.local/solve")
        result = invoke_case(system, {"question": "What is 2+2?"})
        
        assert result == {"answer": "4"}
    
    def test_sends_post_request(self, httpx_mock: HTTPXMock):
        """Sends a POST request with JSON body."""
        httpx_mock.add_response(json={"result": "ok"})
        
        system = SystemConfig(name="test", endpoint="http://test.local/api")
        invoke_case(system, {"input": "data"})
        
        request = httpx_mock.get_request()
        assert request.method == "POST"
        assert request.headers["content-type"] == "application/json"
    
    def test_returns_complex_json(self, httpx_mock: HTTPXMock):
        """Returns complex nested JSON structures."""
        response_data = {
            "result": {
                "answer": "42",
                "confidence": 0.95,
                "metadata": {"model": "gpt-4"}
            }
        }
        httpx_mock.add_response(json=response_data)
        
        system = SystemConfig(name="test", endpoint="http://test.local/api")
        result = invoke_case(system, {})
        
        assert result == response_data
    
    def test_returns_array_response(self, httpx_mock: HTTPXMock):
        """Returns array JSON response."""
        httpx_mock.add_response(json=[1, 2, 3])
        
        system = SystemConfig(name="test", endpoint="http://test.local/api")
        result = invoke_case(system, {})
        
        assert result == [1, 2, 3]
    
    # --- HTTP errors ---
    
    def test_http_404_error(self, httpx_mock: HTTPXMock):
        """404 response raises http_error with status."""
        httpx_mock.add_response(status_code=404)
        
        system = SystemConfig(name="test", endpoint="http://test.local/missing")
        
        with pytest.raises(InvokeError) as exc_info:
            invoke_case(system, {})
        
        assert exc_info.value.code == "http_error"
        assert exc_info.value.http_status == 404
        assert "404" in exc_info.value.message
    
    def test_http_500_error(self, httpx_mock: HTTPXMock):
        """500 response raises http_error with status."""
        httpx_mock.add_response(status_code=500)
        
        system = SystemConfig(name="test", endpoint="http://test.local/api")
        
        with pytest.raises(InvokeError) as exc_info:
            invoke_case(system, {})
        
        assert exc_info.value.code == "http_error"
        assert exc_info.value.http_status == 500
    
    def test_http_400_error(self, httpx_mock: HTTPXMock):
        """400 response raises http_error."""
        httpx_mock.add_response(status_code=400)
        
        system = SystemConfig(name="test", endpoint="http://test.local/api")
        
        with pytest.raises(InvokeError) as exc_info:
            invoke_case(system, {})
        
        assert exc_info.value.code == "http_error"
        assert exc_info.value.http_status == 400
    
    # --- Invalid JSON ---
    
    def test_invalid_json_response(self, httpx_mock: HTTPXMock):
        """Non-JSON response raises invalid_json error."""
        httpx_mock.add_response(text="This is not JSON", status_code=200)
        
        system = SystemConfig(name="test", endpoint="http://test.local/api")
        
        with pytest.raises(InvokeError) as exc_info:
            invoke_case(system, {})
        
        assert exc_info.value.code == "invalid_json"
        assert exc_info.value.http_status is None
        assert "not valid JSON" in exc_info.value.message
    
    def test_empty_response_invalid_json(self, httpx_mock: HTTPXMock):
        """Empty response body raises invalid_json error."""
        httpx_mock.add_response(text="", status_code=200)
        
        system = SystemConfig(name="test", endpoint="http://test.local/api")
        
        with pytest.raises(InvokeError) as exc_info:
            invoke_case(system, {})
        
        assert exc_info.value.code == "invalid_json"
    
    def test_html_response_invalid_json(self, httpx_mock: HTTPXMock):
        """HTML response raises invalid_json error."""
        httpx_mock.add_response(text="<html><body>Error</body></html>", status_code=200)
        
        system = SystemConfig(name="test", endpoint="http://test.local/api")
        
        with pytest.raises(InvokeError) as exc_info:
            invoke_case(system, {})
        
        assert exc_info.value.code == "invalid_json"
    
    # --- Error attributes ---
    
    def test_error_includes_endpoint(self, httpx_mock: HTTPXMock):
        """Error message includes the endpoint URL."""
        httpx_mock.add_response(status_code=500)
        
        system = SystemConfig(name="test", endpoint="http://test.local/specific-endpoint")
        
        with pytest.raises(InvokeError) as exc_info:
            invoke_case(system, {})
        
        assert "test.local/specific-endpoint" in exc_info.value.message
    
    def test_http_error_without_status_for_connection_errors(self, httpx_mock: HTTPXMock):
        """Connection errors have http_error code but no status."""
        # Use httpx.ConnectError to simulate connection failure
        httpx_mock.add_exception(httpx.ConnectError("Connection refused"))
        
        system = SystemConfig(name="test", endpoint="http://nonexistent.local/api")
        
        with pytest.raises(InvokeError) as exc_info:
            invoke_case(system, {})
        
        # Connection errors are http_error with no status
        assert exc_info.value.code == "http_error"
        assert exc_info.value.http_status is None
    
    # --- Timeout ---
    
    def test_timeout_error(self, httpx_mock: HTTPXMock):
        """Timeout raises timeout error."""
        httpx_mock.add_exception(httpx.TimeoutException("Read timed out"))
        
        system = SystemConfig(name="test", endpoint="http://test.local/api")
        
        with pytest.raises(InvokeError) as exc_info:
            invoke_case(system, {})
        
        assert exc_info.value.code == "timeout"
        assert exc_info.value.http_status is None
        assert "timed out" in exc_info.value.message

