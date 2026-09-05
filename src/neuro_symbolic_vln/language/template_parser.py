from __future__ import annotations

import re

from neuro_symbolic_vln.contracts import (
    GoalProgram,
    GroundAtom,
    ParseResult,
    ParseStatus,
)

# 1. Standard Vocabulary
COLORS = r"(?P<color>red|green|blue|yellow|purple|grey)"
OBJECT_TYPES = r"(?P<object>ball|box|key)"
GOTO_VERBS = r"(?:go to|find|move to|reach|navigate to|walk to)"
PICKUP_VERBS = r"(?:pick up|get|grab|take|collect)"
OPEN_VERBS = r"(?:open|unlock)"
GOAL_VERBS = r"(?:go to|reach|move to|navigate to)"

# 2. Regex for GoTo Missions
_GOTO_REGEX = re.compile(
    rf"^{GOTO_VERBS}\s+(?:the|a|an)\s+{COLORS}\s+{OBJECT_TYPES}$",
    flags=re.IGNORECASE,
)

# 3. Regex for Key-Door-Goal Missions
_KEY_DOOR_REGEX = re.compile(
    rf"^{PICKUP_VERBS}\s+(?:the|a)\s+(?P<key_color>red|green|blue|yellow|purple|grey)\s+key"
    r"[,]?\s*(?:and\s+then|and|then)?\s*"
    rf"{OPEN_VERBS}\s+(?:the|a)\s+(?P<door_color>red|green|blue|yellow|purple|grey)\s+door"
    r"[,]?\s*(?:and\s+then|and|,?\s*then)\s*"
    rf"{GOAL_VERBS}\s+the\s+goal$",
    flags=re.IGNORECASE,
)

# 4. Regex for detecting AMBIGUOUS instructions
_AMBIGUOUS_MISSING_COLOR_GOTO = re.compile(
    rf"^{GOTO_VERBS}\s+(?:the|a|an)\s+(?:ball|box|key|door)$",
    flags=re.IGNORECASE,
)
_AMBIGUOUS_MISSING_COLOR_DOOR = re.compile(
    rf"^{OPEN_VERBS}\s+(?:the|a)\s+door\b",
    flags=re.IGNORECASE,
)
_AMBIGUOUS_MULTIPLE_KEYS = re.compile(
    r"\bkey\b.*\b(?:then|and)\b.*\bkey\b",
    flags=re.IGNORECASE,
)
_AMBIGUOUS_MULTIPLE_DOORS = re.compile(
    r"\bdoor\b.*\b(?:then|and)\b.*\bdoor\b",
    flags=re.IGNORECASE,
)
_AMBIGUOUS_ORDER_CONFLICT = re.compile(
    r"\bopen\b.*\bthen\b.*\b(?:pick up|get|grab|take|collect)\b",
    flags=re.IGNORECASE,
)

# 5. UNSUPPORTED keywords
_SPATIAL_KEYWORDS = (
    "left of",
    "right of",
    "next to",
    "behind",
    "in front of",
    "near",
    "adjacent to",
    "beside",
)
_CONDITIONAL_KEYWORDS = ("if ", "otherwise", "unless", "when ")
_UNSUPPORTED_ACTIONS = ("put", "drop", "push", "pull", "throw", "close")


def normalize_instruction(text: str) -> str:
    """Normalizes whitespace, casing and trailing punctuation."""
    cleaned = text.strip().rstrip(".!?,;").lower()
    return " ".join(cleaned.split())


