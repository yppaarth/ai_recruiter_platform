from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import get_current_user
from app.models.models import User
from app.schemas.schemas import GenerateEmailRequest, GeneratedEmail
from app.services.grok_client import grok_client

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/generate-email", response_model=GeneratedEmail)
async def generate_email(
    payload: GenerateEmailRequest,
    current_user: User = Depends(get_current_user),
) -> GeneratedEmail:
    """Generate a single personalized outreach email using Grok AI."""
    try:
        result = await grok_client.generate_outreach_email(
            recruiter_name=payload.recruiter_name,
            company=payload.company,
            title=payload.title,
            candidate_profile=payload.candidate_profile,
            extra_context=payload.extra_context,
        )
        return GeneratedEmail(subject=result["subject"], body=result["body"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")
