"""
ArgusCX -- Challenge Generator
Generates nonce-seeded, deterministic-per-session challenge sequences.
Sequence is unpredictable to attackers (nonce is secret),
reproducible for debugging.
"""
import hashlib
import random
import secrets
from typing import List
from pydantic import BaseModel

CHALLENGE_POOL = [
    {"type": "SHOW_FRONT",     "instruction": "Hold the product facing the camera clearly.",      "required_action": "show_front"},
    {"type": "SHOW_BACK",      "instruction": "Flip the product and show us the back.",           "required_action": "show_back"},
    {"type": "MOVE_LEFT",      "instruction": "Slowly move the camera to the LEFT.",              "required_action": "move_left"},
    {"type": "MOVE_RIGHT",     "instruction": "Slowly move the camera to the RIGHT.",             "required_action": "move_right"},
    {"type": "MOVE_UP",        "instruction": "Slowly tilt the camera UPWARD.",                   "required_action": "move_up"},
    {"type": "FOCUS_SERIAL",   "instruction": "Find the serial/IMEI and hold the camera over it.","required_action": "focus_serial"},
    {"type": "SHOW_PACKAGING", "instruction": "Show the product packaging.",                      "required_action": "show_packaging"},
    {"type": "SHOW_DAMAGE",    "instruction": "Move close to show any damage.",                   "required_action": "show_damage"},
    {"type": "ROTATE_PRODUCT", "instruction": "Slowly rotate the product 360 degrees.",           "required_action": "rotate_product"},
]

DEFAULT_CHALLENGE_COUNT = 5


class ChallengeStep(BaseModel):
    step_index: int
    challenge_type: str
    instruction_text: str
    required_action: str


def generate_session_nonce() -> str:
    return secrets.token_hex(32)


def generate_challenge_sequence(
    nonce: str,
    count: int = DEFAULT_CHALLENGE_COUNT,
    require_serial: bool = True,
    require_packaging: bool = False,
) -> List[ChallengeStep]:
    """
    Deterministic challenge sequence seeded from the session nonce.
    SHOW_FRONT is always first. FOCUS_SERIAL is always last if required.
    """
    seed_int = int(hashlib.sha256(nonce.encode()).hexdigest(), 16)
    rng = random.Random(seed_int)

    sequence = [next(c for c in CHALLENGE_POOL if c["type"] == "SHOW_FRONT")]

    movement_types = ["MOVE_LEFT", "MOVE_RIGHT", "MOVE_UP", "SHOW_BACK", "SHOW_DAMAGE", "ROTATE_PRODUCT"]
    avail = [c for c in CHALLENGE_POOL if c["type"] in movement_types]
    rng.shuffle(avail)

    middle_count = count - 1
    if require_serial:
        middle_count -= 1
    if require_packaging:
        middle_count -= 1

    middle = list(avail[:max(middle_count, 0)])

    if require_packaging:
        pkg = next(c for c in CHALLENGE_POOL if c["type"] == "SHOW_PACKAGING")
        middle.insert(rng.randint(0, len(middle)), pkg)

    sequence.extend(middle)

    if require_serial:
        sequence.append(next(c for c in CHALLENGE_POOL if c["type"] == "FOCUS_SERIAL"))

    return [
        ChallengeStep(
            step_index=idx,
            challenge_type=c["type"],
            instruction_text=c["instruction"],
            required_action=c["required_action"],
        )
        for idx, c in enumerate(sequence[:count])
    ]
