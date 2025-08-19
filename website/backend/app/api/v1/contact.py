"""API endpoints for contact functionality."""

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.limiter import limiter
from app.dependency.database import get_db_dep
from app.schema.requests.contact import ContactRequest
from app.service.contact import ContactService

router = APIRouter()


@router.post("/send")
@limiter.limit("5/minute")  # Limit contact form submissions
async def send_contact_message(
    request: Request,
    body: ContactRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = get_db_dep,
) -> dict[str, str]:
    """Send a contact message to administrators.

    Args:
        request: The FastAPI request object
        body: The contact form data
        background_tasks: Background tasks manager
        db: Database session

    Returns:
        dict: Success message

    Raises:
        HTTPException: If sending fails

    """
    try:
        # Log the received data for debugging
        print(
            f"Received contact form: email={body.email}, request_type={body.request_type}, message_length={len(body.message)}"
        )

        # Detect language from Accept-Language header
        accept_language = request.headers.get("accept-language", "en")
        language = "fr" if accept_language.startswith("fr") else "en"

        # Send contact message to all administrators
        await ContactService.send_contact_message(
            db=db,
            email=body.email,
            request_type=body.request_type,
            message=body.message,
            background_tasks=background_tasks,
            language=language,
        )

        return {"message": "Contact message sent successfully"}

    except Exception as e:
        print(f"Error in contact endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send contact message",
        ) from e
