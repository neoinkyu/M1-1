from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from urllib.parse import unquote, urlsplit, urlunsplit

from statsmodels.tsa.seasonal import seasonal_decompose

from statsmodels.tsa.holtwinters import ExponentialSmoothing

from data_loader import load_sheet
from preprocess import (
    merge_data,
    preprocess_daily_stats,
    preprocess_gsc_daily,
)

from config import ANALYSIS_START_DATE, ANALYSIS_END_DATE


BASE_DIR = Path(__file__).resolve().parents[1]
IMAGES_DIR = BASE_DIR / "images"
IMAGES_DIR.mkdir(exist_ok=True)


def load_analysis_data():
    """Google Sheets 데이터를 불러와 분석 기간 기준으로 병합한다."""
    daily_stats_raw = load_sheet("daily_stats")
    gsc_daily_raw = load_sheet("gsc_daily")

    daily_stats = preprocess_daily_stats(daily_stats_raw)
    gsc_daily = preprocess_gsc_daily(gsc_daily_raw)

    merged = merge_data(daily_stats, gsc_daily)

    start_date = pd.to_datetime(ANALYSIS_START_DATE)
    end_date = pd.to_datetime(ANALYSIS_END_DATE)

    merged = merged[
        (merged["date"] >= start_date)
        & (merged["date"] <= end_date)
    ].copy()

    merged = merged.sort_values("date").reset_index(drop=True)

    return merged


def add_rolling_average(df):
    """주요 지표의 7일 이동평균을 계산한다."""
    df = df.copy()

    columns = [
        "clicks",
        "impressions",
        "users",
        "pv",
        "adsense_estimated",
    ]

    for column in columns:
        df[f"{column}_ma7"] = df[column].rolling(
            window=7,
            min_periods=7,
        ).mean()

    return df


def print_period_comparison(df):
    """초기 7일과 최근 7일 평균을 비교한다."""
    metrics = [
        "clicks",
        "impressions",
        "ctr",
        "position",
        "users",
        "pv",
        "adsense_estimated",
        "posts",
    ]

    print("\n[초기 7일 vs 최근 7일]")
    print("-" * 60)

    for metric in metrics:
        first = df[metric].iloc[:7].mean()
        last = df[metric].iloc[-7:].mean()

        if first != 0:
            change = (last - first) / first * 100
            print(
                f"{metric:20s} "
                f"{first:10.3f} → {last:10.3f} "
                f"({change:+8.1f}%)"
            )
        else:
            print(
                f"{metric:20s} "
                f"{first:10.3f} → {last:10.3f}"
            )


def print_correlations(df):
    """주요 지표 사이의 단순 상관계수를 확인한다."""
    pairs = [
        ("clicks", "users"),
        ("clicks", "pv"),
        ("users", "pv"),
        ("pv", "adsense_estimated"),
        ("users", "adsense_estimated"),
        ("posts", "clicks"),
        ("posts", "users"),
    ]

    print("\n[주요 지표 상관계수]")
    print("-" * 60)

    for x, y in pairs:
        corr = df[x].corr(df[y])
        print(f"{x:15s} ↔ {y:20s}: {corr:.3f}")


def plot_clicks(df):
    plt.figure(figsize=(12, 6))

    plt.plot(
        df["date"],
        df["clicks"],
        alpha=0.35,
        label="Daily clicks",
    )

    plt.plot(
        df["date"],
        df["clicks_ma7"],
        linewidth=2,
        label="7-day moving average",
    )

    plt.title("Google Search Click Trend")
    plt.xlabel("Date")
    plt.ylabel("Clicks")
    plt.legend()
    plt.grid(alpha=0.2)
    plt.tight_layout()

    plt.savefig(
        IMAGES_DIR / "01_search_clicks_trend.png",
        dpi=150,
    )

    plt.close()


def plot_impressions(df):
    plt.figure(figsize=(12, 6))

    plt.plot(
        df["date"],
        df["impressions"],
        alpha=0.35,
        label="Daily impressions",
    )

    plt.plot(
        df["date"],
        df["impressions_ma7"],
        linewidth=2,
        label="7-day moving average",
    )

    plt.title("Google Search Impression Trend")
    plt.xlabel("Date")
    plt.ylabel("Impressions")
    plt.legend()
    plt.grid(alpha=0.2)
    plt.tight_layout()

    plt.savefig(
        IMAGES_DIR / "02_search_impressions_trend.png",
        dpi=150,
    )

    plt.close()


