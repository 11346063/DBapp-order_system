import phonenumbers
from phonenumbers import PhoneNumberType, NumberParseException


class PhoneValidationError(ValueError):
    pass


def normalize_tw_mobile(phone_number):
    raw = (phone_number or "").strip()
    if not raw:
        return ""

    try:
        parsed = phonenumbers.parse(raw, "TW")
    except NumberParseException as exc:
        raise PhoneValidationError from exc

    if not phonenumbers.is_valid_number(parsed):
        raise PhoneValidationError
    if phonenumbers.region_code_for_number(parsed) != "TW":
        raise PhoneValidationError
    if phonenumbers.number_type(parsed) != PhoneNumberType.MOBILE:
        raise PhoneValidationError

    national_number = str(parsed.national_number)
    if not national_number.startswith("9") or len(national_number) != 9:
        raise PhoneValidationError

    return f"0{national_number}"
