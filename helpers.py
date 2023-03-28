from email_validator import validate_email, EmailNotValidError


def check_email(email):
    try:
        validate = validate_email(email)
        email = validate["email"]
    except EmailNotValidError:
        return False
    return True

def conv_tup_to_str(tup):
    string = ''
    if tup != None:
        string.join(tup)
    return string