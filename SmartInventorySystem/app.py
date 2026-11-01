import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from forecast import forecast_demand


# --------------------------------
# PAGE CONFIGURATION
# --------------------------------

st.set_page_config(
    page_title="Smart Inventory Management",
    page_icon="📦",
    layout="wide"
)


# --------------------------------
# TITLE
# --------------------------------

st.title("📦 Smart Inventory Management System")

st.caption(
    "Inventory Analytics | Demand Forecasting | Business Insights"
)


# --------------------------------
# LOAD DATA
# --------------------------------

@st.cache_data
def load_data():
    data = pd.read_csv("inventory.csv")

    # Remove duplicate records
    data = data.drop_duplicates(subset=["Product_ID"])

    # Clean text columns
    text_columns = [
        "Product_ID",
        "Product_Name",
        "Category",
        "Supplier"
    ]

    for column in text_columns:
        data[column] = data[column].fillna("Unknown").astype(str).str.strip()

    # Convert numeric columns
    numeric_columns = [
        "Quantity",
        "Reorder_Level",
        "Purchase_Price",
        "Selling_Price",
        "Units_Sold"
    ]

    for column in numeric_columns:
        data[column] = pd.to_numeric(
            data[column],
            errors="coerce"
        )

        data[column] = data[column].fillna(0)

    # Convert date column
    data["Stock_Entry_Date"] = pd.to_datetime(
        data["Stock_Entry_Date"],
        errors="coerce"
    )

    # Data validation
    data = data[
        (data["Quantity"] >= 0) &
        (data["Purchase_Price"] >= 0) &
        (data["Selling_Price"] >= 0) &
        (data["Units_Sold"] >= 0)
    ]

    # Stock status
    def get_status(row):
        if row["Quantity"] == 0:
            return "Out of Stock"
        elif row["Quantity"] <= row["Reorder_Level"]:
            return "Low Stock"
        else:
            return "Available"

    data["Stock_Status"] = data.apply(
        get_status,
        axis=1
    )

    # Inventory value
    data["Inventory_Value"] = (
        data["Quantity"] * data["Purchase_Price"]
    )

    # Potential revenue from current stock
    data["Potential_Revenue"] = (
        data["Quantity"] * data["Selling_Price"]
    )

    return data


try:
    df = load_data()
except FileNotFoundError:
    st.error("inventory.csv file not found.")
    st.info("Place inventory.csv in the same folder as app.py.")
    st.stop()


# --------------------------------
# SIDEBAR
# --------------------------------

st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Select Page",
    [
        "Dashboard",
        "Inventory",
        "Stock Alerts",
        "Demand Forecast",
        "Business Insights",
        "Reports"
    ]
)


# --------------------------------
# FILTERS
# --------------------------------

st.sidebar.subheader("Filters")

categories = sorted(df["Category"].unique())

selected_category = st.sidebar.selectbox(
    "Select Category",
    ["All"] + categories
)

if selected_category != "All":
    filtered_df = df[
        df["Category"] == selected_category
    ].copy()
else:
    filtered_df = df.copy()


# --------------------------------
# DASHBOARD
# --------------------------------

