from itsdangerous import URLSafeTimedSerializer
from os import environ, path
from dotenv import load_dotenv


def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer('EWRWREREDD3435435AEWREREEETETETETEESDSFSF')
    return serializer.dumps(email, salt=environ.get('SECURITY_PASSWORD_SALT'))


def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer('EWRWREREDD3435435AEWREREEETETETETEESDSFSF')
    try:
        email = serializer.loads(
            token,
            salt=environ.get('SECURITY_PASSWORD_SALT'),
            max_age=expiration
        )
    except:
        return False
    return email