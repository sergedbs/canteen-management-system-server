import re


def extract_name_from_email(email: str):
    """
    Extract first and last name from an email like first.last@*.utm.md
    Handles:
    - missing last/first - returns empty string
    - multi-part names (ana-maria) - capitalizes each part
    - strips numbers and special chars
    """
    local_part = email.split("@")[0]
    parts = local_part.split(".")

    first_raw = parts[0] if len(parts) > 0 else ""
    last_raw = parts[1] if len(parts) > 1 else ""

    def clean_name(name: str):
        name = re.sub(r"[^a-zA-Z\-]", "", name)
        return "-".join([p.capitalize() for p in name.split("-")])

    first_name = clean_name(first_raw)
    last_name = clean_name(last_raw)

    return first_name, last_name
