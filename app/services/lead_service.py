import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead, LeadStatus
from app.schemas.lead import LeadCreate, LeadUpdate


async def create_lead(
    session: AsyncSession,
    data: LeadCreate,
    resume_path: str | None = None,
) -> Lead:
    lead = Lead(
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email,
        resume_path=resume_path,
    )
    session.add(lead)
    await session.commit()
    await session.refresh(lead)
    return lead


async def get_leads(session: AsyncSession) -> list[Lead]:
    result = await session.execute(select(Lead).order_by(Lead.created_at.desc()))
    return list(result.scalars().all())


async def get_lead(session: AsyncSession, lead_id: uuid.UUID) -> Lead | None:
    result = await session.execute(select(Lead).where(Lead.id == lead_id))
    return result.scalar_one_or_none()


async def update_lead(
    session: AsyncSession, lead: Lead, data: LeadUpdate
) -> Lead:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(lead, field, value)
    await session.commit()
    await session.refresh(lead)
    return lead


async def mark_reached_out(session: AsyncSession, lead: Lead) -> Lead:
    lead.status = LeadStatus.REACHED_OUT
    await session.commit()
    await session.refresh(lead)
    return lead
