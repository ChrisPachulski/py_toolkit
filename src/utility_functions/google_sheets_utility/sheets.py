from token import STRING
import time
import re, os
import pandas as pd
import numpy as np
import gspread as gs
from gspread_pandas import Spread
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv
from .common import _get_env_path 

def create_or_update_google_sheet(share_with = STRING, df=pd.DataFrame, workbook_name=STRING, sheet_name=STRING, interactive = False, service_account_path=STRING):
    """
    Create or locate a Google Sheets workbook and write data into a specified sheet using 
    any Service Account. 

    If the specified workbook does not exist, a new one is created and shared with the provided email address.
    The function also removes the default 'Sheet1' if it is not being used to avoid clutter.

    Parameters:
    - share_with (str, optional): Email address(es) to share the Google Sheet with. Multiple emails can be separated by commas. Defaults to STRING.
    - df (pd.DataFrame, optional): DataFrame to write into the Google Sheet. Defaults to an empty pd.DataFrame.
    - workbook_name (str, optional): Name of the Google Sheet workbook to create or locate. Defaults to STRING.
    - sheet_name (str, optional): Name of the sheet within the workbook to write data into. Defaults to STRING.
    - interactive (bool, optional): Flag to control whether to prompt the user for overwriting an existing sheet. Defaults to False.

    Returns:
    - None: The function prints out the URL of the created or located workbook for quick access.

    Side Effects:
    - Creates or updates a Google Sheets workbook and associated sheet.
    - Optionally shares the workbook with specified email address(es).
    - Prints status messages and workbook URL to the console.

    Examples:
    >>> gs_creation(share_with='example@example.com', df=my_dataframe, workbook_name='MyWorkbook', sheet_name='MySheet', interactive=True)
    [Output will be various status messages and the workbook URL]

    Notes:
    - Ensure that Google Sheets API is enabled and OAuth2 credentials are properly set up.
    - This function does not allow the existence of a default 'Sheet1'; a sheet name must be deliberately specified.
    """
    load_dotenv(dotenv_path=_get_env_path())
    if service_account_path == None:
        service_account_path=os.getenv('GOOGLE_SERVICE_ACCOUNT_PATH')
        
    # Attempt to read in the desired workbook
    try:
        # If that workbook exists, verify the desired sheet exists
        wkb = Spread(workbook_name)
        if wkb.find_sheet(sheet=sheet_name) == None:

            # Logic has now verified the sheet does not exists in existing workbook
            wkb.df_to_sheet(
                df=df, sheet=sheet_name, freeze_headers=True, add_filter=True, index=False
            )
            ss = wkb.client.open(wkb.spread.title)
            sheetId = ss.worksheet(sheet_name)._properties["sheetId"]
            body = {
                "requests": [
                    {
                        "autoResizeDimensions": {
                            "dimensions": {
                                "sheetId": sheetId,
                                "dimension": "COLUMNS",
                                "startIndex": 0,  # Please set the column index.
                                "endIndex": df.shape[1]
                                + 1,  # Please set the column index.
                            }
                        }
                    }
                ]
            }
            res = ss.batch_update(body)

            # Communicate sheet creation to end user
            print(sheet_name + " has been created!")
            # Always return the wkb url for ease of access
            print(wkb.url)
        elif (interactive == True):
            # Logic has now verified the sheet DOES exist, and the user must approve/deny alterations
            value = input(
                sheet_name + " already exists in " +workbook_name+" would you like to over-write the existing sheet?"
            )
            value = value.lower()

            if value == "yes":
                # Clear existing sheet
                wkb.clear_sheet(1, 1, sheet_name)
                # Write in new data over now empty sheet
                wkb.df_to_sheet(
                    df=df, sheet=sheet_name, freeze_headers=True, add_filter=True, index=False
                )
                ss = wkb.client.open(wkb.spread.title)
                sheetId = ss.worksheet(sheet_name)._properties["sheetId"]
                body = {
                    "requests": [
                        {
                            "autoResizeDimensions": {
                                "dimensions": {
                                    "sheetId": sheetId,
                                    "dimension": "COLUMNS",
                                    "startIndex": 0,  # Please set the column index.
                                    "endIndex": df.shape[1]
                                    + 1,  # Please set the column index.
                                }
                            }
                        }
                    ]
                }
                res = ss.batch_update(body)
                # Communicate sheet creation to end user
                print(sheet_name+" has been updated!")
                # Always return the wkb url for ease of access
                print(wkb.url)
            elif value == "no":
                # Communicate sheet was not altered to end user
                print(sheet_name+" was not over written.")
                # Always return the wkb url for ease of access
                print(wkb.url)
            else:
                # Provide Direction for User if they made an error or are new
                print('Please answer "Yes" or "No" and try again.')
        elif(interactive == False):
            print('Interactive Sheet Overwrite Logic has been declined.')
            wkb.clear_sheet(1, 1, sheet_name)
            # Write in new data over now empty sheet
            wkb.df_to_sheet(df=df, sheet=sheet_name, freeze_headers=True, add_filter=True, index=False)
            ss = wkb.client.open(wkb.spread.title)
            sheetId = ss.worksheet(sheet_name)._properties["sheetId"]
            body = {
                "requests": [
                    {
                        "autoResizeDimensions": {
                            "dimensions": {
                                "sheetId": sheetId,
                                "dimension": "COLUMNS",
                                "startIndex": 0,  # Please set the column index.
                                "endIndex": df.shape[1]
                                + 1,  # Please set the column index.
                            }
                        }
                    }
                ]
            }
            res = ss.batch_update(body)
            # Communicate sheet creation to end user
            print(sheet_name+" has been updated!")
            # Always return the wkb url for ease of access
            print(wkb.url)
        else:
            print('Please set interactive = True & answer "Yes" or "No", otherwise set interactive = False &  try again.')
    except:
        # Workbook was not discovered in the google drive, logic defaults to creation of the desired workbook
        # Potential room for improvement would be to prompt the user, ensuring they did not make an error
        print("Unable to find Workbook, Creating "+workbook_name+" now")

        # Source service account secrets to obtain permission to create new workbook
        
        gc = gs.service_account(service_account_path)
        sh = gc.create(workbook_name)
        
        share_list = re.split(r'\s*,\s*',share_with)
        # Immediately share with self - potentially need to offer user ability to share with others
        # This will also generate an email informing the end user of the workborks creation
        for user in share_list:
            sh.share(user, perm_type="user", role="writer")
            print("Shared with user:", user)
            time.sleep(0.25)  # Provide a slight wait between sharing

        time.sleep(1)
        
        # Provide slight wait to allow for creation and recognition of creation
        wkb = Spread(workbook_name)

        # Write data to desire sheet
        wkb.df_to_sheet(df=df, sheet=sheet_name, freeze_headers=True, add_filter=True, index=False)
        ss = wkb.client.open(wkb.spread.title)
        sheetId = ss.worksheet(sheet_name)._properties["sheetId"]
        body = {
            "requests": [
                {
                    "autoResizeDimensions": {
                        "dimensions": {
                            "sheetId": sheetId,
                            "dimension": "COLUMNS",
                            "startIndex": 0,  # Please set the column index.
                            "endIndex": df.shape[1] + 1,  # Please set the column index.
                        }
                    }
                }
            ]
        }
        res = ss.batch_update(body)
        # Every new workbook must* have one spreadsheet to exist
        # After writing in our desired data, if user does not expressly
        # wish to write to the default `Sheet1`, remove the un-needed default sheet
        if sheet_name != "Sheet1":
            wkb.delete_sheet("Sheet1")

        # Communicate workbook & sheet creation to end user
        spreadsheet_url = "https://docs.google.com/spreadsheets/d/%s" % sh.id
        print(sheet_name+" has been created inside of "+workbook_name+"!")
        # Always return the wkb url for ease of access
        print(spreadsheet_url)


