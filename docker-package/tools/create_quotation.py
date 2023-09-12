import pickle
import os.path
from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

load_dotenv()
google_scope = os.getenv('GOOGLE_SCOPES', None)
list_of_google_scope = google_scope.split(",")
temp_workbook_id = os.getenv('TEMP_WORKBOOK_ID', None)

def get_creds():
    # print(f'測試scope: {google_scope}')
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        # if creds and creds.expired and creds.refresh_token:
        #     creds.refresh(Request())
        # else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'config/credentials.json', list_of_google_scope)
        creds = flow.run_local_server(port=0)

        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds


def get_sheet_id_by_title(workbook_id, sheet_title, creds):
    sheets_service = build('sheets', 'v4', credentials=creds)
    response = sheets_service.spreadsheets().get(
        spreadsheetId=workbook_id).execute()

    for sheet in response['sheets']:
        if sheet["properties"]["title"] == sheet_title:
            return sheet["properties"]["sheetId"]

    raise ValueError(
        f"No sheet with title '{sheet_title}' found in spreadsheet!")


def copy_sheet(creds, temp_workbook_id):
    drive_service = build('drive', 'v3', credentials=creds)

    # 使用Drive API複製Google Sheet
    copied_data = drive_service.files().copy(fileId=temp_workbook_id).execute()
    copy_id = copied_data["id"]

    return copy_id


def update_cells(creds, target_workbook_id, input_dict):
    sheet_service = build('sheets', 'v4', credentials=creds)

    # Update cells
    for cell, value in input_dict.items():
        range_name = f'Quotation_temp!{cell}'
        body = {
            'values': [[value]]
        }

        result = sheet_service.spreadsheets().values().update(
            spreadsheetId=target_workbook_id, range=range_name,
            valueInputOption='RAW', body=body).execute()

    # paste as value
    range_name = 'Quotation_temp'
    result = sheet_service.spreadsheets().values().get(
        spreadsheetId=target_workbook_id, range=range_name).execute()
    values = result.get('values', [])

    if values:
        body = {
            'valueInputOption': 'RAW',
            'data': [
                {
                    "range": range_name,
                    "values": values
                }
            ]
        }
        sheet_service.spreadsheets().values().batchUpdate(
            spreadsheetId=target_workbook_id, body=body).execute()

        print(
            f"Updated {cell} with {value}. {result.get('updatedCells')} cells updated.")


def rename_and_download_as_pdf(target_workbook_id, creds, quotation_name):
    # 建立Google Sheets和Google Drive的服務
    sheets_service = build('sheets', 'v4', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)

    # 修改複製的Sheet的文件名稱
    drive_service.files().update(fileId=target_workbook_id,
                                 body={"name": quotation_name}).execute()

    # 修改複製的Sheet的Sheet名稱
    copied_sheet_id = get_sheet_id_by_title(
        target_workbook_id, "Quotation_temp", creds)
    sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=target_workbook_id,
        body={
            "requests": [
                {
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": copied_sheet_id,  # 此處的0表示第一個工作表，如果你的Google Sheet有多個工作表，你可能需要根據情況調整此值。
                            "title": quotation_name
                        },
                        "fields": "title"
                    }
                }
            ]
        }).execute()

    # 將複製的Sheet轉換為PDF
    request = drive_service.files().export_media(
        fileId=target_workbook_id, mimeType='application/pdf')
    response = request.execute()

    # 下載PDF文件
    with open(f"output/{quotation_name}.pdf", 'wb') as f:
        f.write(response)

    return f"output/{quotation_name}.pdf"