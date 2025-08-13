# api/utils/playstation.py
import re
from psnawp_api import PSNAWP
from django.conf import settings

# Load from Django settings
# PLAYSTATION_API_KEY = getattr(settings, "PLAYSTATION_API_KEY", None)
PLAYSTATION_API_KEY = "vdqKgop2LlTQHfyXoDRRBvq7JBZp3ko9xYnYz8v7FOSY2ZQ0y3nEi876bMbpkV0w"

# Initialize PSNAWP only once
psnawp = PSNAWP(PLAYSTATION_API_KEY)


def is_valid_gamertag_format(gamertag: str) -> bool:
    """
    Validates PlayStation (or Xbox-style) Gamertag format:
    - Optional '@' at start
    - Letters, numbers, underscores, spaces allowed
    - 1–15 characters (excluding @)
    - No double underscores
    - No underscore at the end
    - No letter+underscore+digit or digit+underscore+letter in a single word
    """
    if not gamertag:
        return False

    # @ allowed only at the start
    if "@" in gamertag[1:]:
        return False

    # Strip leading @ for validation
    actual_tag = gamertag[1:] if gamertag.startswith("@") else gamertag

    # Check length and allowed characters (1-15 chars)
    if not re.fullmatch(r"[A-Za-z0-9_ ]{1,15}", actual_tag):
        return False

    # No ending underscore
    if actual_tag.endswith("_"):
        return False

    # No double underscores
    if "__" in actual_tag:
        return False

    # No letter_+digit or digit_+letter
    if re.search(r"[A-Za-z]_[0-9]", actual_tag) or re.search(r"[0-9]_[A-Za-z]", actual_tag):
        return False

    return True


def get_playstation_profile(gamertag: str):
    """
    Fetch a PlayStation user's profile after validating format.
    :param gamertag: PlayStation online ID (gamertag)
    :return: dict with profile info or error message
    """
    gamertag = gamertag.strip()

    if not gamertag:
        return {"success": False, "error": "PS Gamertag is required", "error_type": "invalid_format"}

    # Step 1: Format validation
    if not is_valid_gamertag_format(gamertag):
        return {
            "success": False,
            "error": "Invalid gamertag format",
            "error_type": "invalid_format"
        }
    
    api_gamertag = gamertag[1:] if gamertag.startswith(("@", "_")) else gamertag

    try:
        # Step 2: Fetch from API
        user = psnawp.user(online_id=api_gamertag)
        profile = user.profile()
        profile["accountId"] = user.account_id
        return {
            "success": True,
            "gamertag_found": api_gamertag,
            "data": profile
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "api_error"
        }