if page == "Dashboard":

    st.header("Inventory Dashboard")

    total_products = len(filtered_df)

    total_categories = filtered_df["Category"].nunique()

    available_stock = filtered_df["Quantity"].sum()

    low_stock = len(
        filtered_df[
            filtered_df["Stock_Status"] == "Low Stock"
        ]
    )

    out_of_stock = len(
        filtered_df[
            filtered_df["Stock_Status"] == "Out of Stock"
        ]
    )

    inventory_value = filtered_df["Inventory_Value"].sum()

    # KPI Cards
    col1, col2, col3 = st.columns(3)

    col1.metric("Total Products", total_products)

    col2.metric("Total Categories", total_categories)

    col3.metric("Available Stock", int(available_stock))

    col4, col5, col6 = st.columns(3)

    col4.metric("Low Stock Products", low_stock)

    col5.metric("Out of Stock Products", out_of_stock)

    col6.metric(
        "Inventory Value",
        f"₹{inventory_value:,.2f}"
    )

    st.divider()

    # Category chart
    st.subheader("Category-wise Inventory")

    category_data = (
        filtered_df.groupby("Category")["Quantity"]
        .sum()
        .reset_index()
    )

    fig_category = px.bar(
        category_data,
        x="Category",
        y="Quantity",
        color="Category",
        title="Stock Quantity by Category"
    )

    st.plotly_chart(
        fig_category,
        use_container_width=True
    )

    # Product chart
    st.subheader("Product-wise Stock Distribution")

    fig_product = px.bar(
        filtered_df,
        x="Product_Name",
        y="Quantity",
        color="Stock_Status",
        title="Product Stock Levels"
    )

    st.plotly_chart(
        fig_product,
        use_container_width=True
    )

    # Inventory value chart
    st.subheader("Inventory Value Analysis")

    fig_value = px.pie(
        filtered_df,
        names="Category",
        values="Inventory_Value",
        title="Inventory Value by Category"
    )

    st.plotly_chart(
        fig_value,
        use_container_width=True
    )


# --------------------------------
# INVENTORY PAGE
# --------------------------------

elif page == "Inventory":

    st.header("Inventory Management")

    search = st.text_input(
        "Search Product by Name"
    )

    inventory_df = filtered_df.copy()

    if search:
        inventory_df = inventory_df[
            inventory_df["Product_Name"].str.contains(
                search,
                case=False,
                na=False
            )
        ]

    status_filter = st.selectbox(
        "Filter by Stock Status",
        ["All", "Available", "Low Stock", "Out of Stock"]
    )

    if status_filter != "All":
        inventory_df = inventory_df[
            inventory_df["Stock_Status"] == status_filter
        ]

    sort_by = st.selectbox(
        "Sort By",
        ["Quantity", "Inventory_Value", "Product_Name"]
    )

    inventory_df = inventory_df.sort_values(
        sort_by,
        ascending=True
    )

    st.dataframe(
        inventory_df,
        use_container_width=True,
        hide_index=True
    )


# --------------------------------
# STOCK ALERTS PAGE
# --------------------------------

