import pandas as pd

from data_loader import load_sheet


def preprocess_daily_stats(df):
    """daily_stats 데이터를 분석 가능한 형태로 정제한다."""
    df = df.copy()

    # 날짜 변환
    df["stat_date"] = pd.to_datetime(df["stat_date"])

    # 숫자형 변환
    numeric_columns = [
        "id",
        "posts",
        "pages",
        "users",
        "pv",
        "adsense_estimated",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    # 날짜순 정렬
    df = df.sort_values("stat_date").reset_index(drop=True)

    return df


def preprocess_gsc_daily(df):
    """gsc_daily 데이터를 분석 가능한 형태로 정제한다."""
    df = df.copy()

    # 날짜 변환
    df["date"] = pd.to_datetime(df["date"])

    # 숫자형 변환
    numeric_columns = [
        "clicks",
        "impressions",
        "ctr",
        "position",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    # 날짜순 정렬
    df = df.sort_values("date").reset_index(drop=True)

    return df


def check_data_quality(df, date_column, name):
    """날짜 연속성, 중복, 결측치를 확인한다."""
    print(f"\n[{name} 품질검사]")
    print("-" * 50)

    print(f"데이터 수: {len(df)}")
    print(
        f"기간: {df[date_column].min().date()} "
        f"~ {df[date_column].max().date()}"
    )

    # 날짜 중복
    duplicate_count = df[date_column].duplicated().sum()
    print(f"중복 날짜: {duplicate_count}개")

    # 전체 날짜 범위와 비교
    full_date_range = pd.date_range(
        start=df[date_column].min(),
        end=df[date_column].max(),
        freq="D",
    )

    missing_dates = full_date_range.difference(df[date_column])

    print(f"누락 날짜: {len(missing_dates)}개")

    if len(missing_dates) > 0:
        print("누락된 날짜:")
        for date in missing_dates:
            print(f"  - {date.date()}")

    # 결측치 확인
    missing_values = df.isna().sum()
    missing_values = missing_values[missing_values > 0]

    if missing_values.empty:
        print("결측값: 없음")
    else:
        print("결측값:")
        print(missing_values)


def merge_data(daily_stats, gsc_daily):
    """daily_stats와 gsc_daily를 날짜 기준으로 병합한다."""
    daily = daily_stats.rename(columns={"stat_date": "date"})

    merged = pd.merge(
        gsc_daily,
        daily,
        on="date",
        how="inner",
        suffixes=("_gsc", "_stats"),
    )

    merged = merged.sort_values("date").reset_index(drop=True)

    return merged


def main():
    # Google Sheets 데이터 불러오기
    daily_stats_raw = load_sheet("daily_stats")
    gsc_daily_raw = load_sheet("gsc_daily")

    # 전처리
    daily_stats = preprocess_daily_stats(daily_stats_raw)
    gsc_daily = preprocess_gsc_daily(gsc_daily_raw)

    # 품질 검사
    check_data_quality(
        daily_stats,
        "stat_date",
        "daily_stats",
    )

    check_data_quality(
        gsc_daily,
        "date",
        "gsc_daily",
    )

    # 병합
    merged = merge_data(daily_stats, gsc_daily)

    print("\n[병합 데이터]")
    print("-" * 50)
    print(f"데이터 수: {len(merged)}")
    print(
        f"공통 기간: {merged['date'].min().date()} "
        f"~ {merged['date'].max().date()}"
    )
    print(f"컬럼: {list(merged.columns)}")

    print("\n처음 5행")
    print(merged.head())

    print("\n마지막 5행")
    print(merged.tail())


if __name__ == "__main__":
    main()