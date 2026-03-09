from setuptools import setup, find_packages
import os

here = os.path.dirname(os.path.abspath(__file__))
parent = os.path.dirname(here)

import importlib.util
if os.path.basename(here) == "shared":
    
    packages = ["shared"] + [
        "shared." + p for p in find_packages(where=here)
    ]
    package_dir = {"shared": here, "": parent}
else:
    packages = find_packages(where=here)
    package_dir = {"": here}

setup(
    name="shared",
    version="0.1.0",
    packages=packages,
    package_dir=package_dir,
    install_requires=[
        "pydantic[email]>=2.5.0",
        "pydantic-settings>=2.1.0",
        "sqlalchemy>=2.0.23",
        "psycopg2-binary>=2.9.9",
        "python-jose[cryptography]>=3.3.0",
        "passlib[bcrypt]>=1.7.4",
        "redis>=5.0.1",
        "motor>=3.3.2",
        "aiohttp>=3.9.1",
        "cryptography",
        "google-generativeai>=0.4.0",
    ],
)
