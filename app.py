from pathlib import Path
import sys

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


# --------------------------------------------------
# 프로젝트 경로 설정
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from data_loader import load_sheet
from preprocess import (
    merge_data,
    preprocess_daily_stats,
    preprocess_gsc_daily,
)


# --------------------------------------------------
# Streamlit 기본 설정
# --------------------------------------------------

st.set_page_config(
    page_title="AuctionSuit Dashboard",
    page_icon="📊",
    layout="wide",
)


# --------------------------------------------------
# 데이터 로딩
# --------------------------------------------------

@st.cache_data(ttl=300)
def load_dashboard_data():
    """
    Google Sheets에서 최신 데이터를 불러와
    대시보드용 데이터로 병합한다.

    캐시는 5분간 유지한다.
    """

    daily_stats_raw = load_sheet("daily_stats")
    gsc_daily_raw = load_sheet("gsc_daily")

    daily_stats = preprocess_daily_stats(
        daily_stats_raw
    )

    gsc_daily = preprocess_gsc_daily(
        gsc_daily_raw
    )

    merged = merge_data(
        daily_stats,
        gsc_daily,
    )

    merged = (
        merged
        .sort_values("date")
        .reset_index(drop=True)
    )

    return merged


# --------------------------------------------------
# 보조 함수
# --------------------------------------------------

def calculate_weighted_position(df):
    """
    기간 전체의 평균 검색순위를
    노출수 기준 가중평균으로 계산한다.
    """

    total_impressions = df["impressions"].sum()

    if total_impressions == 0:
        return 0

    weighted_position = (
        df["position"] * df["impressions"]
    ).sum() / total_impressions

    return weighted_position


def add_dashboard_features(df):
    """
    대시보드 표시용 파생변수를 만든다.
    """

    df = df.copy()

    df["clicks_ma7"] = (
        df["clicks"]
        .rolling(
            window=7,
            min_periods=1,
        )
        .mean()
    )

    df["impressions_ma7"] = (
        df["impressions"]
        .rolling(
            window=7,
            min_periods=1,
        )
        .mean()
    )

    df["users_ma7"] = (
        df["users"]
        .rolling(
            window=7,
            min_periods=1,
        )
        .mean()
    )

    df["pv_ma7"] = (
        df["pv"]
        .rolling(
            window=7,
            min_periods=1,
        )
        .mean()
    )

    df["revenue_ma7"] = (
        df["adsense_estimated"]
        .rolling(
            window=7,
            min_periods=1,
        )
        .mean()
    )

    weekday_names = {
        0: "월",
        1: "화",
        2: "수",
        3: "목",
        4: "금",
        5: "토",
        6: "일",
    }

    df["weekday"] = (
        df["date"]
        .dt.dayofweek
        .map(weekday_names)
    )

    return df


def plot_metric_trend(
    df,
    column,
    rolling_column,
    title,
    ylabel,
    show_ma,
):
    """
    일별 지표와 7일 이동평균을 시각화한다.
    """

    fig, ax = plt.subplots(
        figsize=(12, 5)
    )

    ax.plot(
        df["date"],
        df[column],
        alpha=0.35,
        label="일별",
    )

    if show_ma:
        ax.plot(
            df["date"],
            df[rolling_column],
            linewidth=2,
            label="7일 이동평균",
        )

    ax.set_title(title)
    ax.set_xlabel("날짜")
    ax.set_ylabel(ylabel)

    ax.legend()
    ax.grid(alpha=0.2)

    fig.tight_layout()

    return fig


# --------------------------------------------------
# 데이터 불러오기
# --------------------------------------------------

try:
    df = load_dashboard_data()

except Exception as error:
    st.error(
        "Google Sheets 데이터를 불러오지 못했습니다."
    )

    st.exception(error)
    st.stop()


if df.empty:
    st.warning(
        "표시할 데이터가 없습니다."
    )

    st.stop()


# --------------------------------------------------
# 제목
# --------------------------------------------------

st.title(
    "📊 AuctionSuit 운영 대시보드"
)

st.caption(
    "Google Search Console · GA4 · AdSense · WordPress 통계"
)


# --------------------------------------------------
# 사이드바
# --------------------------------------------------

st.sidebar.header(
    "조회 조건"
)