def plot_users_and_pv(df):
    plt.figure(figsize=(12, 6))

    plt.plot(
        df["date"],
        df["users_ma7"],
        linewidth=2,
        label="Users (7-day MA)",
    )

    plt.plot(
        df["date"],
        df["pv_ma7"],
        linewidth=2,
        label="Pageviews (7-day MA)",
    )

    plt.title("Website Traffic Trend")
    plt.xlabel("Date")
    plt.ylabel("Count")
    plt.legend()
    plt.grid(alpha=0.2)
    plt.tight_layout()

    plt.savefig(
        IMAGES_DIR / "03_website_traffic_trend.png",
        dpi=150,
    )

    plt.close()


def plot_adsense(df):
    plt.figure(figsize=(12, 6))

    plt.plot(
        df["date"],
        df["adsense_estimated"],
        alpha=0.35,
        label="Daily revenue",
    )

    plt.plot(
        df["date"],
        df["adsense_estimated_ma7"],
        linewidth=2,
        label="7-day moving average",
    )

    plt.title("AdSense Estimated Revenue Trend")
    plt.xlabel("Date")
    plt.ylabel("Estimated Revenue")
    plt.legend()
    plt.grid(alpha=0.2)
    plt.tight_layout()

    plt.savefig(
        IMAGES_DIR / "04_adsense_revenue_trend.png",
        dpi=150,
    )

    plt.close()

