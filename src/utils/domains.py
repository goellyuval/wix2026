import re
import uuid

# A domain that will stay registered for the life of this project.
TAKEN_DOMAIN = "google.com"

# Values the docs list for availability.premiumType.
DOCUMENTED_PREMIUM_TYPES = {"FIRST_YEAR_ONLY", "FIRST_YEAR_AND_RENEWAL"}

# name.tld (tld may be multi-part, e.g. co.il); labels are letters/digits/hyphens, no edge hyphens.
_DOMAIN_PATTERN = re.compile(r"^(?!-)[a-z0-9-]{1,63}(?<!-)(\.[a-z]{2,63})+$")


def random_unregistered_domain(tld: str = "com") -> str:
    """Random name that is practically guaranteed to be free (availability is point-in-time)."""
    return f"qa-{uuid.uuid4().hex[:12]}.{tld}"


def is_full_domain(value: str) -> bool:
    """True for a lowercase name + TLD, e.g. 'mybakery.com' or 'mybakery.co.il'."""
    return bool(_DOMAIN_PATTERN.match(value))
