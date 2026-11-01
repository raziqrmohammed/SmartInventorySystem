import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression


def forecast_demand(data, product_name, days=30):
    """
    Estimate future demand using historical monthly sales.

    The dataset must contain:
    Product_Name, Units_Sold, Stock_Entry_Date
    """

    product_data = data[
        data["Product_Name"] == product_name
    ].copy()

    if product_data.empty:
        return None

    product_data["Stock_Entry_Date"] = pd.to_datetime(
        product_data["Stock_Entry_Date"],
        errors="coerce"
    )

    product_data = product_data.dropna(
        subset=["Stock_Entry_Date", "Units_Sold"]
    )

    if product_data.empty:
        return None

    # Aggregate historical sales by month
    monthly_sales = (
        product_data
        .set_index("Stock_Entry_Date")["Units_Sold"]
        .resample("MS")
        .sum()
        .reset_index()
    )

    monthly_sales = monthly_sales[
        monthly_sales["Units_Sold"] >= 0
    ]

    if len(monthly_sales) < 2:
        # Not enough historical data for regression
        return float(monthly_sales["Units_Sold"].mean())

    # Create sequential month numbers
    monthly_sales["Month_Number"] = np.arange(
        len(monthly_sales)
    )

    X = monthly_sales[["Month_Number"]]
    y = monthly_sales["Units_Sold"]

    # Train model
    model = LinearRegression()
    model.fit(X, y)

    # Predict next month
    next_month = len(monthly_sales)

    predicted_demand = model.predict(
        pd.DataFrame({"Month_Number": [next_month]})
    )[0]

    # Demand cannot be negative
    predicted_demand = max(0, predicted_demand)

    # Return estimated monthly demand
    return round(float(predicted_demand), 2)