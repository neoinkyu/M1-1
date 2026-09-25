from pathlib import Path

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials


# 프로젝트 루트 경로
BASE_DIR = Path(__file__).resolve().parents[1]

# 로컬 개발환경용 서비스 계정 JSON
CREDENTIALS_FILE = (
    BASE_DIR
    / "credentials"
    / "service_account.json"
)

# Google Sheets 문서 ID
SPREADSHEET_ID = (
    "1p79GKh8h_wNYzG4mR-DJIxesynrVoFghRw3cSQLI4xk"
)

# 읽기 전용 권한
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


def get_google_sheets_client():
    """
    로컬에서는 service_account.json을 사용하고,
    Streamlit Cloud에서는 st.secrets를 사용한다.
    """

    # 1. 로컬 개발환경
    if CREDENTIALS_FILE.exists():
        credentials = (
            Credentials.from_service_account_file(
                CREDENTIALS_FILE,
                scopes=SCOPES,
            )
        )

    # 2. Streamlit Community Cloud
    else:
        try:
            import streamlit as st

            service_account_info = dict(
                st.secrets["gcp_service_account"]
            )

            credentials = (
                Credentials.from_service_account_info(
                    service_account_info,
                    scopes=SCOPES,
                )
            )

        except Exception as error:
            raise RuntimeError(
                "Google 서비스 계정 인증정보를 "
                "찾을 수 없습니다."
            ) from error

    return gspread.authorize(credentials)


def load_sheet(sheet_name):
    """
    지정한 Google Sheets 탭을
    pandas DataFrame으로 불러온다.
    """

    client = get_google_sheets_client()

    spreadsheet = client.open_by_key(
        SPREADSHEET_ID
    )

    worksheet = spreadsheet.worksheet(
        sheet_name
    )

    data = worksheet.get_all_records()

    return pd.DataFrame(data)


def main():
    """Google Sheets 연결 테스트."""

    print("Google Sheets 연결 테스트")
    print("-" * 50)

    daily_stats = load_sheet(
        "daily_stats"
    )

    gsc_daily = load_sheet(
        "gsc_daily"
    )

    print("\n[daily_stats]")
    print(f"행 수: {len(daily_stats)}")
    print(
        f"컬럼: "
        f"{list(daily_stats.columns)}"
    )

    print("\n[gsc_daily]")
    print(f"행 수: {len(gsc_daily)}")
    print(
        f"컬럼: "
        f"{list(gsc_daily.columns)}"
    )


if __name__ == "__main__":
    main()