"""
Google OAuth Connector
Implements OAuth 2.0 for Google Drive and Gmail
"""
from typing import Dict, Optional, Any
from urllib.parse import urlencode
import httpx

from .base import BaseOAuthConnector


class GoogleConnector(BaseOAuthConnector):
    """
    Google OAuth 2.0 connector for Drive and Gmail

    Implements the Google OAuth 2.0 flow:
    https://developers.google.com/identity/protocols/oauth2/web-server

    Scopes for Google Drive:
    - https://www.googleapis.com/auth/drive.readonly: Read-only access to Drive files
    - https://www.googleapis.com/auth/drive.metadata.readonly: Read file metadata

    Scopes for Gmail:
    - https://www.googleapis.com/auth/gmail.readonly: Read-only access to Gmail
    - https://www.googleapis.com/auth/gmail.metadata: Read email metadata
    """

    @property
    def provider_name(self) -> str:
        return "google"

    @property
    def authorization_base_url(self) -> str:
        return "https://accounts.google.com/o/oauth2/v2/auth"

    @property
    def token_url(self) -> str:
        return "https://oauth2.googleapis.com/token"

    async def get_authorization_url(
        self,
        state: str,
        code_challenge: Optional[str] = None
    ) -> str:
        """
        Generate Google OAuth authorization URL with PKCE support

        Args:
            state: CSRF protection state parameter
            code_challenge: PKCE code challenge (optional)

        Returns:
            Full authorization URL to redirect user to
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "state": state,
            "scope": " ".join(self.scopes),
            "access_type": "offline",  # Request refresh token
            "prompt": "consent",  # Force consent screen to get refresh token
        }

        # Add PKCE parameters if provided
        if code_challenge:
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = "S256"

        return f"{self.authorization_base_url}?{urlencode(params)}"

    async def exchange_code_for_tokens(
        self,
        code: str,
        state: Optional[str] = None,
        code_verifier: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for access and refresh tokens with PKCE support

        Args:
            code: Authorization code from OAuth callback
            state: State parameter (not used in token exchange)
            code_verifier: PKCE code verifier (optional)

        Returns:
            Dictionary containing:
                - access_token: Access token
                - refresh_token: Refresh token
                - expires_in: Token expiration in seconds (usually 3600)
                - token_type: 'Bearer'
                - scope: Granted scopes
        """
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
        }

        # Add PKCE code_verifier if provided
        if code_verifier:
            data["code_verifier"] = code_verifier

        try:
            response = await self.http_client.post(
                self.token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()

            token_data = response.json()

            # Google tokens typically expire in 1 hour
            if "expires_in" not in token_data:
                token_data["expires_in"] = 3600

            return token_data

        except httpx.HTTPStatusError as e:
            error_detail = e.response.json() if e.response.content else {}
            raise Exception(
                f"Failed to exchange code for tokens: {error_detail.get('error_description', str(e))}"
            )
        except Exception as e:
            raise Exception(f"Failed to exchange code for tokens: {str(e)}")

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh expired access token using refresh token

        Args:
            refresh_token: Valid refresh token

        Returns:
            Dictionary containing new access_token and expires_in
        """
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }

        try:
            response = await self.http_client.post(
                self.token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()

            token_data = response.json()

            if "expires_in" not in token_data:
                token_data["expires_in"] = 3600

            return token_data

        except httpx.HTTPStatusError as e:
            error_detail = e.response.json() if e.response.content else {}
            raise Exception(
                f"Failed to refresh access token: {error_detail.get('error_description', str(e))}"
            )
        except Exception as e:
            raise Exception(f"Failed to refresh access token: {str(e)}")

    async def test_connection(self, access_token: str) -> bool:
        """
        Test if the connection works with given access token
        Uses the Google userinfo endpoint

        Args:
            access_token: Access token to test

        Returns:
            True if connection is valid, False otherwise
        """
        try:
            await self.get_user_info(access_token)
            return True
        except Exception:
            return False

    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get user information from Google

        Uses the Google OAuth2 userinfo endpoint

        Args:
            access_token: Valid access token

        Returns:
            Dictionary containing:
                - id: User's Google ID
                - email: User's email address
                - verified_email: Whether email is verified
                - name: User's full name
                - given_name: First name
                - family_name: Last name
                - picture: Profile picture URL
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
        }

        try:
            response = await self.http_client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers=headers
            )
            response.raise_for_status()

            data = response.json()

            return {
                "id": data.get("id"),
                "email": data.get("email"),
                "verified_email": data.get("verified_email"),
                "name": data.get("name"),
                "given_name": data.get("given_name"),
                "family_name": data.get("family_name"),
                "picture": data.get("picture"),
            }

        except httpx.HTTPStatusError as e:
            error_detail = e.response.json() if e.response.content else {}
            raise Exception(
                f"Failed to get user info: {error_detail.get('error_description', str(e))}"
            )
        except Exception as e:
            raise Exception(f"Failed to get user info: {str(e)}")

    async def revoke_token(self, access_token: str) -> bool:
        """
        Revoke an access token (disconnect)

        Args:
            access_token: Token to revoke

        Returns:
            True if revocation succeeded
        """
        try:
            response = await self.http_client.post(
                f"https://oauth2.googleapis.com/revoke?token={access_token}",
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            return response.status_code == 200
        except Exception:
            return False