elif page == "Stock Alerts":

    st.header("🚨 Stock Alert System")

    low_stock_df = filtered_df[
        filtered_df["Stock_Status"] == "Low Stock"
    ]

    out_stock_df = filtered_df[
        filtered_df["Stock_Status"] == "Out of Stock"
    ]

    st.subheader("Low Stock Products")

    if low_stock_df.empty:
        st.success("No low stock products.")
    else:
        st.warning(
            f"{len(low_stock_df)} products need restocking."
        )

        st.dataframe(
            low_stock_df[
                [
                    "Product_Name",
                    "Quantity",
                    "Reorder_Level",
                    "Supplier"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

    st.subheader("Out of Stock Products")

    if out_stock_df.empty:
        st.success("No out-of-stock products.")
    else:
        st.error(
            f"{len(out_stock_df)} products are out of stock."
        )

        st.dataframe(
            out_stock_df[
                [
                    "Product_Name",
                    "Quantity",
                    "Supplier"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )


# --------------------------------
# DEMAND FORECAST PAGE
# --------------------------------

elif page == "Demand Forecast":

    st.header("📈 Demand Forecasting")

    product_name = st.selectbox(
        "Select Product",
        filtered_df["Product_Name"].tolist()
    )

    forecast = forecast_demand(
        df,
        product_name
    )

    product_row = df[
        df["Product_Name"] == product_name
    ].iloc[0]

    current_stock = product_row["Quantity"]

    reorder_level = product_row["Reorder_Level"]

    st.metric(
        "Current Stock",
        int(current_stock)
    )

    if forecast is not None:

        st.metric(
            "Estimated Monthly Demand",
            f"{forecast:.0f} units"
        )

        recommended_stock = max(
            0,
            forecast - current_stock
        )

        st.metric(
            "Estimated Stock Needed",
            f"{recommended_stock:.0f} units"
        )

        if current_stock < reorder_level:
            st.warning(
                "Current stock is below the reorder level."
            )

        if current_stock < forecast:
            st.warning(
                "Current stock may not cover estimated demand."
            )
        else:
            st.success(
                "Current stock may cover estimated demand."
            )

    else:
        st.warning(
            "Not enough historical sales data for this product."
        )


# --------------------------------
# BUSINESS INSIGHTS PAGE
# --------------------------------

elif page == "Business Insights":

    st.header("💡 Inventory Business Insights")

    # Fast moving products
    st.subheader("Top-Selling Products")

    top_products = filtered_df.sort_values(
        "Units_Sold",
        ascending=False
    ).head(5)

    st.dataframe(
        top_products[
            ["Product_Name", "Units_Sold", "Quantity"]
        ],
        use_container_width=True,
        hide_index=True
    )

    # Slow moving products
    st.subheader("Slow-Moving Products")

    slow_products = filtered_df.sort_values(
        "Units_Sold",
        ascending=True
    ).head(5)

    st.dataframe(
        slow_products[
            ["Product_Name", "Units_Sold", "Quantity"]
        ],
        use_container_width=True,
        hide_index=True
    )

    # Overstocked products
    st.subheader("Potential Overstocked Products")

    overstocked = filtered_df[
        filtered_df["Quantity"] > 
        3 * filtered_df["Reorder_Level"]
    ]

    if overstocked.empty:
        st.info("No potential overstocked products.")
    else:
        st.dataframe(
            overstocked[
                ["Product_Name", "Quantity", "Reorder_Level"]
            ],
            use_container_width=True,
            hide_index=True
        )

    # Recommendations
    st.subheader("Restocking Recommendations")

    for _, row in filtered_df.iterrows():

        if row["Stock_Status"] == "Out of Stock":

            st.error(
                f"{row['Product_Name']}: Restock immediately."
            )

        elif row["Stock_Status"] == "Low Stock":

            st.warning(
                f"{row['Product_Name']}: Consider placing a purchase order."
            )

        elif row["Quantity"] > 3 * row["Reorder_Level"]:

            st.info(
                f"{row['Product_Name']}: Review excess inventory."
            )


# --------------------------------
# REPORTS PAGE
# --------------------------------

elif page == "Reports":

    st.header("📄 Inventory Reports")

    st.subheader("Inventory Summary")

    summary = pd.DataFrame({
        "Metric": [
            "Total Products",
            "Total Categories",
            "Total Stock",
            "Low Stock Products",
            "Out of Stock Products",
            "Total Inventory Value"
        ],
        "Value": [
            len(filtered_df),
            filtered_df["Category"].nunique(),
            int(filtered_df["Quantity"].sum()),
            len(filtered_df[
                filtered_df["Stock_Status"] == "Low Stock"
            ]),
            len(filtered_df[
                filtered_df["Stock_Status"] == "Out of Stock"
            ]),
            filtered_df["Inventory_Value"].sum()
        ]
    })

    st.dataframe(
        summary,
        use_container_width=True,
        hide_index=True
    )

    # Export CSV
    csv_data = filtered_df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="Download Inventory Report (CSV)",
        data=csv_data,
        file_name="inventory_report.csv",
        mime="text/csv"
    )

    # Export Excel
    excel_data = None

    try:
        import io

        buffer = io.BytesIO()

        with pd.ExcelWriter(
            buffer,
            engine="openpyxl"
        ) as writer:

            filtered_df.to_excel(
                writer,
                index=False,
                sheet_name="Inventory"
            )

            summary.to_excel(
                writer,
                index=False,
                sheet_name="Summary"
            )

        excel_data = buffer.getvalue()

        st.download_button(
            label="Download Inventory Report (Excel)",
            data=excel_data,
            file_name="inventory_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except ImportError:
        st.info(
            "Install openpyxl to enable Excel export."
        )


# --------------------------------
# FOOTER
# --------------------------------

st.sidebar.divider()

st.sidebar.caption(
    "Smart Inventory Management System | Python & Streamlit"
)