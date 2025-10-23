"""
Base OAuth Connector
Abstract base class for all OAuth-based data source connectors
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import httpx


class BaseOAuthConnector(ABC):
    """
    Abstract base class for OAuth 2.0 connectors

    Each connector must implement:
    - get_authorization_url(): Returns OAuth authorization URL
    - exchange_code_for_tokens(): Exchanges auth code for access/refresh tokens
    - refresh_access_token(): Refreshes expired access token
    - test_connection(): Tests if credentials work
    - get_user_info(): Gets user info from the connected account
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        scopes: list[str]
    ):
        """
        Initialize OAuth connector

        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            redirect_uri: OAuth callback URL
            scopes: List of OAuth scopes to request
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scopes = scopes
        self.http_client = httpx.AsyncClient(timeout=30.0)

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the OAuth provider (e.g., 'salesforce', 'slack')"""
        pass

    @property
    @abstractmethod
    def authorization_base_url(self) -> str:
        """OAuth authorization endpoint URL"""
        pass

    @property
    @abstractmethod
    def token_url(self) -> str:
        """OAuth token exchange endpoint URL"""
        pass

    @abstractmethod
    async def get_authorization_url(self, state: str) -> str:
        """
        Generate OAuth authorization URL

        Args:
            state: CSRF protection state parameter

        Returns:
            Full authorization URL to redirect user to
        """
        pass

    @abstractmethod
    async def exchange_code_for_tokens(
        self,
        code: str,
        state: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for access and refresh tokens

        Args:
            code: Authorization code from OAuth callback
            state: State parameter for CSRF validation

        Returns:
            Dictionary containing:
                - access_token: Access token
                - refresh_token: Refresh token (if available)
                - expires_in: Token expiration in seconds
                - token_type: Token type (usually 'Bearer')
                - scope: Granted scopes
                - [provider-specific fields]
        """
        pass

    @abstractmethod
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh expired access token using refresh token

        Args:
            refresh_token: Valid refresh token

        Returns:
            Dictionary containing new access_token and expires_in
        """
        pass

    @abstractmethod
    async def test_connection(self, access_token: str) -> bool:
        """
        Test if the connection works with given access token

        Args:
            access_token: Access token to test

        Returns:
            True if connection is valid, False otherwise
        """
        pass

    @abstractmethod
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get user information from the connected account

        Args:
            access_token: Valid access token

        Returns:
            Dictionary containing user info (email, name, etc.)
        """
        pass

    def calculate_token_expiry(self, expires_in: int) -> datetime:
        """
        Calculate token expiration timestamp

        Args:
            expires_in: Seconds until token expires

        Returns:
            Datetime when token will expire
        """
        return datetime.utcnow() + timedelta(seconds=expires_in)

    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
