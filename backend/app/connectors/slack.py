"""
Slack OAuth Connector
Implements OAuth 2.0 for Slack Workspace Apps
"""
from typing import Dict, Optional, Any
from urllib.parse import urlencode
import httpx

from .base import BaseOAuthConnector


class SlackConnector(BaseOAuthConnector):
    """
    Slack OAuth 2.0 connector

    Implements the Slack OAuth 2.0 flow:
    https://api.slack.com/authentication/oauth-v2

    Scopes:
    - channels:history: View messages in public channels
    - channels:read: View basic channel info
    - files:read: View files shared in channels
    - search:read: Search workspace content
    - users:read: View people in workspace
    """

    @property
    def provider_name(self) -> str:
        return "slack"

    @property
    def authorization_base_url(self) -> str:
        return "https://slack.com/oauth/v2/authorize"

    @property
    def token_url(self) -> str:
        return "https://slack.com/api/oauth.v2.access"

    async def get_authorization_url(
        self,
        state: str,
        code_challenge: Optional[str] = None
    ) -> str:
        """
        Generate Slack OAuth authorization URL with PKCE support

        Args:
            state: CSRF protection state parameter
            code_challenge: PKCE code challenge (optional)

        Returns:
            Full authorization URL to redirect user to
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": state,
            "scope": ",".join(self.scopes),
            "user_scope": "",  # No user-level scopes needed
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
                - access_token: Bot access token
                - token_type: 'Bearer'
                - scope: Granted scopes
                - bot_user_id: Bot user ID
                - team: Team/workspace info
                - authed_user: Authenticated user info
        """
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
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

            if not token_data.get("ok"):
                raise Exception(f"Slack API error: {token_data.get('error', 'Unknown error')}")

            # Slack tokens don't expire (unless revoked)
            if "expires_in" not in token_data:
                token_data["expires_in"] = 315360000  # 10 years (effectively permanent)

            return token_data

        except httpx.HTTPStatusError as e:
            error_detail = e.response.json() if e.response.content else {}
            raise Exception(
                f"Failed to exchange code for tokens: {error_detail.get('error', str(e))}"
            )
        except Exception as e:
            raise Exception(f"Failed to exchange code for tokens: {str(e)}")

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Slack tokens don't expire, so refresh is not needed

        Args:
            refresh_token: Not used (Slack doesn't provide refresh tokens)

        Returns:
            Empty dict (not applicable for Slack)
        """
        raise NotImplementedError("Slack tokens don't expire and cannot be refreshed")

    async def test_connection(self, access_token: str) -> bool:
        """
        Test if the connection works with given access token
        Uses the Slack auth.test endpoint

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
        Get workspace and user information from Slack

        Uses the Slack auth.test endpoint to get workspace details

        Args:
            access_token: Valid access token

        Returns:
            Dictionary containing:
                - id: User ID
                - team_id: Workspace/Team ID
                - team: Workspace name
                - user: Username
                - user_id: User ID
                - bot_id: Bot user ID (if applicable)
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        try:
            response = await self.http_client.post(
                "https://slack.com/api/auth.test",
                headers=headers
            )
            response.raise_for_status()

            data = response.json()

            if not data.get("ok"):
                raise Exception(f"Slack API error: {data.get('error', 'Unknown error')}")

            return {
                "id": data.get("user_id"),
                "team_id": data.get("team_id"),
                "team": data.get("team"),
                "user": data.get("user"),
                "user_id": data.get("user_id"),
                "bot_id": data.get("bot_id"),
            }

        except httpx.HTTPStatusError as e:
            error_detail = e.response.json() if e.response.content else {}
            raise Exception(
                f"Failed to get user info: {error_detail.get('error', str(e))}"
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
                "https://slack.com/api/auth.revoke",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            data = response.json()
            return data.get("ok", False)
        except Exception:
            return False
