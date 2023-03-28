from email_validator import validate_email, EmailNotValidError


def check(email):
    try:
        validate = validate_email(email)
        email = validate["email"]
    except EmailNotValidError:
        return False
    return True
