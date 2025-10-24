"""
Data Sources API Endpoints
OAuth connection flows for all data sources (Salesforce, Slack, Google, Notion)
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import secrets
from datetime import datetime
from typing import Type, Dict, List

from app.core.database import get_db
from app.core.config import settings
from app.models import DataSource, User
from app.services.encryption import encryption_service
from app.connectors import (
    BaseOAuthConnector,
    SalesforceConnector,
    SlackConnector,
    GoogleConnector,
    NotionConnector,
)
from app.api.dependencies import get_current_user

router = APIRouter()

# In-memory state storage (replace with Redis in production)
oauth_states: Dict[str, Dict] = {}

# Connector configurations
CONNECTOR_CONFIGS = {
    "salesforce": {
        "connector_class": SalesforceConnector,
        "client_id_setting": "SALESFORCE_CLIENT_ID",
        "client_secret_setting": "SALESFORCE_CLIENT_SECRET",
        "redirect_uri_setting": "SALESFORCE_REDIRECT_URI",
        "scopes": ["api", "refresh_token", "id"],
    },
    "slack": {
        "connector_class": SlackConnector,
        "client_id_setting": "SLACK_CLIENT_ID",
        "client_secret_setting": "SLACK_CLIENT_SECRET",
        "redirect_uri_setting": "SLACK_REDIRECT_URI",
        "scopes": ["channels:history", "channels:read", "files:read", "search:read", "users:read"],
    },
    "google": {  # Used for both Google Drive and Gmail
        "connector_class": GoogleConnector,
        "client_id_setting": "GOOGLE_CLIENT_ID",
        "client_secret_setting": "GOOGLE_CLIENT_SECRET",
        "redirect_uri_setting": "GOOGLE_REDIRECT_URI",
        "scopes": [
            "https://www.googleapis.com/auth/drive.readonly",
            "https://www.googleapis.com/auth/gmail.readonly",
        ],
    },
    "notion": {
        "connector_class": NotionConnector,
        "client_id_setting": "NOTION_CLIENT_ID",
        "client_secret_setting": "NOTION_CLIENT_SECRET",
        "redirect_uri_setting": "NOTION_REDIRECT_URI",
        "scopes": [],  # Notion doesn't use explicit scopes
    },
}


def get_connector_config(source_type: str):
    """Get connector configuration for a data source type"""
    if source_type not in CONNECTOR_CONFIGS:
        raise HTTPException(status_code=400, detail=f"Unsupported data source type: {source_type}")
    return CONNECTOR_CONFIGS[source_type]


def create_connector(source_type: str) -> BaseOAuthConnector:
    """Create and initialize a connector instance"""
    config = get_connector_config(source_type)

    client_id = getattr(settings, config["client_id_setting"], None)
    client_secret = getattr(settings, config["client_secret_setting"], None)
    redirect_uri = getattr(settings, config["redirect_uri_setting"], None)

    if not client_id or not client_secret:
        raise HTTPException(
            status_code=503,
            detail=f"{source_type.title()} connector is not configured yet. Please contact your administrator to set up OAuth credentials."
        )

    connector_class = config["connector_class"]
    return connector_class(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scopes=config["scopes"],
    )


# Generic connect endpoint creator
def create_connect_endpoint(source_type: str):
    """Factory function to create connect endpoint for a data source"""

    async def connect_handler():
        """Initiate OAuth flow with PKCE"""
        # Generate PKCE code_verifier and code_challenge
        code_verifier, code_challenge = BaseOAuthConnector.generate_pkce_pair()

        # Generate CSRF state token
        state = secrets.token_urlsafe(32)
        oauth_states[state] = {
            "user_id": "test-user-id",  # Hardcoded for testing
            "source_type": source_type,
            "code_verifier": code_verifier,
            "created_at": datetime.utcnow()
        }

        # Initialize connector
        connector = create_connector(source_type)

        # Get authorization URL with PKCE
        auth_url = await connector.get_authorization_url(state, code_challenge=code_challenge)
        await connector.close()

        return {
            "authorization_url": auth_url,
            "state": state
        }

    return connect_handler


# Generic callback endpoint creator
def create_callback_endpoint(source_type: str):
    """Factory function to create callback endpoint for a data source"""

    async def callback_handler(
        code: str = Query(..., description="Authorization code"),
        state: str = Query(..., description="CSRF state token"),
        db: AsyncSession = Depends(get_db)
    ):
        """OAuth callback - exchanges code for tokens"""
        print(f"[OAuth] {source_type} callback received")

        # Validate state token
        if state not in oauth_states:
            raise HTTPException(status_code=400, detail="Invalid or expired state token")

        state_data = oauth_states.pop(state)
        user_id = state_data["user_id"]
        code_verifier = state_data.get("code_verifier")

        # Initialize connector
        connector = create_connector(source_type)

        try:
            print(f"[OAuth] Exchanging code for tokens with PKCE...")
            # Exchange code for tokens
            token_data = await connector.exchange_code_for_tokens(
                code,
                state=state,
                code_verifier=code_verifier
            )
            print(f"[OAuth] Token exchange successful!")

            # Get user info
            print(f"[OAuth] Fetching user info...")
            user_info = await connector.get_user_info(token_data["access_token"])
            print(f"[OAuth] User info retrieved")

            # Encrypt tokens
            encrypted_access_token = encryption_service.encrypt(token_data["access_token"])
            encrypted_refresh_token = encryption_service.encrypt(token_data.get("refresh_token", ""))

            # Calculate token expiry
            token_expiry = connector.calculate_token_expiry(token_data.get("expires_in", 3600))

            # Check if data source already exists
            result = await db.execute(
                select(DataSource).where(
                    DataSource.user_id == user_id,
                    DataSource.type == source_type
                )
            )
            existing_source = result.scalar_one_or_none()

            if existing_source:
                # Update existing data source
                existing_source.status = "connected"
                existing_source.oauth_token = encrypted_access_token
                existing_source.refresh_token = encrypted_refresh_token
                existing_source.token_expires_at = token_expiry
                existing_source.metadata = user_info
                existing_source.last_synced_at = None
            else:
                # Create new data source
                new_source = DataSource(
                    user_id=user_id,
                    type=source_type,
                    name=f"{source_type.title()} ({user_info.get('email', user_info.get('name', 'Unknown'))})",
                    status="connected",
                    oauth_token=encrypted_access_token,
                    refresh_token=encrypted_refresh_token,
                    token_expires_at=token_expiry,
                    metadata=user_info
                )
                db.add(new_source)

            await db.commit()
            await connector.close()

            print(f"[OAuth] {source_type} connected successfully!")

            # Redirect back to frontend with success
            return RedirectResponse(
                url=f"{settings.WEB_URL}/data-sources?status=success&source={source_type}"
            )

        except Exception as e:
            print(f"[OAuth] ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            await connector.close()
            # Redirect back to frontend with error
            return RedirectResponse(
                url=f"{settings.WEB_URL}/data-sources?status=error&source={source_type}&message={str(e)}"
            )

    return callback_handler


# Register all connect and callback endpoints
for source_type in CONNECTOR_CONFIGS.keys():
    # Connect endpoint
    router.add_api_route(
        f"/{source_type}/connect",
        create_connect_endpoint(source_type),
        methods=["GET"],
        name=f"connect_{source_type}",
        summary=f"Initiate {source_type.title()} OAuth flow",
    )

    # Callback endpoint
    router.add_api_route(
        f"/{source_type}/callback",
        create_callback_endpoint(source_type),
        methods=["GET"],
        name=f"{source_type}_callback",
        summary=f"{source_type.title()} OAuth callback",
    )


@router.get("/")
async def list_data_sources(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all data sources for current user's organization"""
    result = await db.execute(
        select(DataSource).where(DataSource.org_id == current_user.org_id)
    )
    sources = result.scalars().all()

    return {
        "data_sources": [
            {
                "id": str(source.id),
                "type": source.source_type,
                "name": source.name,
                "status": source.status,
                "last_synced_at": source.last_sync_at.isoformat() if source.last_sync_at else None,
                "documents_indexed": source.documents_indexed,
                "metadata": source.config
            }
            for source in sources
        ]
    }


