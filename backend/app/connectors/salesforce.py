"""
Salesforce OAuth Connector
Implements OAuth 2.0 Web Server Flow for Salesforce
"""
from typing import Dict, Optional, Any
from urllib.parse import urlencode
import httpx

from .base import BaseOAuthConnector


class SalesforceConnector(BaseOAuthConnector):
    """
    Salesforce OAuth 2.0 connector

    Implements the Salesforce Web Server OAuth flow:
    https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_web_server_flow.htm

    Scopes:
    - api: Access to Salesforce APIs
    - refresh_token: Ability to refresh access token
    - id: Access to user identity information
    - full: Full access to all data (use with caution)
    """

    @property
    def provider_name(self) -> str:
        return "salesforce"

    @property
    def authorization_base_url(self) -> str:
        # Use login.salesforce.com for production, test.salesforce.com for sandbox
        return "https://login.salesforce.com/services/oauth2/authorize"

    @property
    def token_url(self) -> str:
        return "https://login.salesforce.com/services/oauth2/token"

    async def get_authorization_url(self, state: str) -> str:
        """
        Generate Salesforce OAuth authorization URL

        Args:
            state: CSRF protection state parameter

        Returns:
            Full authorization URL to redirect user to
        """
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": state,
            "scope": " ".join(self.scopes),
            # Salesforce-specific: request immediate response (no approval page for already authorized apps)
            "prompt": "login",
        }

        return f"{self.authorization_base_url}?{urlencode(params)}"

    async def exchange_code_for_tokens(
        self,
        code: str,
        state: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for access and refresh tokens

        Args:
            code: Authorization code from OAuth callback
            state: State parameter for CSRF validation (not used in token exchange)

        Returns:
            Dictionary containing:
                - access_token: Access token
                - refresh_token: Refresh token
                - instance_url: Salesforce instance URL (e.g., https://na1.salesforce.com)
                - id: Identity URL
                - token_type: 'Bearer'
                - issued_at: Token issue timestamp
                - signature: Token signature
        """
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
        }

        try:
            response = await self.http_client.post(
                self.token_url,
                data=data,
                headers={"Accept": "application/json"}
            )
            response.raise_for_status()

            token_data = response.json()

            # Salesforce doesn't return expires_in by default
            # Access tokens typically don't expire, but can be revoked
            # We'll set a default of 2 hours for safety
            if "expires_in" not in token_data:
                token_data["expires_in"] = 7200  # 2 hours

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
            Dictionary containing new access_token and instance_url
        """
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        try:
            response = await self.http_client.post(
                self.token_url,
                data=data,
                headers={"Accept": "application/json"}
            )
            response.raise_for_status()

            token_data = response.json()

            # Set default expires_in
            if "expires_in" not in token_data:
                token_data["expires_in"] = 7200  # 2 hours

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
        Uses the Salesforce identity endpoint

        Args:
            access_token: Access token to test

        Returns:
            True if connection is valid, False otherwise
        """
        try:
            # Get user info - if this succeeds, token is valid
            await self.get_user_info(access_token)
            return True
        except Exception:
            return False

    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get user information from Salesforce

        Uses the Salesforce Identity endpoint to get user details

        Args:
            access_token: Valid access token

        Returns:
            Dictionary containing user info:
                - id: User ID
                - email: User email
                - username: Salesforce username
                - display_name: Display name
                - organization_id: Salesforce Org ID
        """
        # First, get the identity URL from a simple query
        # We'll use the query endpoint which also tells us the instance URL
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }

        try:
            # Get the latest API version
            versions_response = await self.http_client.get(
                "https://login.salesforce.com/services/data/",
                headers=headers
            )
            versions_response.raise_for_status()
            versions = versions_response.json()
            latest_version = versions[-1]["version"]

            # Query for current user info
            query_url = f"https://login.salesforce.com/services/data/v{latest_version}/query"
            query_params = {
                "q": "SELECT Id, Email, Username, Name FROM User WHERE Id = UserInfo.getUserId()"
            }

            user_response = await self.http_client.get(
                query_url,
                headers=headers,
                params=query_params
            )
            user_response.raise_for_status()
            user_data = user_response.json()

            if user_data.get("records"):
                user = user_data["records"][0]
                return {
                    "id": user.get("Id"),
                    "email": user.get("Email"),
                    "username": user.get("Username"),
                    "display_name": user.get("Name"),
                    "organization_id": user.get("Id", "")[:15],  # Extract org ID from user ID
                }
            else:
                raise Exception("No user data returned from Salesforce")

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
        revoke_url = "https://login.salesforce.com/services/oauth2/revoke"

        try:
            response = await self.http_client.post(
                revoke_url,
                data={"token": access_token}
            )
            return response.status_code == 200
        except Exception:
            return False
