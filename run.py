from app import create_app
from app.config import RUN_CONFIG

app = create_app()

if __name__ == "__main__":
    app.run(**RUN_CONFIG)