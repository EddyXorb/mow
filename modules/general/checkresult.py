from dataclasses import dataclass


@dataclass
class CheckResult:
    """
    General purpose check return type.
    ok: indicates if check was successful
    error: reason for why check was unsuccesful
    """

    ok: bool
    error: str = ""