min_date = df["date"].min().date()
max_date = df["date"].max().date()

selected_dates = st.sidebar.date_input(
    "조회 기간",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)


if isinstance(
    selected_dates,
    (tuple, list),
) and len(selected_dates) == 2:

    start_date = pd.Timestamp(
        selected_dates[0]
    )

    end_date = pd.Timestamp(
        selected_dates[1]
    )

else:
    start_date = pd.Timestamp(min_date)
    end_date = pd.Timestamp(max_date)


show_ma = st.sidebar.checkbox(
    "7일 이동평균 표시",
    value=True,
)


if st.sidebar.button(
    "최신 데이터 다시 불러오기"
):

    st.cache_data.clear()
    st.rerun()


# --------------------------------------------------
# 기간 필터
# --------------------------------------------------

filtered = df[
    (df["date"] >= start_date)
    & (df["date"] <= end_date)
].copy()


if filtered.empty:
    st.warning(
        "선택한 기간에 데이터가 없습니다."
    )

    st.stop()


filtered = add_dashboard_features(
    filtered
)


# --------------------------------------------------
# 핵심 지표
# --------------------------------------------------

total_clicks = (
    filtered["clicks"].sum()
)

total_impressions = (
    filtered["impressions"].sum()
)

if total_impressions > 0:

    weighted_ctr = (
        total_clicks
        / total_impressions
        * 100
    )

else:
    weighted_ctr = 0


average_position = (
    calculate_weighted_position(
        filtered
    )
)

average_users = (
    filtered["users"].mean()
)

average_pv = (
    filtered["pv"].mean()
)

total_revenue = (
    filtered["adsense_estimated"].sum()
)


st.subheader(
    "핵심 지표"
)

metric_columns = st.columns(6)

metric_columns[0].metric(
    "검색 클릭",
    f"{total_clicks:,.0f}",
)

metric_columns[1].metric(
    "검색 노출",
    f"{total_impressions:,.0f}",
)

metric_columns[2].metric(
    "CTR",
    f"{weighted_ctr:.2f}%",
)

metric_columns[3].metric(
    "평균 검색순위",
    f"{average_position:.2f}",
)

metric_columns[4].metric(
    "일평균 사용자",
    f"{average_users:,.1f}",
)

metric_columns[5].metric(
    "일평균 PV",
    f"{average_pv:,.1f}",
)


st.metric(
    "기간 AdSense 예상수익",
    f"{total_revenue:,.2f}",
)


st.caption(
    f"조회기간: "
    f"{start_date.date()} ~ "
    f"{end_date.date()} "
    f"({len(filtered)}일)"
)


# --------------------------------------------------
# 탭
# --------------------------------------------------

tab_overview, tab_search, tab_traffic, tab_revenue = (
    st.tabs(
        [
            "📈 전체 현황",
            "🔍 검색 성과",
            "👥 사이트 이용",
            "💰 수익",
        ]
    )
)


# ==================================================
# 전체 현황
# ==================================================

with tab_overview:

    st.subheader(
        "주요 지표 추세"
    )

    overview_df = (
        filtered[
            [
                "date",
                "clicks",
                "users",
                "pv",
            ]
        ]
        .set_index("date")
    )

    st.line_chart(
        overview_df
    )

    st.subheader(
        "최근 데이터"
    )

    display_columns = [
        "date",
        "clicks",
        "impressions",
        "ctr",
        "position",
        "users",
        "pv",
        "adsense_estimated",
        "posts",
    ]

    recent_data = (
        filtered[
            display_columns
        ]
        .tail(14)
        .sort_values(
            "date",
            ascending=False,
        )
    )

    st.dataframe(
        recent_data,
        width="stretch",
        hide_index=True,
    )


# ==================================================
# 검색 성과
# ==================================================