def add_time_features(df):
    """요일과 28일 분석 구간을 추가한다."""
    df = df.copy()

    weekday_order = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    df["weekday"] = pd.Categorical(
        df["date"].dt.day_name(),
        categories=weekday_order,
        ordered=True,
    )

    # 112일을 동일한 28일 구간 4개로 구분
    df["period_28d"] = (df.index // 28) + 1

    return df


def print_weekday_summary(df):
    """요일별 평균 성과를 확인한다."""
    summary = (
        df.groupby("weekday", observed=True)
        .agg(
            days=("date", "count"),
            clicks=("clicks", "mean"),
            impressions=("impressions", "mean"),
            ctr=("ctr", "mean"),
            users=("users", "mean"),
            pv=("pv", "mean"),
            revenue=("adsense_estimated", "mean"),
        )
    )

    numeric_columns = summary.select_dtypes(include="number").columns
    summary[numeric_columns] = summary[numeric_columns].round(3)

    print("\n[요일별 평균]")
    print("-" * 100)
    print(summary.to_string())


def print_28day_summary(df):
    """완전한 28일 단위로 주요 지표의 변화를 비교한다."""
    df = df.copy()

    complete_days = (len(df) // 28) * 28
    df = df.iloc[:complete_days].copy()

    df["period_28d"] = (df.index // 28) + 1

    summary = (
        df.groupby("period_28d")
        .agg(
            start_date=("date", "min"),
            end_date=("date", "max"),
            clicks=("clicks", "mean"),
            impressions=("impressions", "mean"),
            ctr=("ctr", "mean"),
            position=("position", "mean"),
            users=("users", "mean"),
            pv=("pv", "mean"),
            revenue=("adsense_estimated", "mean"),
            posts=("posts", "mean"),
        )
    )

    numeric_columns = summary.select_dtypes(include="number").columns
    summary[numeric_columns] = summary[numeric_columns].round(3)

    print("\n[28일 구간별 평균]")
    print("-" * 100)
    print(summary.to_string())

def plot_ctr(df):
    df = df.copy()

    df["ctr_ma7"] = (
        df["ctr"]
        .rolling(window=7, min_periods=7)
        .mean()
    )

    plt.figure(figsize=(12, 6))

    plt.plot(
        df["date"],
        df["ctr"] * 100,
        alpha=0.3,
        label="Daily CTR",
    )

    plt.plot(
        df["date"],
        df["ctr_ma7"] * 100,
        linewidth=2,
        label="7-day moving average",
    )

    plt.title("Google Search CTR Trend")
    plt.xlabel("Date")
    plt.ylabel("CTR (%)")
    plt.legend()
    plt.grid(alpha=0.2)
    plt.tight_layout()

    plt.savefig(
        IMAGES_DIR / "05_search_ctr_trend.png",
        dpi=150,
    )

    plt.close()


def plot_position(df):
    df = df.copy()

    df["position_ma7"] = (
        df["position"]
        .rolling(window=7, min_periods=7)
        .mean()
    )

    plt.figure(figsize=(12, 6))

    plt.plot(
        df["date"],
        df["position"],
        alpha=0.3,
        label="Daily average position",
    )

    plt.plot(
        df["date"],
        df["position_ma7"],
        linewidth=2,
        label="7-day moving average",
    )

    # 검색순위는 숫자가 작을수록 좋으므로 Y축 반전
    plt.gca().invert_yaxis()

    plt.title("Google Search Average Position Trend")
    plt.xlabel("Date")
    plt.ylabel("Average Position (lower is better)")
    plt.legend()
    plt.grid(alpha=0.2)
    plt.tight_layout()

    plt.savefig(
        IMAGES_DIR / "06_search_position_trend.png",
        dpi=150,
    )

    plt.close()


def plot_weekday_clicks(df):
    weekday = (
        df.groupby("weekday", observed=True)["clicks"]
        .mean()
    )

    plt.figure(figsize=(10, 6))

    plt.bar(
        weekday.index,
        weekday.values,
    )

    plt.title("Average Google Search Clicks by Weekday")
    plt.xlabel("Weekday")
    plt.ylabel("Average Clicks")
    plt.xticks(rotation=30)
    plt.grid(axis="y", alpha=0.2)
    plt.tight_layout()

    plt.savefig(
        IMAGES_DIR / "07_weekday_clicks.png",
        dpi=150,
    )

    plt.close()


def plot_weekday_impressions(df):
    weekday = (
        df.groupby("weekday", observed=True)["impressions"]
        .mean()
    )

    plt.figure(figsize=(10, 6))

    plt.bar(
        weekday.index,
        weekday.values,
    )

    plt.title("Average Google Search Impressions by Weekday")
    plt.xlabel("Weekday")
    plt.ylabel("Average Impressions")
    plt.xticks(rotation=30)
    plt.grid(axis="y", alpha=0.2)
    plt.tight_layout()

    plt.savefig(
        IMAGES_DIR / "08_weekday_impressions.png",
        dpi=150,
    )

    plt.close()


def preprocess_gsc_dimension(df, dimension):
    """페이지·검색어 단위 GSC 데이터를 분석 가능한 형태로 정제한다."""
    df = df.copy()

    df["date"] = pd.to_datetime(df["date"])

    numeric_columns = [
        "clicks",
        "impressions",
        "ctr",
        "position",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    df = df.sort_values("date").reset_index(drop=True)

    if dimension == "page":
        df["page"] = df["page"].apply(normalize_page_url)

    return df


def get_comparison_periods(df):
    """첫 번째와 마지막 완전한 28일 구간의 날짜 범위를 반환한다."""
    complete_days = (len(df) // 28) * 28
    complete_df = df.iloc[:complete_days].copy()

    complete_df["period_28d"] = (
        range(len(complete_df))
    )

    complete_df["period_28d"] = (
        complete_df["period_28d"] // 28
    ) + 1

    first_period = complete_df[
        complete_df["period_28d"] == 1
    ]

    last_period_number = complete_df["period_28d"].max()

    last_period = complete_df[
        complete_df["period_28d"] == last_period_number
    ]

    return (
        first_period["date"].min(),
        first_period["date"].max(),
        last_period["date"].min(),
        last_period["date"].max(),
    )


def compare_gsc_dimension(
    df,
    dimension,
    first_start,
    first_end,
    last_start,
    last_end,
    top_n=15,
):
    """첫 28일과 마지막 28일의 페이지·검색어 성과 변화를 비교한다."""

    first = df[
        (df["date"] >= first_start)
        & (df["date"] <= first_end)
    ]

    last = df[
        (df["date"] >= last_start)
        & (df["date"] <= last_end)
    ]

    first_summary = (
        first.groupby(dimension)
        .agg(
            clicks_first=("clicks", "sum"),
            impressions_first=("impressions", "sum"),
        )
        .reset_index()
    )

    last_summary = (
        last.groupby(dimension)
        .agg(
            clicks_last=("clicks", "sum"),
            impressions_last=("impressions", "sum"),
        )
        .reset_index()
    )

    comparison = pd.merge(
        first_summary,
        last_summary,
        on=dimension,
        how="outer",
    ).fillna(0)

    comparison["impressions_change"] = (
        comparison["impressions_last"]
        - comparison["impressions_first"]
    )

    comparison["clicks_change"] = (
        comparison["clicks_last"]
        - comparison["clicks_first"]
    )

    decreases = comparison.sort_values(
        "impressions_change"
    ).head(top_n)

    increases = comparison.sort_values(
        "impressions_change",
        ascending=False,
    ).head(top_n)

    print(
        f"\n[{dimension} - 노출 감소 상위 {top_n}개]"
    )
    print("-" * 120)

    print(
        decreases[
            [
                dimension,
                "impressions_first",
                "impressions_last",
                "impressions_change",
                "clicks_first",
                "clicks_last",
                "clicks_change",
            ]
        ].to_string(index=False)
    )

    print(
        f"\n[{dimension} - 노출 증가 상위 {top_n}개]"
    )
    print("-" * 120)

    print(
        increases[
            [
                dimension,
                "impressions_first",
                "impressions_last",
                "impressions_change",
                "clicks_first",
                "clicks_last",
                "clicks_change",
            ]
        ].to_string(index=False)
    )

    return comparison


def normalize_page_url(url):
    """URL fragment(#...)를 제거하고 페이지 단위 URL로 정규화한다."""
    url = unquote(url)

    parts = urlsplit(url)

    normalized = urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            parts.path,
            parts.query,
            "",
        )
    )

    return normalized


def plot_28day_index_comparison(df):
    """28일 구간별 주요 지표 변화를 첫 구간=100 기준으로 비교한다."""
    df = df.copy()

    df["period_28d"] = (df.index // 28) + 1

    metrics = [
        "clicks",
        "impressions",
        "users",
        "pv",
        "adsense_estimated",
    ]

    summary = (
        df.groupby("period_28d")[metrics]
        .mean()
    )

    index_summary = (
        summary
        .div(summary.iloc[0])
        * 100
    )

    plt.figure(figsize=(12, 7))

    for metric in metrics:
        plt.plot(
            index_summary.index,
            index_summary[metric],
            marker="o",
            linewidth=2,
            label=metric,
        )

    plt.axhline(
        100,
        linestyle="--",
        linewidth=1,
    )

    plt.title("28-Day Performance Index Comparison")
    plt.xlabel("28-Day Period")
    plt.ylabel("Index (Period 1 = 100)")
    plt.xticks(
        [1, 2, 3, 4],
        ["Period 1", "Period 2", "Period 3", "Period 4"],
    )
    plt.legend()
    plt.grid(alpha=0.2)
    plt.tight_layout()

    plt.savefig(
        IMAGES_DIR / "09_28day_index_comparison.png",
        dpi=150,
    )

    plt.close()


def plot_top_page_impression_decreases(
    comparison,
    top_n=10,
):
    """검색 노출 감소가 가장 큰 페이지를 시각화한다."""
    decreases = (
        comparison[
            comparison["impressions_change"] < 0
        ]
        .sort_values("impressions_change")
        .head(top_n)
        .copy()
    )

    decreases["label"] = (
        decreases["page"]
        .str.replace(
            "https://www.auctionsuit.com/",
            "",
            regex=False,
        )
        .str.strip("/")
    )

    decreases["decrease_amount"] = (
        -decreases["impressions_change"]
    )

    plt.figure(figsize=(12, 7))

    plt.barh(
        decreases["label"],
        decreases["decrease_amount"],
    )

    plt.gca().invert_yaxis()

    plt.title(
        "Top Pages Contributing to Search Impression Decline"
    )
    plt.xlabel("Decrease in Impressions")
    plt.ylabel("Page")
    plt.grid(axis="x", alpha=0.2)
    plt.tight_layout()

    plt.savefig(
        IMAGES_DIR / "10_top_page_impression_decreases.png",
        dpi=150,
    )

    plt.close()

def plot_pv_revenue_relationship(df):
    """페이지뷰와 AdSense 예상수익의 관계를 시각화한다."""
    correlation = df[
        "pv"
    ].corr(
        df["adsense_estimated"]
    )

    plt.figure(figsize=(9, 7))

    plt.scatter(
        df["pv"],
        df["adsense_estimated"],
        alpha=0.6,
    )

    plt.title(
        "Pageviews vs AdSense Estimated Revenue"
    )
    plt.xlabel("Pageviews")
    plt.ylabel("AdSense Estimated Revenue")
    plt.grid(alpha=0.2)

    plt.text(
        0.03,
        0.95,
        f"Correlation: {correlation:.3f}",
        transform=plt.gca().transAxes,
        verticalalignment="top",
    )

    plt.tight_layout()

    plt.savefig(
        IMAGES_DIR / "11_pv_adsense_relationship.png",
        dpi=150,
    )

    plt.close()

def plot_clicks_decomposition(df):
    """검색 클릭수를 추세·계절성·잔차로 분해한다."""
    series = (
        df.set_index("date")["clicks"]
        .asfreq("D")
    )

    decomposition = seasonal_decompose(
        series,
        model="additive",
        period=7,
    )

    fig = decomposition.plot()
    fig.set_size_inches(12, 9)

    fig.suptitle(
        "Google Search Clicks Time Series Decomposition",
        fontsize=14,
    )

    fig.tight_layout()

    fig.savefig(
        IMAGES_DIR / "12_clicks_decomposition.png",
        dpi=150,
    )

    plt.close(fig)


def forecast_clicks(df, test_days=14, future_days=14):
    """Holt-Winters 방식으로 클릭수를 검증하고 향후 14일을 예측한다."""
    series = (
        df.set_index("date")["clicks"]
        .asfreq("D")
    )

    # -------------------------
    # 1. 백테스트
    # -------------------------
    train = series.iloc[:-test_days]
    test = series.iloc[-test_days:]

    model = ExponentialSmoothing(
        train,
        trend="add",
        seasonal="add",
        seasonal_periods=7,
    ).fit()

    test_forecast = model.forecast(test_days)

    mae = (
        abs(test - test_forecast)
        .mean()
    )

    print("\n[클릭수 예측 백테스트]")
    print("-" * 60)
    print(f"테스트 기간: {test.index.min().date()} ~ {test.index.max().date()}")
    print(f"MAE: {mae:.3f}")

    # -------------------------
    # 2. 전체 데이터로 재학습
    # -------------------------
    final_model = ExponentialSmoothing(
        series,
        trend="add",
        seasonal="add",
        seasonal_periods=7,
    ).fit()

    future_forecast = final_model.forecast(
        future_days
    )

    # -------------------------
    # 3. 시각화
    # -------------------------
    plt.figure(figsize=(12, 7))

    plt.plot(
        series.index,
        series.values,
        label="Actual clicks",
    )

    plt.plot(
        future_forecast.index,
        future_forecast.values,
        marker="o",
        label="14-day forecast",
    )

    plt.axvline(
        series.index.max(),
        linestyle="--",
        linewidth=1,
    )

    plt.title(
        "Google Search Clicks - 14-Day Forecast"
    )
    plt.xlabel("Date")
    plt.ylabel("Clicks")
    plt.legend()
    plt.grid(alpha=0.2)
    plt.tight_layout()

    plt.savefig(
        IMAGES_DIR / "13_clicks_forecast.png",
        dpi=150,
    )

    plt.close()

    return mae, future_forecast


def main():
    df = load_analysis_data()
    df = add_rolling_average(df)
    df = add_time_features(df)

    print("[1차·2차·3차 탐색분석]")
    print("-" * 60)

    print(
        f"분석 기간: "
        f"{df['date'].min().date()} ~ "
        f"{df['date'].max().date()}"
    )

    print(f"데이터 포인트: {len(df)}개")

    # 1차 분석
    print_period_comparison(df)
    print_correlations(df)

    # 2차 분석
    print_weekday_summary(df)
    print_28day_summary(df)

    # 기본 시각화
    plot_clicks(df)
    plot_impressions(df)
    plot_users_and_pv(df)
    plot_adsense(df)
    plot_ctr(df)
    plot_position(df)
    plot_weekday_clicks(df)
    plot_weekday_impressions(df)

    # 28일 구간 종합 비교
    plot_28day_index_comparison(df)

    # 3차 분석: 페이지·검색어 변화
    (
        first_start,
        first_end,
        last_start,
        last_end,
    ) = get_comparison_periods(df)

    print("\n[페이지·검색어 비교 기간]")
    print(
        f"초기: {first_start.date()} ~ {first_end.date()}"
    )
    print(
        f"최근: {last_start.date()} ~ {last_end.date()}"
    )

    gsc_pages_raw = load_sheet("gsc_pages")
    gsc_queries_raw = load_sheet("gsc_queries")

    gsc_pages = preprocess_gsc_dimension(
        gsc_pages_raw,
        "page",
    )

    gsc_queries = preprocess_gsc_dimension(
        gsc_queries_raw,
        "query",
    )

    page_comparison = compare_gsc_dimension(
        gsc_pages,
        "page",
        first_start,
        first_end,
        last_start,
        last_end,
    )

    compare_gsc_dimension(
        gsc_queries,
        "query",
        first_start,
        first_end,
        last_start,
        last_end,
    )

    # 최종 REPORT용 추가 시각화
    plot_top_page_impression_decreases(
        page_comparison
    )

    plot_pv_revenue_relationship(df)

    # 보너스: 시계열 분해
    plot_clicks_decomposition(df)

    # 보너스: 간단 예측
    forecast_clicks(df)

    print("\n시각화 저장 완료")
    print(f"저장 위치: {IMAGES_DIR}")


if __name__ == "__main__":
    main()