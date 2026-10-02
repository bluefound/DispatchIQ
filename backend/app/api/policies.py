from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from app.api.deps import CurrentUserDep, SessionDep
from app.models.policy import Policy
from app.schemas.policy import PolicyCreate, PolicyResponse, PolicyUpdate

router = APIRouter(prefix="/policies", tags=["Policies"])


@router.get("", response_model=list[PolicyResponse])
async def list_policies(
    session: SessionDep,
    is_active: bool | None = None,
    policy_type: str | None = None,
):
    stmt = select(Policy)
    if is_active is not None:
        stmt = stmt.where(Policy.is_active == is_active)
    if policy_type:
        stmt = stmt.where(Policy.policy_type == policy_type)
    stmt = stmt.order_by(Policy.priority.asc())
    result = await session.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_policy(
    policy_in: PolicyCreate,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    stmt = select(Policy).where(Policy.name == policy_in.name)
    res = await session.execute(stmt)
    if res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Policy with this name already exists")

    policy = Policy(
        name=policy_in.name,
        description=policy_in.description,
        rules=policy_in.rules,
        policy_type=policy_in.policy_type,
        is_active=policy_in.is_active,
        priority=policy_in.priority,
        created_by=current_user.email,
    )
    session.add(policy)
    await session.commit()
    await session.refresh(policy)
    return policy


@router.patch("/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    policy_id: UUID,
    policy_in: PolicyUpdate,
    session: SessionDep,
    _: CurrentUserDep,
):
    stmt = select(Policy).where(Policy.id == policy_id)
    res = await session.execute(stmt)
    policy = res.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")

    update_data = policy_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(policy, field, value)

    await session.commit()
    await session.refresh(policy)
    return policy
