from email_validator import validate_email, EmailNotValidError
from flask import redirect, request, session
from functools import wraps

# Function to check if email is valid
def check_email(email):
    try:
        validate = validate_email(email)
        email = validate["email"]
    except EmailNotValidError:
        return False
    return True

# Function to convert tuple to string, if tuple is empty, it returns None
def conv_tup_to_str(tup):
    if tup != None:
        string = ''.join(tup)
        return string
    else:
        return None

# Login requirement decorator for routs in app
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function