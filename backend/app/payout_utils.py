from __future__ import annotations

import re

IFSC_PATTERN = re.compile(r"^[A-Z]{4}0[A-Z0-9]{6}$")


def is_valid_ifsc(value: str | None) -> bool:
    return bool(value and IFSC_PATTERN.match(value.strip().upper()))


def is_valid_upi(value: str | None) -> bool:
    if not value:
        return False

    upi = value.strip()
    if "@" not in upi or " " in upi:
        return False

    left, right = upi.split("@", 1)
    return bool(left and right)


def mask_bank_account(account_number: str | None) -> str | None:
    if not account_number:
        return None

    digits = str(account_number).strip()
    if len(digits) <= 4:
        return "X" * len(digits)

    return f"{'X' * (len(digits) - 4)}{digits[-4:]}"
