# py_toolkit

A **modular Python toolkit** housing various utility functions for:
- **Gmail** (sending, authentication, handling)
- **Google Sheets** (creating/updating sheets, reading data)
- **Salesforce** (OAuth, query, reporting)
- **SharePoint** (authentication, file explorer, file uploader)
- **Genesys** (authentication, conversation/user queries, transformations)

Each utility is cleanly separated into its own package under `src/utility_functions/`.

---

## Table of Contents

1. [Project Structure](#project-structure)  
2. [Installation & Environment](#installation--environment)  
3. [Usage](#usage)  
   - [Gmail Utility](#1-gmail-utility)
   - [Google Sheets Utility](#2-google-sheets-utility)
   - [Salesforce Utility](#3-salesforce-utility)
   - [SharePoint Utility](#4-sharepoint-utility)
   - [Genesys Utility](#5-genesys-utility)
4. [Testing](#testing)  
5. [Contributing](#contributing)  
6. [License](#license)

---

## Project Structure
```bash
py_toolkit/ 
├── README.md
├── google_oauth_token.json
├── google_oauth_access_token.json
├── google_service_account.json
├── pyproject.toml
├── requirements.txt
├── src
│   ├── __init__.py
│   └── utility_functions
│       ├── __init__.py
│       ├── genesys_utility
│       │   ├── __init__.py
│       │   ├── auth.py
│       │   ├── common.py
│       │   ├── conversation.py
│       │   ├── conversation_details_query.py
│       │   ├── transformations.py
│       │   └── users.py
│       ├── gmail_utility
│       │   ├── __init__.py
│       │   ├── auth.py
│       │   ├── common.py
│       │   ├── file_handling.py
│       │   ├── inbox.py
│       │   └── send.py
│       ├── google_sheets_utility
│       │   ├── __init__.py
│       │   ├── common.py
│       │   └── sheets.py
│       ├── salesforce_utility
│       │   ├── __init__.py
│       │   ├── auth.py
│       │   ├── common.py
│       │   ├── query.py
│       │   ├── reporting.py
│       │   └── transformations.py
│       └── sharepoint_utility
│           ├── __init__.py
│           ├── auth.py
│           ├── common.py
│           ├── explorer.py
│           └── uploader.py
└── tests
    ├── test_genesys_utility.py
    ├── test_gmail_utility.py
    ├── test_google_sheets_utility.py
    ├── test_salesforce_utility.py
    └── test_sharepoint_utility.py
```

- **`gmail_utility`**: 
  - Sending emails with attachments via Gmail API. 
  - Reviewing Inbox emails and attachments therein.  
- **`google_sheets_utility`**: Creating, reading, updating Google Sheets  
- **`salesforce_utility`**: OAuth flows, SOQL queries, Analytics reporting  
- **`sharepoint_utility`**: Auth, file explorer, and uploading  
- **`genesys_utility`**: Auth, conversation/user queries, transformations  

---

## Installation & Environment

1. **Clone** this repository:

```bash
git clone https://github.com/your-org/py_toolkit.git
cd py_toolkit
# Using pip + requirements.txt
pip install -r requirements.txt
```

2. Install Dependencies (either via requirements.txt or pyproject.toml):
```bash
# Using pip + requirements.txt
pip install -r requirements.txt

# OR using Poetry 
poetry install
```

3. Environment Variables
Many utilities rely on .env files or environment variables for credentials (e.g. SF_REFRESH, MAIN_USER, GENESYS_ACCESS_TOKEN, etc.).
By default, the .env is expected at ~/Documents/py_toolkit/.env.
Adjust or overwrite paths as needed.

## Usage
1. Gmail Utility

```python
from src.utility_functions.gmail_utility.send import gmail_send_message

gmail_send_message(
    data="/path/to/file.csv",     # or pd.DataFrame
    receivers="someone@example.com",
    file_titles="report.csv",
    subject="Daily Report",
    content="Please see attached."
)
```

```python
from src.utility_functions.gmail_utility.inbox import gmail_reports_inbox
gmail_reports_inbox(
    search_query='subject: Super Unique Subject',
    stored_file_path=os.path.join(os.path.expanduser('~'), 'Downloads'),
    multiple_files=False
)

```

2. Google Sheets Utility
```python
from src.utility_functions.google_sheets_utility.sheets import create_or_update_google_sheet

create_or_update_google_sheet(
    share_with="user@example.com",
    df=my_dataframe,
    workbook_name="MyWorkbook",
    sheet_name="Sheet1",
    interactive=False
)
```

3. Salesforce Utility
```
from src.utility_functions.salesforce_utility.query import query_salesforce_soql

# Assuming SF_REFRESH token is stored in .env
df = query_salesforce_soql("SELECT Id, Name FROM Account LIMIT 10")
print(df.head())
```

4. Sharepoint Utility
```python
from src.utility_functions.sharepoint_utility.uploader import upload_file_to_sharepoint

result = upload_file_to_sharepoint(
    base_url="https://mycompany.sharepoint.com",
    site_path="/sites/MySite",
    username="myuser@company.com",
    password="SecretPassword",
    library_title="Documents",
    root_subfolder="General",
    local_file_path="/path/to/file.xlsx"
)
print(result)
```

5. Genesys Utility
```python
from src.utility_functions.genesys_utility.auth import get_genesys_access_token

get_genesys_access_token("CLIENT_ID", "CLIENT_SECRET", "mypurecloud.com")
# This sets genesys.configuration.access_token internally
```

## Testing 
I used pytest for testing. All tests reside under tests/, grouped by integration type (e.g., test_gmail_utility.py for Gmail, etc.).

Run the full test suite:
```bash
python -m pytest tests
```

### Notes:
- Each external API call is mocked. No real network calls occur.
- Credentials and environment variables are mocked or read from .env.

## Contributing
1. Fork the repo & create a new branch.
2. Implement new features or bugfixes in the appropriate utility directory.
3. Add/Update Tests in tests/.
4. Open a Pull Request and link to any related issues.

## License
This project is licensed under the MIT License. Please see LICENSE for details.

