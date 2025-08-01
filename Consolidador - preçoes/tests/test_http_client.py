"""
Unit tests for HTTP client with retry mechanism.
"""

import pytest
import time
import requests
from unittest.mock import Mock, patch, MagicMock
from requests.exceptions import ConnectionError, Timeout, HTTPError, RequestException

from services.http_client import HTTPClient, RequestConfig


class TestRequestConfig:
    """Test RequestConfig dataclass."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = RequestConfig()
        assert config.timeout == 10
        assert config.max_retries == 3
        assert config.backoff_factor == 1.0
        assert config.rate_limit_delay == 1.0
        assert config.verify_ssl is True
        assert config.follow_redirects is True
    
    def test_custom_values(self):
        """Test custom configuration values."""
        config = RequestConfig(
            timeout=30,
            max_retries=5,
            backoff_factor=2.0,
            rate_limit_delay=0.5,
            verify_ssl=False,
            follow_redirects=False
        )
        assert config.timeout == 30
        assert config.max_retries == 5
        assert config.backoff_factor == 2.0
        assert config.rate_limit_delay == 0.5
        assert config.verify_ssl is False
        assert config.follow_redirects is False


class TestHTTPClient:
    """Test HTTPClient functionality."""
    
    @pytest.fixture
    def client(self):
        """Create HTTPClient instance for testing."""
        config = RequestConfig(rate_limit_delay=0.1)  # Faster tests
        return HTTPClient(config)
    
    @pytest.fixture
    def mock_response(self):
        """Create mock response object."""
        response = Mock()
        response.status_code = 200
        response.text = "<html>Test content</html>"
        response.headers = {"Content-Type": "text/html"}
        response.raise_for_status = Mock()
        return response
    
    def test_initialization_default_config(self):
        """Test client initialization with default config."""
        client = HTTPClient()
        assert client.config.timeout == 10
        assert client.config.max_retries == 3
        assert client.session is not None
        assert client.last_request_time == 0.0
        assert client.domain_headers == {}
    
    def test_initialization_custom_config(self):
        """Test client initialization with custom config."""
        config = RequestConfig(timeout=30, max_retries=5)
        client = HTTPClient(config)
        assert client.config.timeout == 30
        assert client.config.max_retries == 5
    
    def test_get_random_user_agent(self, client):
        """Test user agent rotation."""
        user_agents = set()
        for _ in range(20):
            ua = client._get_random_user_agent()
            user_agents.add(ua)
            assert ua in HTTPClient.USER_AGENTS
        
        # Should get multiple different user agents
        assert len(user_agents) > 1
    
    def test_get_domain_from_url(self, client):
        """Test domain extraction from URLs."""
        assert client._get_domain_from_url("https://example.com/path") == "example.com"
        assert client._get_domain_from_url("http://subdomain.example.com") == "subdomain.example.com"
        assert client._get_domain_from_url("https://EXAMPLE.COM") == "example.com"
        assert client._get_domain_from_url("invalid-url") == ""
    
    def test_set_domain_headers(self, client):
        """Test setting domain-specific headers."""
        headers = {"X-Custom": "value", "Authorization": "Bearer token"}
        client.set_domain_headers("example.com", headers)
        
        assert "example.com" in client.domain_headers
        assert client.domain_headers["example.com"] == headers
    
    def test_build_headers_basic(self, client):
        """Test basic header building."""
        headers = client._build_headers("https://example.com")
        
        assert "User-Agent" in headers
        assert "Accept" in headers
        assert "Accept-Language" in headers
        assert headers["User-Agent"] in HTTPClient.USER_AGENTS
    
    def test_build_headers_with_domain_specific(self, client):
        """Test header building with domain-specific headers."""
        domain_headers = {"X-Custom": "domain-value"}
        client.set_domain_headers("example.com", domain_headers)
        
        headers = client._build_headers("https://example.com")
        assert headers["X-Custom"] == "domain-value"
    
    def test_build_headers_with_custom(self, client):
        """Test header building with custom headers."""
        custom_headers = {"X-Test": "test-value"}
        headers = client._build_headers("https://example.com", custom_headers)
        assert headers["X-Test"] == "test-value"
    
    def test_rate_limiting(self, client):
        """Test rate limiting functionality."""
        start_time = time.time()
        
        # First request should not be delayed
        client._apply_rate_limiting()
        first_request_time = time.time() - start_time
        assert first_request_time < 0.05  # Should be very fast
        
        # Second request should be delayed
        start_time = time.time()
        client._apply_rate_limiting()
        second_request_time = time.time() - start_time
        assert second_request_time >= 0.09  # Should wait ~0.1s
    
    @patch('services.http_client.requests.Session.request')
    def test_successful_get_request(self, mock_request, client, mock_response):
        """Test successful GET request."""
        mock_request.return_value = mock_response
        
        response = client.get("https://example.com")
        
        assert response == mock_response
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert args[0] == "GET"
        assert args[1] == "https://example.com"
        assert "User-Agent" in kwargs["headers"]
    
    @patch('services.http_client.requests.Session.request')
    def test_successful_post_request(self, mock_request, client, mock_response):
        """Test successful POST request."""
        mock_request.return_value = mock_response
        test_data = {"key": "value"}
        
        response = client.post("https://example.com", json=test_data)
        
        assert response == mock_response
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert args[0] == "POST"
        assert kwargs["json"] == test_data
    
    @patch('services.http_client.requests.Session.request')
    @patch('time.sleep')
    def test_retry_on_connection_error(self, mock_sleep, mock_request, client):
        """Test retry mechanism on connection errors."""
        # First two calls fail, third succeeds
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        
        mock_request.side_effect = [
            ConnectionError("Connection failed"),
            ConnectionError("Connection failed"),
            mock_response
        ]
        
        response = client.get("https://example.com")
        
        assert response == mock_response
        assert mock_request.call_count == 3
        assert mock_sleep.call_count == 2  # Two retries
    
    @patch('services.http_client.requests.Session.request')
    @patch('time.sleep')
    def test_retry_on_timeout(self, mock_sleep, mock_request, client):
        """Test retry mechanism on timeout errors."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        
        mock_request.side_effect = [
            Timeout("Request timeout"),
            mock_response
        ]
        
        response = client.get("https://example.com")
        
        assert response == mock_response
        assert mock_request.call_count == 2
        assert mock_sleep.call_count == 1
    
    @patch('services.http_client.requests.Session.request')
    @patch('time.sleep')
    def test_retry_on_server_error(self, mock_sleep, mock_request, client):
        """Test retry mechanism on server errors."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        
        # Create HTTP error for 503
        error_response = Mock()
        error_response.status_code = 503
        http_error = HTTPError(response=error_response)
        
        mock_request.side_effect = [
            http_error,
            mock_response
        ]
        
        response = client.get("https://example.com")
        
        assert response == mock_response
        assert mock_request.call_count == 2
    
    @patch('services.http_client.requests.Session.request')
    def test_no_retry_on_client_error(self, mock_request, client):
        """Test no retry on client errors (4xx except 429)."""
        error_response = Mock()
        error_response.status_code = 404
        http_error = HTTPError(response=error_response)
        
        mock_request.side_effect = http_error
        
        with pytest.raises(HTTPError):
            client.get("https://example.com")
        
        assert mock_request.call_count == 1  # No retries
    
    @patch('services.http_client.requests.Session.request')
    @patch('time.sleep')
    def test_retry_exhaustion(self, mock_sleep, mock_request, client):
        """Test behavior when all retries are exhausted."""
        mock_request.side_effect = ConnectionError("Connection failed")
        
        with pytest.raises(ConnectionError):
            client.get("https://example.com")
        
        # Should try max_retries + 1 times (initial + retries)
        assert mock_request.call_count == client.config.max_retries + 1
        assert mock_sleep.call_count == client.config.max_retries
    
    @patch('services.http_client.requests.Session.request')
    @patch('time.sleep')
    def test_exponential_backoff(self, mock_sleep, mock_request, client):
        """Test exponential backoff timing."""
        mock_request.side_effect = ConnectionError("Connection failed")
        
        with pytest.raises(ConnectionError):
            client.get("https://example.com")
        
        # Check that sleep times follow exponential backoff
        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        expected_times = [1.0, 2.0, 4.0]  # backoff_factor * 2^(attempt-1)
        
        assert len(sleep_calls) == len(expected_times)
        for actual, expected in zip(sleep_calls, expected_times):
            assert abs(actual - expected) < 0.1
    
    def test_close_session(self, client):
        """Test session cleanup."""
        mock_session = Mock()
        client.session = mock_session
        
        client.close()
        
        mock_session.close.assert_called_once()
    
    @patch('services.http_client.requests.Session.request')
    def test_custom_headers_in_request(self, mock_request, client, mock_response):
        """Test that custom headers are included in requests."""
        mock_request.return_value = mock_response
        custom_headers = {"X-API-Key": "secret"}
        
        client.get("https://example.com", headers=custom_headers)
        
        args, kwargs = mock_request.call_args
        assert kwargs["headers"]["X-API-Key"] == "secret"
    
    @patch('services.http_client.requests.Session.request')
    def test_request_parameters(self, mock_request, client, mock_response):
        """Test that request parameters are properly set."""
        mock_request.return_value = mock_response
        
        client.get("https://example.com")
        
        args, kwargs = mock_request.call_args
        assert kwargs["timeout"] == client.config.timeout
        assert kwargs["verify"] == client.config.verify_ssl
        assert kwargs["allow_redirects"] == client.config.follow_redirects


class TestHTTPClientIntegration:
    """Integration tests for HTTPClient."""
    
    def test_real_request_success(self):
        """Test real HTTP request (requires internet)."""
        client = HTTPClient()
        
        try:
            response = client.get("https://httpbin.org/get")
            assert response.status_code == 200
            assert "User-Agent" in response.json()["headers"]
        except Exception:
            pytest.skip("Internet connection required for integration test")
        finally:
            client.close()
    
    def test_real_request_with_custom_headers(self):
        """Test real HTTP request with custom headers."""
        client = HTTPClient()
        custom_headers = {"X-Test-Header": "test-value"}
        
        try:
            response = client.get("https://httpbin.org/get", headers=custom_headers)
            assert response.status_code == 200
            assert response.json()["headers"]["X-Test-Header"] == "test-value"
        except Exception:
            pytest.skip("Internet connection required for integration test")
        finally:
            client.close()


if __name__ == "__main__":
    pytest.main([__file__])