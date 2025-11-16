call i:\Language_helper\api\.venv\Scripts\activate.bat

ruff check --fix .
ruff format .

call i:\Language_helper\api\.venv\Scripts\deactivate.bat
