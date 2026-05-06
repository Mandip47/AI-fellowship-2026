import os
from dynaconf import Dynaconf

HERE = os.path.dirname(os.path.abspath(__file__))
settings_path = os.path.join(HERE, "configs/settings.yaml")

# Check if the file actually exists where we think it is
if not os.path.exists(settings_path):
    print(f"⚠️ WARNING: Config file not found at {settings_path}")

settings = Dynaconf(
    envvar_prefix="DYNACONF",
    settings_files=[settings_path, os.path.join(HERE, "configs/.secrets.yaml")],
    environments=True,
    load_dotenv=True,
)