def parse_instruction(instruction: str) -> ParseResult:
    """
    Parses a natural language instruction into a typed GoalProgram or failure reason.
    Deterministic, finite and contains no floating-point confidence scores.
    """
    norm_ins = normalize_instruction(instruction)
    if not norm_ins:
        return ParseResult(
            status=ParseStatus.UNSUPPORTED,
            goal_program=None,
            alternatives=(),
            reason="EMPTY_INSTRUCTION",
        )

    # 1. Checks UNSUPPORTED keywords
    for kw in _CONDITIONAL_KEYWORDS:
        if kw in norm_ins:
            return ParseResult(
                status=ParseStatus.UNSUPPORTED,
                goal_program=None,
                alternatives=(),
                reason="UNSUPPORTED_CONDITIONAL",
            )

    for kw in _SPATIAL_KEYWORDS:
        if kw in norm_ins:
            return ParseResult(
                status=ParseStatus.UNSUPPORTED,
                goal_program=None,
                alternatives=(),
                reason="UNSUPPORTED_SPATIAL_RELATION",
            )

    for action in _UNSUPPORTED_ACTIONS:
        if re.search(rf"\b{action}\b", norm_ins):
            return ParseResult(
                status=ParseStatus.UNSUPPORTED,
                goal_program=None,
                alternatives=(),
                reason="UNSUPPORTED_ACTION",
            )

    # 2. Checks AMBIGUOUS keywords
    if _AMBIGUOUS_MULTIPLE_KEYS.search(norm_ins):
        return ParseResult(
            status=ParseStatus.AMBIGUOUS,
            goal_program=None,
            alternatives=(),
            reason="AMBIGUOUS_MULTIPLE_HELD_OBJECTS",
        )

    if _AMBIGUOUS_MULTIPLE_DOORS.search(norm_ins):
        return ParseResult(
            status=ParseStatus.AMBIGUOUS,
            goal_program=None,
            alternatives=(),
            reason="AMBIGUOUS_MULTIPLE_DOORS",
        )

    if _AMBIGUOUS_MISSING_COLOR_GOTO.match(
        norm_ins
    ) or _AMBIGUOUS_MISSING_COLOR_DOOR.search(norm_ins):
        return ParseResult(
            status=ParseStatus.AMBIGUOUS,
            goal_program=None,
            alternatives=(),
            reason="AMBIGUOUS_MISSING_COLOR",
        )

    # Reverse order: opening door before picking up key
    if _AMBIGUOUS_ORDER_CONFLICT.search(norm_ins):
        return ParseResult(
            status=ParseStatus.AMBIGUOUS,
            goal_program=None,
            alternatives=(),
            reason="AMBIGUOUS_ORDER_CONFLICT",
        )

    # 3. Match the GoTo grammar
    match_goto = _GOTO_REGEX.match(norm_ins)
    if match_goto:
        color = match_goto.group("color").lower()
        obj = match_goto.group("object").lower()
        program = GoalProgram(
            family="goto_type_color",
            ordered_subgoals=(GroundAtom("goto-target", (color, obj)),),
        )

        return ParseResult(
            status=ParseStatus.DETERMINISTIC,
            goal_program=program,
            alternatives=(),
            reason=None,
        )

    # 4. Match the Key-Door-Goal grammar
    match_kd = _KEY_DOOR_REGEX.match(norm_ins)
    if match_kd:
        key_color = match_kd.group("key_color").lower()
        door_color = match_kd.group("door_color").lower()
        program = GoalProgram(
            family="key_door_goal",
            ordered_subgoals=(
                GroundAtom("pickup-key", (key_color, "key")),
                GroundAtom("open-door", (door_color, "door")),
                GroundAtom("reach-goal", ()),
            ),
        )

        return ParseResult(
            status=ParseStatus.DETERMINISTIC,
            goal_program=program,
            alternatives=(),
            reason=None,
        )

    # 5. If no pattern matches in grammar
    return ParseResult(
        status=ParseStatus.UNSUPPORTED,
        goal_program=None,
        alternatives=(),
        reason="OUT_OF_GRAMMAR",
    )


class TemplateInstructionParser:
    """Protocol-compliant wrapper for instruction parsing."""

    def parse(self, instruction: str) -> ParseResult:
        return parse_instruction(instruction)
