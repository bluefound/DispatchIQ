from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from app.api.deps import CurrentUserDep, SessionDep
from app.engine.dispatch_optimizer import CandidateDriver, DispatchOptimizer, OrderTarget
from app.engine.policy_engine import PolicyEngine
from app.models.dispatch import DispatchDecision, DispatchMethod, DispatchStatus
from app.models.driver import Driver, DriverStatus
from app.models.order import DeliveryEvent, DeliveryEventType, Order, OrderStatus
from app.models.policy import Policy
from app.schemas.dispatch import BatchDispatchRequest, DispatchDecisionResponse, DispatchRequest

router = APIRouter(prefix="/dispatch", tags=["Dispatch Optimization"])


@router.post("/optimize/{order_id}", response_model=list[DispatchDecisionResponse])
async def optimize_dispatch_candidates(
    order_id: UUID,
    session: SessionDep,
    _: CurrentUserDep,
):
    stmt_order = select(Order).where(Order.id == order_id)
    res_order = await session.execute(stmt_order)
    order = res_order.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    stmt_drivers = select(Driver).where(Driver.is_available == True)
    res_drivers = await session.execute(stmt_drivers)
    available_drivers = res_drivers.scalars().all()

    if not available_drivers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No available drivers found"
        )

    candidates = [
        CandidateDriver(
            driver_id=str(d.id),
            latitude=d.current_latitude or order.pickup_latitude,
            longitude=d.current_longitude or order.pickup_longitude,
            rating=d.rating,
            active_orders=d.active_orders,
            capacity=d.capacity,
            vehicle_type=d.vehicle_type.value,
            current_zone=d.current_zone,
        )
        for d in available_drivers
    ]

    order_target = OrderTarget(
        order_id=str(order.id),
        pickup_latitude=order.pickup_latitude,
        pickup_longitude=order.pickup_longitude,
        dropoff_latitude=order.dropoff_latitude,
        dropoff_longitude=order.dropoff_longitude,
        priority=order.priority.value,
    )

    optimizer = DispatchOptimizer()
    scored_candidates = optimizer.optimize_single_order(order_target, candidates)

    stmt_policies = select(Policy).where(Policy.is_active == True)
    res_policies = await session.execute(stmt_policies)
    policies = res_policies.scalars().all()

    policy_engine = PolicyEngine()
    decisions = []

    for cand in scored_candidates:
        driver = next(d for d in available_drivers if str(d.id) == cand.driver_id)
        eval_res = policy_engine.evaluate_dispatch(
            driver=driver,
            order=order,
            distance_km=cand.distance_km,
            policies=policies,
        )

        decision_status = (
            DispatchStatus.POLICY_APPROVED
            if eval_res.approved
            else DispatchStatus.POLICY_REJECTED
        )
        if eval_res.approved and eval_res.requires_approval:
            decision_status = DispatchStatus.AWAITING_APPROVAL

        decision = DispatchDecision(
            order_id=order.id,
            driver_id=driver.id,
            score=cand.score,
            distance_km=cand.distance_km,
            estimated_eta_minutes=cand.estimated_eta_minutes,
            optimization_method=DispatchMethod.SCORING,
            rank=cand.rank,
            scoring_details=cand.scoring_details,
            status=decision_status,
            policy_approved=eval_res.approved,
            policy_reason=eval_res.reason,
            policy_violations=[
                {
                    "policy": v.policy_name,
                    "rule": v.rule_key,
                    "expected": v.expected,
                    "actual": v.actual,
                    "message": v.message,
                }
                for v in eval_res.violations
            ]
            if eval_res.violations
            else None,
        )
        session.add(decision)
        decisions.append(decision)

    await session.commit()
    for d in decisions:
        await session.refresh(d)

    return decisions


@router.post("/assign", response_model=DispatchDecisionResponse)
async def assign_driver(
    req: DispatchRequest,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    stmt_order = select(Order).where(Order.id == req.order_id)
    res_order = await session.execute(stmt_order)
    order = res_order.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    driver_id = req.preferred_driver_id
    if not driver_id:
        stmt_dec = (
            select(DispatchDecision)
            .where(
                DispatchDecision.order_id == req.order_id,
                DispatchDecision.policy_approved == True,
            )
            .order_by(DispatchDecision.score.desc())
        )
        res_dec = await session.execute(stmt_dec)
        top_decision = res_dec.scalars().first()
        if not top_decision:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No policy-approved driver decision found. Run optimization first.",
            )
        driver_id = top_decision.driver_id

    stmt_driver = select(Driver).where(Driver.id == driver_id)
    res_driver = await session.execute(stmt_driver)
    driver = res_driver.scalar_one_or_none()
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

    now = datetime.now(timezone.utc)
    order.driver_id = driver.id
    order.status = OrderStatus.ASSIGNED
    order.assigned_at = now

    driver.status = DriverStatus.ASSIGNED
    driver.active_orders += 1
    if driver.active_orders >= driver.capacity:
        driver.is_available = False

    decision = DispatchDecision(
        order_id=order.id,
        driver_id=driver.id,
        score=100.0 if req.force else 90.0,
        distance_km=0.0,
        estimated_eta_minutes=15.0,
        optimization_method=DispatchMethod.MANUAL if req.preferred_driver_id else DispatchMethod.OR_TOOLS,
        rank=1,
        status=DispatchStatus.ACCEPTED,
        policy_approved=True,
        policy_reason="Manually assigned or policy approved assignment executed",
        accepted_at=now,
        reviewed_by=current_user.email,
    )
    session.add(decision)

    event = DeliveryEvent(
        order_id=order.id,
        driver_id=driver.id,
        event_type=DeliveryEventType.DRIVER_ASSIGNED,
        description=f"Driver {driver.id} assigned to order {order.order_number}",
    )
    session.add(event)

    await session.commit()
    await session.refresh(decision)
    return decision