@router.delete("/{source_id}")
async def disconnect_data_source(
    source_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Disconnect (delete) a data source"""
    result = await db.execute(
        select(DataSource).where(
            DataSource.id == source_id,
            DataSource.user_id == current_user.id
        )
    )
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")

    # TODO: Revoke OAuth token with provider

    await db.delete(source)
    await db.commit()

    return {"message": "Data source disconnected successfully"}


@router.post("/{source_id}/sync")
async def trigger_sync(
    source_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger data sync for a source"""
    from app.services.data_sync import data_sync_service
    from uuid import UUID

    result = await db.execute(
        select(DataSource).where(
            DataSource.id == UUID(source_id),
            DataSource.connected_by_user_id == current_user.id
        )
    )
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")

    if source.status not in ["connected", "error"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot sync data source in '{source.status}' state"
        )

    try:
        # Trigger sync using data sync service
        sync_result = await data_sync_service.sync_data_source(
            db=db,
            data_source_id=UUID(source_id),
            sync_type="manual"
        )

        return {
            "message": "Sync completed successfully",
            "source_id": str(source.id),
            "status": "success",
            "stats": sync_result.get("stats", {}),
            "sync_log_id": str(sync_result.get("sync_log_id"))
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Sync failed: {str(e)}"
        )
