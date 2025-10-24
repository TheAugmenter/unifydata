"""
Data Sources API Endpoints
OAuth connection flows for all data sources
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import secrets
from datetime import datetime

from app.core.database import get_db
from app.core.config import settings
from app.models import DataSource, User
from app.services.encryption import encryption_service
from app.connectors.salesforce import SalesforceConnector
from app.api.dependencies import get_current_user

router = APIRouter()


# In-memory state storage (replace with Redis in production)
oauth_states = {}


@router.get("/salesforce/connect")
async def connect_salesforce(
    # current_user: User = Depends(get_current_user)  # Disabled for testing
):
    """
    Initiate Salesforce OAuth flow

    Returns authorization URL to redirect user to
    """
    if not settings.SALESFORCE_CLIENT_ID or not settings.SALESFORCE_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Salesforce OAuth is not configured"
        )

    # Generate CSRF state token
    state = secrets.token_urlsafe(32)
    oauth_states[state] = {
        "user_id": "test-user-id",  # Hardcoded for testing
        "source_type": "salesforce",
        "created_at": datetime.utcnow()
    }

    # Initialize Salesforce connector
    connector = SalesforceConnector(
        client_id=settings.SALESFORCE_CLIENT_ID,
        client_secret=settings.SALESFORCE_CLIENT_SECRET,
        redirect_uri=settings.SALESFORCE_REDIRECT_URI,
        scopes=["api", "refresh_token", "id"]
    )

    # Get authorization URL
    auth_url = await connector.get_authorization_url(state)
    await connector.close()

    return {
        "authorization_url": auth_url,
        "state": state
    }


@router.get("/salesforce/callback")
async def salesforce_callback(
    code: str = Query(..., description="Authorization code from Salesforce"),
    state: str = Query(..., description="CSRF state token"),
    db: AsyncSession = Depends(get_db)
):
    """
    Salesforce OAuth callback endpoint

    Exchanges authorization code for access and refresh tokens
    """
    # Validate state token
    if state not in oauth_states:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired state token"
        )

    state_data = oauth_states.pop(state)
    user_id = state_data["user_id"]

    # Initialize Salesforce connector
    connector = SalesforceConnector(
        client_id=settings.SALESFORCE_CLIENT_ID,
        client_secret=settings.SALESFORCE_CLIENT_SECRET,
        redirect_uri=settings.SALESFORCE_REDIRECT_URI,
        scopes=["api", "refresh_token", "id"]
    )

    try:
        # Exchange code for tokens
        token_data = await connector.exchange_code_for_tokens(code, state)

        # Get user info from Salesforce
        user_info = await connector.get_user_info(token_data["access_token"])

        # Encrypt tokens
        encrypted_access_token = encryption_service.encrypt(token_data["access_token"])
        encrypted_refresh_token = encryption_service.encrypt(token_data.get("refresh_token", ""))

        # Calculate token expiry
        token_expiry = connector.calculate_token_expiry(token_data.get("expires_in", 7200))

        # Check if data source already exists for this user
        result = await db.execute(
            select(DataSource).where(
                DataSource.user_id == user_id,
                DataSource.type == "salesforce"
            )
        )
        existing_source = result.scalar_one_or_none()

        if existing_source:
            # Update existing data source
            existing_source.status = "connected"
            existing_source.oauth_token = encrypted_access_token
            existing_source.refresh_token = encrypted_refresh_token
            existing_source.token_expires_at = token_expiry
            existing_source.metadata = {
                "instance_url": token_data.get("instance_url"),
                "user_email": user_info.get("email"),
                "username": user_info.get("username"),
                "salesforce_user_id": user_info.get("id")
            }
            existing_source.last_synced_at = None  # Reset sync status
        else:
            # Create new data source
            new_source = DataSource(
                user_id=user_id,
                type="salesforce",
                name=f"Salesforce ({user_info.get('email', 'Unknown')})",
                status="connected",
                oauth_token=encrypted_access_token,
                refresh_token=encrypted_refresh_token,
                token_expires_at=token_expiry,
                metadata={
                    "instance_url": token_data.get("instance_url"),
                    "user_email": user_info.get("email"),
                    "username": user_info.get("username"),
                    "salesforce_user_id": user_info.get("id")
                }
            )
            db.add(new_source)

        await db.commit()
        await connector.close()

        # Redirect back to frontend with success
        return RedirectResponse(
            url=f"{settings.WEB_URL}/data-sources?status=success&source=salesforce"
        )

    except Exception as e:
        await connector.close()
        # Redirect back to frontend with error
        return RedirectResponse(
            url=f"{settings.WEB_URL}/data-sources?status=error&source=salesforce&message={str(e)}"
        )


@router.get("/")
async def list_data_sources(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all data sources for current user
    """
    result = await db.execute(
        select(DataSource).where(DataSource.user_id == current_user.id)
    )
    sources = result.scalars().all()

    return {
        "data_sources": [
            {
                "id": str(source.id),
                "type": source.type,
                "name": source.name,
                "status": source.status,
                "last_synced_at": source.last_synced_at.isoformat() if source.last_synced_at else None,
                "documents_indexed": source.documents_indexed,
                "metadata": source.metadata
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
    """
    Disconnect (delete) a data source
    """
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
    # For now, just delete from DB

    await db.delete(source)
    await db.commit()

    return {"message": "Data source disconnected successfully"}


@router.post("/{source_id}/sync")
async def trigger_sync(
    source_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger data sync for a source
    """
    result = await db.execute(
        select(DataSource).where(
            DataSource.id == source_id,
            DataSource.user_id == current_user.id
        )
    )
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")

    if source.status != "connected":
        raise HTTPException(
            status_code=400,
            detail="Data source is not in connected state"
        )

    # TODO: Queue sync job with Celery
    # For now, just update status
    source.status = "syncing"
    await db.commit()

    return {
        "message": "Sync triggered successfully",
        "source_id": str(source.id),
        "status": "syncing"
    }
