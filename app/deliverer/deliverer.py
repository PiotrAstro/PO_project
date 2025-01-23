from typing import Optional
from app.models import Deliverer


def get_user(login: str, password: str) -> Optional[Deliverer]:
    # This function should return the user id if the login and password are correct, otherwise return None
    user = Deliverer.query.filter_by(login=login, password=password).first()
    return user