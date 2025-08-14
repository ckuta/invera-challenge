#!/usr/bin/env python
import os
import sys
from pathlib import Path



def main():
    """Creates a .env file with default values if it does not exist"""
    base_dir = Path(__file__).resolve().parent.parent.parent
    env_file_path = base_dir / '.env'

    # Check if the .env file already exists
    if env_file_path.exists():
        if "--force" not in sys.argv:
            print(f"The .env file already exists at {env_file_path}")
            print("Use --force to overwrite it")
            return
        else:
            print(f"Overwriting the existing .env file...")

    # Determine if we're running in Docker or locally
    in_docker = "--docker" in sys.argv

    if in_docker:
        # Default content for the .env file
        env_content = """# Auto-generated .env file
        
# Django Configuration
DEBUG=True
SECRET_KEY=django-insecure-development-key-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,[::1]

# Database Configuration
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
DB_CONN_MAX_AGE=60

# Other Configurations
TIME_ZONE=UTC
LANGUAGE_CODE=en-en
"""
    else:
        env_content = """# Auto-generated .env file
        
# Django Configuration
DEBUG=True
SECRET_KEY=django-insecure-development-key-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,[::1]

# Database Configuration
DATABASE_URL=sqlite:///db.sqlite3

# Other Configurations
TIME_ZONE=UTC
LANGUAGE_CODE=en-en
"""


    # Write the .env file
    with open(env_file_path, 'w') as f:
        f.write(env_content)

    print(f".env file created at {env_file_path}")

    example_env_path = base_dir / '.env.example'
    with open(example_env_path, 'w') as f:
        f.write(env_content)
    print(f".env.example file created at {example_env_path}")

if __name__ == "__main__":
    main()