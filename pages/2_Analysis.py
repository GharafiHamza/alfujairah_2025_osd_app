import json
import os

import altair as alt
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(page_title="Fujairah Analysis 2025", layout="wide")

st.markdown(
    """
    <style>
        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stAppViewContainer"] > .main,
        [data-testid="stHeader"] {
            background: #0b1220 !important;
            color: #e5eefb !important;
        }
        header[data-testid="stHeader"],
        div[data-testid="stToolbar"],
        div[data-testid="stDecoration"] {
            display: none;
        }
        [data-testid="stSidebar"],
        [data-testid="stSidebarNav"],
        [data-testid="collapsedControl"] {
            display: none;
        }
        .block-container {
            padding-top: 2rem;
        }
        div[data-testid="stButton"] > button {
            width: 100%;
            border-radius: 14px;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.08);
            color: #e5eefb;
            font-weight: 700;
            padding: 0.85rem 0;
        }
        div[data-testid="stButton"] > button:hover {
            background: rgba(255, 255, 255, 0.08);
            border-color: rgba(255, 255, 255, 0.16);
        }
    </style>
    """,
    unsafe_allow_html=True,
)

nav_left, nav_right = st.columns(2)
with nav_left:
    if st.button("Map", use_container_width=True):
        st.switch_page("app.py")
with nav_right:
    if st.button("Analysis", use_container_width=True):
        st.switch_page("pages/2_Analysis.py")

st.title("Fujairah Slick Analysis 2025")

SLICKS_FILE = "slicks_2025_alfujairah.geojson"

if not os.path.exists(SLICKS_FILE):
    st.error("Slick data file not found. Please run the extraction step first.")
    st.stop()

with open(SLICKS_FILE, "r") as f:
    slicks_geojson = json.load(f)


def build_yearly_analysis(slicks_data):
    rows = []
    for feature in slicks_data.get("features", []):
        props = feature.get("properties", {})
        detected_at = pd.to_datetime(props.get("detected_at"), errors="coerce")
        area = pd.to_numeric(props.get("area"), errors="coerce")
        min_conf = pd.to_numeric(props.get("min_confidence"), errors="coerce")
        max_conf = pd.to_numeric(props.get("max_confidence"), errors="coerce")
        rows.append(
            {
                "slick_id": props.get("id"),
                "scene_id": props.get("scene_id"),
                "detected_at": detected_at,
                "month": detected_at.month if not pd.isna(detected_at) else None,
                "area": area,
                "min_confidence": min_conf,
                "max_confidence": max_conf,
            }
        )

    df = pd.DataFrame(rows)
    df = df.dropna(subset=["month"]).copy()
    if df.empty:
        return df, pd.DataFrame(), pd.DataFrame(), pd.Series(dtype=float)

    df["month"] = df["month"].astype(int)
    df["confidence_mid"] = df[["min_confidence", "max_confidence"]].mean(axis=1)

    monthly = (
        df.groupby("month")
        .agg(
            slick_count=("slick_id", "count"),
            detected_area=("area", "sum"),
            average_area=("area", "mean"),
            median_area=("area", "median"),
            average_confidence=("confidence_mid", "mean"),
        )
        .reindex(range(1, 13), fill_value=0)
    )
    monthly.index.name = "month"
    monthly["cumulative_slick_count"] = monthly["slick_count"].cumsum()
    monthly["cumulative_detected_area"] = monthly["detected_area"].cumsum()

    top_slicks = (
        df.sort_values("area", ascending=False)
        .head(10)
        .assign(month_name=lambda x: x["month"].map(lambda m: pd.Timestamp(year=2025, month=int(m), day=1).strftime("%b")))
    )

    confidence_bins = pd.cut(
        df["confidence_mid"],
        bins=[0, 70, 80, 90, 100],
        labels=["<70", "70-80", "80-90", "90-100"],
        include_lowest=True,
    ).value_counts().sort_index()

    return df, monthly, top_slicks, confidence_bins


slick_df, monthly_stats, top_slicks, confidence_bins = build_yearly_analysis(slicks_geojson)

st.caption("Sentinel-1 SAR detected slicks across 2025, summarized by count, detected area, and confidence.")

if slick_df.empty:
    st.warning("No slick records were available for analysis.")
