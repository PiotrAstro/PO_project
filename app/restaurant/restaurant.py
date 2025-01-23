from typing import Optional
from app.models import Restaurant


def get_user(login: str, password: str) -> Optional[Restaurant]:
    # This function should return the user id if the login and password are correct, otherwise return None
    user = Restaurant.query.filter_by(login=login, password=password).first()
    return user