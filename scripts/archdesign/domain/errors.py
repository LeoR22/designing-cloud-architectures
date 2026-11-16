"""Domain errors. Messages must tell the caller how to fix the problem."""


class SpecError(ValueError):
    """An input spec is malformed or inconsistent."""
