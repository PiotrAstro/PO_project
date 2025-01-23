from typing import Optional
from app.models import Client


def get_user(login: str, password: str) -> Optional[Client]:
    # This function should return the user id if the login and password are correct, otherwise return None
    user = Client.query.filter_by(login=login, password=password).first()
    return user
