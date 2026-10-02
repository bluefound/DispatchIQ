from dataclasses import dataclass
from typing import Any
from app.models.driver import Driver
from app.models.order import Order
from app.models.policy import Policy


@dataclass
class PolicyViolation:
    policy_name: str
    rule_key: str
    expected: Any
    actual: Any
    message: str


@dataclass
class PolicyEvaluationResult:
    approved: bool
    requires_approval: bool
    violations: list[PolicyViolation]
    reason: str


class PolicyEngine:
    def evaluate_dispatch(
        self,
        driver: Driver,
        order: Order,
        distance_km: float,
        policies: list[Policy],
    ) -> PolicyEvaluationResult:
        violations: list[PolicyViolation] = []
        requires_approval = False

        active_policies = [p for p in policies if p.is_active]
        active_policies.sort(key=lambda p: p.priority)

        for policy in active_policies:
            rules = policy.rules

            if "max_distance_km" in rules:
                max_dist = float(rules["max_distance_km"])
                if distance_km > max_dist:
                    violations.append(
                        PolicyViolation(
                            policy_name=policy.name,
                            rule_key="max_distance_km",
                            expected=max_dist,
                            actual=distance_km,
                            message=f"Distance {distance_km:.2f}km exceeds max allowed {max_dist}km",
                        )
                    )

            if "max_active_orders" in rules:
                max_orders = int(rules["max_active_orders"])
                if driver.active_orders >= max_orders:
                    violations.append(
                        PolicyViolation(
                            policy_name=policy.name,
                            rule_key="max_active_orders",
                            expected=max_orders,
                            actual=driver.active_orders,
                            message=f"Driver active orders ({driver.active_orders}) reached limit ({max_orders})",
                        )
                    )

            if rules.get("require_same_zone", False) and driver.current_zone and order.restaurant:
                if driver.current_zone != order.restaurant.zone:
                    violations.append(
                        PolicyViolation(
                            policy_name=policy.name,
                            rule_key="require_same_zone",
                            expected=order.restaurant.zone,
                            actual=driver.current_zone,
                            message=f"Driver zone '{driver.current_zone}' differs from restaurant zone '{order.restaurant.zone}'",
                        )
                    )

            if rules.get("requires_human_approval", False):
                requires_approval = True

            if "min_driver_rating" in rules:
                min_rating = float(rules["min_driver_rating"])
                if driver.rating < min_rating:
                    violations.append(
                        PolicyViolation(
                            policy_name=policy.name,
                            rule_key="min_driver_rating",
                            expected=min_rating,
                            actual=driver.rating,
                            message=f"Driver rating {driver.rating} below minimum required {min_rating}",
                        )
                    )

        approved = len(violations) == 0
        if not approved:
            reason = f"Failed {len(violations)} policy checks: " + "; ".join(
                v.message for v in violations
            )
        elif requires_approval:
            reason = "Action approved by automated policies but requires human sign-off"
        else:
            reason = "Approved by all operational policies"

        return PolicyEvaluationResult(
            approved=approved,
            requires_approval=requires_approval,
            violations=violations,
            reason=reason,
        )
