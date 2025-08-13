import re
import requests
from django.conf import settings

# OPENXBL_API_KEY = getattr(settings, "OPENXBL_API_KEY", "b8af71b4-6bb4-4eb7-b4ab-7a510082177a")
OPENXBL_API_KEY = "b8af71b4-6bb4-4eb7-b4ab-7a510082177a"

def is_valid_gamertag_format(gamertag):
    """
    Validates Xbox Gamertag format:
    - Optional '@' at start
    - Letters, numbers, underscores, spaces allowed
    - 1–15 characters (excluding @)
    - No double underscores
    - No underscore at the end
    - No letter+underscore+digit or digit+underscore+letter in a single word
    """
    # Check if @ appears anywhere other than the start
    if "@" in gamertag[1:]:
        return False
    
    # Remove @ if present for validation of the actual tag
    actual_tag = gamertag[1:] if gamertag.startswith("@") else gamertag
    
    # Check length and allowed characters (1-15 chars for the actual tag)
    if not re.fullmatch(r"[A-Za-z0-9_ ]{1,15}", actual_tag):
        return False
    
    # Check for ending underscore
    if actual_tag.endswith("_"):
        return False
    
    # Check for double underscores
    if "__" in actual_tag:
        return False
    
    # No letter_digit or digit_letter pattern
    if re.search(r"[A-Za-z]_[0-9]", actual_tag) or re.search(r"[0-9]_[A-Za-z]", actual_tag):
        return False
    
    return True


def xbox_gamertag_lookup(gamertag):
    """
    Looks up an Xbox gamertag using the OpenXBL API.
    """
    gamertag = gamertag.strip()

    if not gamertag:
        return {"success": False, "error": "Xbox Gamertag is required", "error_type": "invalid_format"}

    if not is_valid_gamertag_format(gamertag):
        return {"success": False, "error": "Invalid Xbox Gamertag format", "error_type": "invalid_format"}

    api_gamertag = gamertag[1:] if gamertag.startswith("@") else gamertag

    try:
        url = f"https://xbl.io/api/v2/search/{api_gamertag}"
        headers = {"X-Authorization": OPENXBL_API_KEY}
        response = requests.get(url, headers=headers, timeout=5)

        if response.status_code == 200:
            data = response.json()
            if data.get("people"):
                return {"success": True, "gamertag_found": gamertag, "data": data}
            else:
                return {"success": False, "error": "Gamertag not found", "error_type": "not_found"}
        else:
            return {
                "success": False,
                "error": f"Error from Xbox API (status {response.status_code})",
                "error_type": "api_error"
            }

    except Exception as e:
        return {"success": False, "error": str(e), "error_type": "exception"}
    




