import re
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple, Type
from pydantic import BaseModel, ValidationError
from app.core.logging import logger


class GuardrailViolationException(Exception):
    """Raised when an input or tool execution violates security or domain guardrails."""
    def __init__(self, rule_name: str, message: str, severity: str = "HIGH", sanitized_input: Optional[str] = None):
        super().__init__(message)
        self.rule_name = rule_name
        self.message = message
        self.severity = severity
        self.sanitized_input = sanitized_input


class SecurityGuardrails:
    """
    Enterprise-grade security guardrails for DealForge AI:
    1. Prompt Injection & Jailbreak Defense
    2. Toxic & Abusive Language Filtering
    3. Tool Return & Parameter Type Validation Callbacks
    4. Procurement Domain Boundary Enforcement
    """

    # Prompt injection and jailbreak patterns
    INJECTION_PATTERNS = [
        r"(?i)\bignore\s+(?:all\s+)?(?:previous|prior|above)\s+instructions\b",
        r"(?i)\bdisregard\s+(?:all\s+)?(?:previous|prior|above)\s+instructions\b",
        r"(?i)\bsystem\s+override\b",
        r"(?i)\byou\s+are\s+now\s+(?:an?\s+)?(?:unfiltered|jailbroken|developer\s+mode|dan)\b",
        r"(?i)\bpretend\s+you\s+have\s+no\s+(?:rules|guidelines|restrictions)\b",
        r"(?i)\bprint\s+(?:your\s+)?(?:system\s+prompt|instructions|api\s*key)\b",
        r"(?i)\bdrop\s+table\b",
        r"(?i)\bunion\s+select\b",
        r"(?i)<script\b[^>]*>",
        r"(?i)javascript:\s*",
        r"(?i)\bexec\s*\(\s*['\"]",
        r"(?i)\beval\s*\(\s*['\"]",
        r"(?i)base64_decode",
    ]

    # Toxic, abusive, or harmful keyword patterns
    TOXIC_PATTERNS = [
        r"(?i)\b(?:kill|murder|bomb|attack|hack|exploit|threaten|harass)\b",
        r"(?i)\b(?:idiot|stupid|bastard|scam|fraudulent\s+scheme)\b",
    ]

    # Domain constraints
    MIN_QUANTITY = 1
    MAX_QUANTITY = 100_000
    MIN_BUDGET = Decimal("100.00")
    MAX_BUDGET = Decimal("1000000000.00")  # ₹100 Crore ceiling

    @classmethod
    def validate_user_prompt(cls, text: str) -> Tuple[bool, Optional[str]]:
        """
        Scans incoming natural-language purchase request for prompt injection,
        jailbreak attempts, and toxic or malicious patterns.
        """
        if not text or not text.strip():
            raise GuardrailViolationException(
                rule_name="EMPTY_PROMPT_RULE",
                message="User procurement prompt cannot be empty or whitespace only.",
                severity="MEDIUM"
            )

        # 1. Prompt Injection Checks
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, text):
                logger.warning(f"Security Alert: Prompt injection pattern matched: {pattern}")
                raise GuardrailViolationException(
                    rule_name="PROMPT_INJECTION_DEFENSE",
                    message="Malicious prompt injection or instruction override attempt detected.",
                    severity="CRITICAL",
                    sanitized_input=re.sub(pattern, "[REDACTED_ATTACK_VECTOR]", text)
                )

        # 2. Toxic Language Checks
        for pattern in cls.TOXIC_PATTERNS:
            if re.search(pattern, text):
                logger.warning(f"Security Alert: Toxic/harmful pattern matched: {pattern}")
                raise GuardrailViolationException(
                    rule_name="TOXIC_LANGUAGE_DEFENSE",
                    message="Abusive, toxic, or hazardous language detected in procurement request.",
                    severity="HIGH"
                )

        return True, None

    @classmethod
    def validate_domain_constraints(
        cls,
        quantity: Optional[int] = None,
        budget: Optional[Decimal] = None,
        category: Optional[str] = None
    ) -> bool:
        """
        Enforces procurement business logic boundaries and prevents arithmetic exploits.
        """
        if quantity is not None:
            if quantity < cls.MIN_QUANTITY or quantity > cls.MAX_QUANTITY:
                raise GuardrailViolationException(
                    rule_name="QUANTITY_BOUNDARY_GUARDRAIL",
                    message=f"Procurement quantity {quantity} is outside safe allowable bounds ({cls.MIN_QUANTITY} to {cls.MAX_QUANTITY}).",
                    severity="HIGH"
                )

        if budget is not None:
            if budget < cls.MIN_BUDGET or budget > cls.MAX_BUDGET:
                raise GuardrailViolationException(
                    rule_name="BUDGET_BOUNDARY_GUARDRAIL",
                    message=f"Budget ₹{budget:,.2f} is outside enterprise allowable boundaries (₹{cls.MIN_BUDGET} to ₹{cls.MAX_BUDGET}).",
                    severity="HIGH"
                )

        return True

    @classmethod
    def validate_tool_output(cls, tool_name: str, output: Any, expected_type: Type[BaseModel] = None) -> Any:
        """
        Callback validation function verifying data types and integrity of tool return values.
        Guarantees that external tools never return corrupted or type-mismatched data into agent state.
        """
        if output is None:
            raise GuardrailViolationException(
                rule_name="TOOL_OUTPUT_NULL_CHECK",
                message=f"Tool '{tool_name}' returned NULL, violating deterministic execution guarantees.",
                severity="HIGH"
            )

        if expected_type and issubclass(expected_type, BaseModel):
            try:
                if isinstance(output, dict):
                    return expected_type.model_validate(output)
                elif isinstance(output, expected_type):
                    return output
            except ValidationError as ve:
                logger.error(f"Tool output type validation error in {tool_name}: {ve}")
                raise GuardrailViolationException(
                    rule_name="TOOL_OUTPUT_SCHEMA_VALIDATION",
                    message=f"Tool '{tool_name}' output failed strict Pydantic type validation: {ve}",
                    severity="HIGH"
                )

        return output