def auto_resize_columns(spreadsheet_id, sheet_name, service_account_path=STRING):
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    SERVICE_ACCOUNT_FILE = service_account_path

    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    service = build('sheets', 'v4', credentials=credentials)
    sheet = service.spreadsheets()

    # Get the sheet ID and the number of columns
    sheet_metadata = sheet.get(spreadsheetId=spreadsheet_id).execute()
    sheets = sheet_metadata.get('sheets', '')
    sheet_id = None
    max_columns = 0
    for s in sheets:
        if s.get("properties", {}).get("title", "") == sheet_name:
            sheet_id = s.get("properties", {}).get("sheetId", "")
            # Get the number of columns
            grid_properties = s.get('properties', {}).get('gridProperties', {})
            max_columns = grid_properties.get('columnCount', 0)
            break

    if sheet_id is None:
        raise Exception(f"Sheet with name '{sheet_name}' not found")

    # Auto-resize columns
    body = {
        "requests": [
            {
                "autoResizeDimensions": {
                    "dimensions": {
                        "sheetId": sheet_id,
                        "dimension": "COLUMNS",
                        "startIndex": 0,
                        "endIndex": max_columns
                    }
                }
            }
        ]
    }
    
    sheet.batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()

    # Retrieve the resized column widths and adjust if necessary
    sheet_metadata = sheet.get(spreadsheetId=spreadsheet_id, ranges=[sheet_name], fields="sheets(data/columnMetadata)").execute()
    columns_metadata = sheet_metadata['sheets'][0]['data'][0]['columnMetadata']
    
    for index, col in enumerate(columns_metadata):
        pixel_size = col.get('pixelSize', 100) + 10  # Add extra pixels for filter icon
        body = {
            "requests": [
                {
                    "updateDimensionProperties": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "COLUMNS",
                            "startIndex": index,
                            "endIndex": index + 1
                        },
                        "properties": {
                            "pixelSize": pixel_size
                        },
                        "fields": "pixelSize"
                    }
                }
            ]
        }
        sheet.batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()

    return "Columns auto-resized successfully."


def read_sheet(workbook_name, sheet_name, service_account_path=STRING):
    """
    Wrapper function to read a google sheet into a DataFrame (Largely Unneeded):
    """
    load_dotenv(dotenv_path=_get_env_path())
    if service_account_path == None:
        service_account_path=os.getenv('GOOGLE_SERVICE_ACCOUNT_PATH')
    try:
        wkb = Spread(workbook_name, user=service_account_path)
        df = wkb.sheet_to_df(sheet=sheet_name)
        return df
    except Exception as e:
        print(f"Error reading {sheet_name} in {workbook_name}: {e}")
        return pd.DataFrame()


