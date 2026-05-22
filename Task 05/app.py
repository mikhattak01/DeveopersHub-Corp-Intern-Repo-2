import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Page config 
st.set_page_config(page_title="SuperStore Dashboard", layout="wide", page_icon="🛒")


# Load & clean data 
@st.cache_data
def load_data():
    df = pd.read_csv("SuperStore.csv", encoding="latin1")
    df.columns = df.columns.str.replace(".", "_", regex=False)  # dot → underscore
    df["Order_Date"] = pd.to_datetime(df["Order_Date"], dayfirst=True, errors="coerce")
    df["Ship_Date"]  = pd.to_datetime(df["Ship_Date"],  dayfirst=True, errors="coerce")
    df = df.dropna(subset=["Sales", "Profit"])
    return df

df = load_data()

# Sidebar filters 
st.sidebar.title("🔍 Filters")

regions = ["All"] + sorted(df["Region"].dropna().unique().tolist())
categories = ["All"] + sorted(df["Category"].dropna().unique().tolist())

sel_region   = st.sidebar.selectbox("Region", regions)
sel_category = st.sidebar.selectbox("Category", categories)

# Sub-category depends on category selection
if sel_category != "All":
    sub_options = ["All"] + sorted(df[df["Category"] == sel_category]["Sub_Category"].dropna().unique().tolist())
else:
    sub_options = ["All"] + sorted(df["Sub_Category"].dropna().unique().tolist())

sel_sub = st.sidebar.selectbox("Sub-Category", sub_options)

# Year range
years = sorted(df["Order_Date"].dt.year.dropna().unique().astype(int).tolist())
year_range = st.sidebar.select_slider("Year Range", options=years, value=(min(years), max(years)))

# Apply filters 
fdf = df.copy()
if sel_region   != "All": fdf = fdf[fdf["Region"]       == sel_region]
if sel_category != "All": fdf = fdf[fdf["Category"]     == sel_category]
if sel_sub      != "All": fdf = fdf[fdf["Sub_Category"] == sel_sub]
fdf = fdf[fdf["Order_Date"].dt.year.between(year_range[0], year_range[1])]

# Header 
st.title("🛒 Global SuperStore Dashboard")
st.markdown("Interactive analysis of **sales, profit & segment performance**.")
st.markdown("---")

# KPI Cards 
total_sales   = fdf["Sales"].sum()
total_profit  = fdf["Profit"].sum()
profit_margin = (total_profit / total_sales * 100) if total_sales else 0
total_orders  = fdf["Order_ID"].nunique()
total_qty     = fdf["Quantity"].sum()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("💰 Total Sales",    f"${total_sales:,.0f}")
k2.metric("📈 Total Profit",   f"${total_profit:,.0f}")
k3.metric("📊 Profit Margin",  f"{profit_margin:.1f}%")
k4.metric("📦 Total Orders",   f"{total_orders:,}")
k5.metric("🔢 Units Sold",     f"{total_qty:,}")

st.markdown("---")

# Row 1: Sales trend + Category breakdown 
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("📅 Monthly Sales & Profit Trend")
    monthly = (fdf.groupby(fdf["Order_Date"].dt.to_period("M"))
                  .agg(Sales=("Sales","sum"), Profit=("Profit","sum"))
                  .reset_index())
    monthly["Order_Date"] = monthly["Order_Date"].astype(str)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=monthly["Order_Date"], y=monthly["Sales"],
                             name="Sales", line=dict(color="#4F8EF7", width=2)))
    fig.add_trace(go.Scatter(x=monthly["Order_Date"], y=monthly["Profit"],
                             name="Profit", line=dict(color="#2ECC71", width=2)))
    fig.update_layout(margin=dict(t=10,b=10), height=300, legend=dict(orientation="h"))
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("🗂 Sales by Category")
    cat_df = fdf.groupby("Category")["Sales"].sum().reset_index()
    fig2 = px.pie(cat_df, names="Category", values="Sales",
                  color_discrete_sequence=["#4F8EF7","#F7934F","#2ECC71"],
                  hole=0.4)
    fig2.update_layout(margin=dict(t=10,b=10), height=300,
                       legend=dict(orientation="h", y=-0.1))
    st.plotly_chart(fig2, use_container_width=True)

# Row 2: Top 5 Customers + Segment + Region
c3, c4, c5 = st.columns(3)

with c3:
    st.subheader("🏆 Top 5 Customers by Sales")
    top5 = (fdf.groupby("Customer_Name")["Sales"].sum()
               .nlargest(5).reset_index())
    fig3 = px.bar(top5, x="Sales", y="Customer_Name", orientation="h",
                  color="Sales", color_continuous_scale="Blues",
                  labels={"Customer_Name": ""})
    fig3.update_layout(margin=dict(t=10,b=10), height=280,
                       coloraxis_showscale=False, yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig3, use_container_width=True)

with c4:
    st.subheader("👥 Profit by Segment")
    seg = fdf.groupby("Segment")["Profit"].sum().reset_index()
    fig4 = px.bar(seg, x="Segment", y="Profit",
                  color="Segment",
                  color_discrete_sequence=["#4F8EF7","#F7934F","#2ECC71"])
    fig4.update_layout(margin=dict(t=10,b=10), height=280, showlegend=False)
    st.plotly_chart(fig4, use_container_width=True)

with c5:
    st.subheader("🌍 Sales by Region (Top 8)")
    reg = fdf.groupby("Region")["Sales"].sum().nlargest(8).reset_index()
    fig5 = px.bar(reg, x="Region", y="Sales",
                  color="Sales", color_continuous_scale="Teal")
    fig5.update_layout(margin=dict(t=10,b=10), height=280,
                       coloraxis_showscale=False,
                       xaxis=dict(tickangle=-30))
    st.plotly_chart(fig5, use_container_width=True)

# Row 3: Sub-category profit + Discount vs Profit scatter
c6, c7 = st.columns([1, 1])

with c6:
    st.subheader("📦 Sub-Category: Sales vs Profit")
    sub_df = (fdf.groupby("Sub_Category")
                 .agg(Sales=("Sales","sum"), Profit=("Profit","sum"))
                 .reset_index()
                 .sort_values("Sales", ascending=False))
    fig6 = px.scatter(sub_df, x="Sales", y="Profit", text="Sub_Category",
                      color="Profit", color_continuous_scale="RdYlGn",
                      size="Sales", size_max=40)
    fig6.update_traces(textposition="top center", textfont_size=10)
    fig6.update_layout(margin=dict(t=10,b=10), height=340,
                       coloraxis_showscale=False)
    st.plotly_chart(fig6, use_container_width=True)

with c7:
    st.subheader("🔖 Discount Impact on Profit")
    sample = fdf.sample(min(2000, len(fdf)), random_state=42)
    fig7 = px.scatter(sample, x="Discount", y="Profit",
                      color="Category",
                      color_discrete_sequence=["#4F8EF7","#F7934F","#2ECC71"],
                      opacity=0.5)
    fig7.update_layout(margin=dict(t=10,b=10), height=340,
                       legend=dict(orientation="h", y=-0.15))
    st.plotly_chart(fig7, use_container_width=True)

# Raw data preview
with st.expander("📋 View Filtered Data"):
    st.dataframe(fdf[["Order_Date","Customer_Name","Category","Sub_Category",
                       "Region","Segment","Sales","Profit","Quantity","Discount"]]
                   .sort_values("Sales", ascending=False)
                   .reset_index(drop=True),
                 use_container_width=True)
    st.caption(f"{len(fdf):,} rows shown after filters.")