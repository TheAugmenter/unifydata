"""
Notion OAuth Connector
Implements OAuth 2.0 for Notion Integrations
"""
from typing import Dict, Optional, Any
from urllib.parse import urlencode
import httpx

from .base import BaseOAuthConnector


class NotionConnector(BaseOAuthConnector):
    """
    Notion OAuth 2.0 connector

    Implements the Notion OAuth flow:
    https://developers.notion.com/docs/authorization

    Notion uses a simplified OAuth flow without explicit scopes.
    Access is granted at the workspace level, and the integration
    can only access pages/databases that are explicitly shared with it.
    """

    @property
    def provider_name(self) -> str:
        return "notion"

    @property
    def authorization_base_url(self) -> str:
        return "https://api.notion.com/v1/oauth/authorize"

    @property
    def token_url(self) -> str:
        return "https://api.notion.com/v1/oauth/token"

    async def get_authorization_url(
        self,
        state: str,
        code_challenge: Optional[str] = None
    ) -> str:
        """
        Generate Notion OAuth authorization URL with PKCE support

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
            "owner": "user",  # Request user-level access
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
        Exchange authorization code for access token with PKCE support

        Args:
            code: Authorization code from OAuth callback
            state: State parameter (not used in token exchange)
            code_verifier: PKCE code verifier (optional)

        Returns:
            Dictionary containing:
                - access_token: Access token
                - token_type: 'bearer'
                - bot_id: Bot/integration ID
                - workspace_name: Workspace name
                - workspace_icon: Workspace icon URL
                - workspace_id: Workspace ID
                - owner: Owner info (user or workspace)
        """
        # Notion requires Basic Auth for token exchange
        auth = (self.client_id, self.client_secret)

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
        }

        # Add PKCE code_verifier if provided
        if code_verifier:
            data["code_verifier"] = code_verifier

        try:
            response = await self.http_client.post(
                self.token_url,
                json=data,  # Notion expects JSON, not form data
                auth=auth,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

            token_data = response.json()

            # Notion tokens don't expire
            if "expires_in" not in token_data:
                token_data["expires_in"] = 315360000  # 10 years (effectively permanent)

            return token_data

        except httpx.HTTPStatusError as e:
            error_detail = e.response.json() if e.response.content else {}
            raise Exception(
                f"Failed to exchange code for tokens: {error_detail.get('message', str(e))}"
            )
        except Exception as e:
            raise Exception(f"Failed to exchange code for tokens: {str(e)}")

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Notion tokens don't expire, so refresh is not needed

        Args:
            refresh_token: Not used (Notion doesn't provide refresh tokens)

        Returns:
            Empty dict (not applicable for Notion)
        """
        raise NotImplementedError("Notion tokens don't expire and cannot be refreshed")

    async def test_connection(self, access_token: str) -> bool:
        """
        Test if the connection works with given access token
        Uses the Notion users/me endpoint

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
        Get user/bot information from Notion

        Uses the Notion users/me endpoint

        Args:
            access_token: Valid access token

        Returns:
            Dictionary containing:
                - id: Bot/user ID
                - type: 'person' or 'bot'
                - name: Bot/user name
                - avatar_url: Avatar URL
                - object: 'user'
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Notion-Version": "2022-06-28",  # Notion requires API version
        }

        try:
            response = await self.http_client.get(
                "https://api.notion.com/v1/users/me",
                headers=headers
            )
            response.raise_for_status()

            data = response.json()

            return {
                "id": data.get("id"),
                "type": data.get("type"),
                "name": data.get("name"),
                "avatar_url": data.get("avatar_url"),
                "object": data.get("object"),
            }

        except httpx.HTTPStatusError as e:
            error_detail = e.response.json() if e.response.content else {}
            raise Exception(
                f"Failed to get user info: {error_detail.get('message', str(e))}"
            )
        except Exception as e:
            raise Exception(f"Failed to get user info: {str(e)}")

    async def revoke_token(self, access_token: str) -> bool:
        """
        Notion doesn't provide a token revocation endpoint
        Tokens can only be revoked manually from the Notion UI

        Args:
            access_token: Token to revoke (not used)

        Returns:
            False (manual revocation required)
        """
        # Notion doesn't support programmatic token revocation
        # Users must revoke access from their Notion settings
        return False