with tab_search:

    st.subheader(
        "Google 검색 클릭"
    )

    fig = plot_metric_trend(
        filtered,
        "clicks",
        "clicks_ma7",
        "검색 클릭 추세",
        "클릭",
        show_ma,
    )

    st.pyplot(fig)
    plt.close(fig)


    st.subheader(
        "Google 검색 노출"
    )

    fig = plot_metric_trend(
        filtered,
        "impressions",
        "impressions_ma7",
        "검색 노출 추세",
        "노출",
        show_ma,
    )

    st.pyplot(fig)
    plt.close(fig)


    search_col1, search_col2 = (
        st.columns(2)
    )


    with search_col1:

        st.subheader(
            "CTR 추세"
        )

        ctr_df = (
            filtered[
                [
                    "date",
                    "ctr",
                ]
            ]
            .copy()
        )

        ctr_df["ctr"] = (
            ctr_df["ctr"] * 100
        )

        ctr_df = (
            ctr_df.set_index("date")
        )

        st.line_chart(
            ctr_df
        )


    with search_col2:

        st.subheader(
            "평균 검색순위"
        )

        position_df = (
            filtered[
                [
                    "date",
                    "position",
                ]
            ]
            .set_index("date")
        )

        st.line_chart(
            position_df
        )


    st.subheader(
        "요일별 검색 성과"
    )

    weekday_order = [
        "월",
        "화",
        "수",
        "목",
        "금",
        "토",
        "일",
    ]

    weekday_summary = (
        filtered
        .groupby(
            "weekday",
            observed=True,
        )
        .agg(
            clicks=("clicks", "mean"),
            impressions=(
                "impressions",
                "mean",
            ),
        )
        .reindex(weekday_order)
    )

    st.bar_chart(
        weekday_summary["clicks"]
    )

    st.caption(
        "주의: GSC의 일별 데이터는 Pacific Time 기준으로 집계되므로 "
        "한국 현지 요일과 직접 일치하지 않습니다."
    )


# ==================================================
# 사이트 이용
# ==================================================

with tab_traffic:

    st.subheader(
        "사용자 추세"
    )

    fig = plot_metric_trend(
        filtered,
        "users",
        "users_ma7",
        "사용자 추세",
        "Users",
        show_ma,
    )

    st.pyplot(fig)
    plt.close(fig)


    st.subheader(
        "페이지뷰 추세"
    )

    fig = plot_metric_trend(
        filtered,
        "pv",
        "pv_ma7",
        "페이지뷰 추세",
        "Pageviews",
        show_ma,
    )

    st.pyplot(fig)
    plt.close(fig)


    st.subheader(
        "Users와 Pageviews 관계"
    )

    traffic_relation = (
        filtered[
            [
                "date",
                "users",
                "pv",
            ]
        ]
        .set_index("date")
    )

    st.line_chart(
        traffic_relation
    )


# ==================================================
# 수익
# ==================================================

with tab_revenue:

    st.subheader(
        "AdSense 예상수익 추세"
    )

    fig = plot_metric_trend(
        filtered,
        "adsense_estimated",
        "revenue_ma7",
        "AdSense 예상수익 추세",
        "예상수익",
        show_ma,
    )

    st.pyplot(fig)
    plt.close(fig)


    st.subheader(
        "Pageviews와 AdSense 예상수익"
    )

    correlation = (
        filtered["pv"]
        .corr(
            filtered[
                "adsense_estimated"
            ]
        )
    )

    fig, ax = plt.subplots(
        figsize=(9, 6)
    )

    ax.scatter(
        filtered["pv"],
        filtered["adsense_estimated"],
        alpha=0.6,
    )

    ax.set_xlabel(
        "Pageviews"
    )

    ax.set_ylabel(
        "AdSense 예상수익"
    )

    ax.set_title(
        "Pageviews vs AdSense 예상수익"
    )

    ax.grid(alpha=0.2)

    ax.text(
        0.03,
        0.95,
        f"상관계수: {correlation:.3f}",
        transform=ax.transAxes,
        verticalalignment="top",
    )

    fig.tight_layout()

    st.pyplot(fig)
    plt.close(fig)


    st.info(
        "상관계수는 두 지표가 함께 움직이는 정도를 보여주며, "
        "인과관계를 의미하지는 않습니다."
    )


# --------------------------------------------------
# 하단 정보
# --------------------------------------------------

st.divider()

st.caption(
    "데이터 출처: AuctionSuit Google Sheets "
    "(Google Search Console, GA4, AdSense, WordPress)"
)

st.caption(
    "대시보드는 Google Sheets의 최신 데이터를 불러오며 "
    "최대 5분간 캐시됩니다."
)