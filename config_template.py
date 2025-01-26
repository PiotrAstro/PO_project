# create config.py from this template

RUN_CONFIG = {
    "debug": True,
    "host": "127.0.0.1",
    "port": 5000
}


class Config:
    SQLALCHEMY_DATABASE_URI = 'postgresql://username:password@localhost:5432/mydatabase'  # Replace with actual credentials
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "fgtershbgdrfhnyt"


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://username:password@localhost/test_db'  # another db with the same structure but for testing
    WTF_CSRF_ENABLED = False
    SECRET_KEY = ""