else:
    total_slicks = int(slick_df.shape[0])
    total_area = float(slick_df["area"].fillna(0).sum())
    avg_area = float(slick_df["area"].fillna(0).mean())
    peak_month = int(monthly_stats["slick_count"].idxmax())
    peak_month_count = int(monthly_stats.loc[peak_month, "slick_count"])
    peak_area_month = int(monthly_stats["detected_area"].idxmax())
    peak_area_value = float(monthly_stats.loc[peak_area_month, "detected_area"])

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total slicks", f"{total_slicks}")
    k2.metric("Total detected area", f"{total_area:,.2f}")
    k3.metric("Average slick area", f"{avg_area:,.2f}")
    k4.metric("Peak month", f"{pd.Timestamp(year=2025, month=peak_month, day=1).strftime('%B')} ({peak_month_count})")

    tab1, tab2, tab3 = st.tabs(["Trends", "Tables", "Distribution"])

    with tab1:
        trend_df = monthly_stats.reset_index().copy().sort_values("month")
        trend_df["month_name"] = trend_df["month"].apply(lambda m: pd.Timestamp(year=2025, month=int(m), day=1).strftime("%b"))
        trend_df = trend_df.set_index("month_name")
        month_order = trend_df.index.tolist()

        st.subheader("Monthly slick counts")
        count_chart = (
            alt.Chart(trend_df.reset_index())
            .mark_bar()
            .encode(
                x=alt.X("month_name:N", sort=month_order, title="Month"),
                y=alt.Y("slick_count:Q", title="Slicks"),
                tooltip=["month_name", "slick_count"],
            )
        )
        st.altair_chart(count_chart, use_container_width=True)

        st.subheader("Monthly detected area")
        area_chart = (
            alt.Chart(trend_df.reset_index())
            .mark_bar(color="#38bdf8")
            .encode(
                x=alt.X("month_name:N", sort=month_order, title="Month"),
                y=alt.Y("detected_area:Q", title="Detected Area"),
                tooltip=["month_name", "detected_area"],
            )
        )
        st.altair_chart(area_chart, use_container_width=True)

        st.subheader("Cumulative evolution")
        cum_df = trend_df.reset_index()
        cumulative_slicks = (
            alt.Chart(cum_df)
            .mark_line(point=True)
            .encode(
                x=alt.X("month_name:N", sort=month_order, title="Month"),
                y=alt.Y("cumulative_slick_count:Q", title="Cumulative Slicks"),
                tooltip=["month_name", "cumulative_slick_count"],
            )
        )
        cumulative_area = (
            alt.Chart(cum_df)
            .mark_line(point=True, color="#f97316")
            .encode(
                x=alt.X("month_name:N", sort=month_order, title="Month"),
                y=alt.Y("cumulative_detected_area:Q", title="Cumulative Area"),
                tooltip=["month_name", "cumulative_detected_area"],
            )
        )
        c1, c2 = st.columns(2)
        with c1:
            st.altair_chart(cumulative_slicks, use_container_width=True)
        with c2:
            st.altair_chart(cumulative_area, use_container_width=True)

    with tab2:
        st.subheader("Monthly summary")
        monthly_table = monthly_stats.reset_index().copy().sort_values("month")
        monthly_table["month"] = monthly_table["month"].apply(lambda m: pd.Timestamp(year=2025, month=int(m), day=1).strftime("%B"))
        monthly_table = monthly_table.rename(
            columns={
                "month": "Month",
                "slick_count": "Slicks",
                "detected_area": "Detected Area",
                "average_area": "Avg Area",
                "median_area": "Median Area",
                "average_confidence": "Avg Confidence",
                "cumulative_slick_count": "Cumulative Slicks",
                "cumulative_detected_area": "Cumulative Area",
            }
        )
        st.dataframe(monthly_table, use_container_width=True, hide_index=True)

        st.subheader("Top 10 largest slicks")
        if not top_slicks.empty:
            top_table = top_slicks[
                ["slick_id", "scene_id", "month_name", "area", "min_confidence", "max_confidence", "detected_at"]
            ].rename(
                columns={
                    "slick_id": "Slick ID",
                    "scene_id": "Scene ID",
                    "month_name": "Month",
                    "area": "Area",
                    "min_confidence": "Min Confidence",
                    "max_confidence": "Max Confidence",
                    "detected_at": "Detected At",
                }
            )
            st.dataframe(top_table, use_container_width=True, hide_index=True)

    with tab3:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Confidence distribution")
            st.bar_chart(confidence_bins.to_frame(name="count"))
        with c2:
            st.subheader("Highest area month")
            st.metric(
                "Peak detected area",
                f"{peak_area_value:,.2f}",
                pd.Timestamp(year=2025, month=peak_area_month, day=1).strftime("%B"),
            )
            st.write(
                "This analysis is based on Sentinel-1 SAR detections, so the reported area reflects the detected slick footprint rather than a direct oil volume estimate."
            )
