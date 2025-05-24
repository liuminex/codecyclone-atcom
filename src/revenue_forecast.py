import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from xgboost import XGBRegressor

from suggest_bundles import get_average_added_profit

# Load and preprocess your data here (same as before)
orders = pd.read_csv('../data/orders.csv', parse_dates=['CreatedDate'])
orders['OrderDate'] = orders['CreatedDate'].dt.date
unique_orders = orders.drop_duplicates(subset=['OrderNumber'])
daily_revenue = unique_orders.groupby('OrderDate')['TotalOrderAmount'].sum().reset_index()
daily_revenue['OrderDate'] = pd.to_datetime(daily_revenue['OrderDate'])
daily_revenue = daily_revenue.sort_values('OrderDate').reset_index(drop=True)

all_days = pd.date_range(daily_revenue['OrderDate'].min(), daily_revenue['OrderDate'].max())
daily_revenue = daily_revenue.set_index('OrderDate').reindex(all_days, fill_value=0).rename_axis('OrderDate').reset_index()

# Feature engineering function
def create_features(df):
    df['day_of_week'] = df['OrderDate'].dt.dayofweek
    df['day_of_month'] = df['OrderDate'].dt.day
    df['month'] = df['OrderDate'].dt.month
    df['quarter'] = df['OrderDate'].dt.quarter
    return df

# Initial features + lag creation (lag features for training)
daily_revenue = create_features(daily_revenue)

# Add lag features for training data (shifted revenue values)
for lag in range(1, 8):
    daily_revenue[f'lag_{lag}'] = daily_revenue['TotalOrderAmount'].shift(lag).fillna(0)

# Prepare training dataset
features = ['day_of_week', 'day_of_month', 'month', 'quarter'] + [f'lag_{i}' for i in range(1, 8)]
target = 'TotalOrderAmount'

X_train = daily_revenue[features]
y_train = daily_revenue[target]

# Train the model
model = XGBRegressor(
    n_estimators=1000,
    learning_rate=0.05,
    max_depth=5,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    early_stopping_rounds=50,
    verbosity=0
)
model.fit(X_train, y_train, eval_set=[(X_train, y_train)], verbose=False)

# Forecast horizon
fh = 365

# Prepare dataframe to hold future predictions
last_date = daily_revenue['OrderDate'].iloc[-1]
future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=fh)

# Create a dataframe for future dates
future_df = pd.DataFrame({'OrderDate': future_dates})
future_df = create_features(future_df)

# Initialize lag columns for future_df to zero
for lag in range(1, 8):
    future_df[f'lag_{lag}'] = 0.0

# Combine historical + future to help fill lagged values during iteration
full_df = pd.concat([daily_revenue[['OrderDate', 'TotalOrderAmount']], future_df[['OrderDate']]], ignore_index=True)
full_df['TotalOrderAmount'] = pd.concat([daily_revenue['TotalOrderAmount'], pd.Series([np.nan]*fh)], ignore_index=True)

# Iterative forecasting for each future day
for i in range(fh):
    current_date = future_dates[i]
    
    # Fill lag features for current date from full_df
    for lag in range(1, 8):
        lag_date = current_date - pd.Timedelta(days=lag)
        # If lag_date is in full_df, get its TotalOrderAmount; else 0
        if lag_date in full_df['OrderDate'].values:
            lag_value = full_df.loc[full_df['OrderDate'] == lag_date, 'TotalOrderAmount'].values[0]
            if np.isnan(lag_value):
                lag_value = 0
        else:
            lag_value = 0
        future_df.loc[future_df['OrderDate'] == current_date, f'lag_{lag}'] = lag_value

    # Extract features for prediction
    X_pred = future_df[future_df['OrderDate'] == current_date][features]
    pred = model.predict(X_pred)[0]
    
    # Store prediction in future_df and full_df
    future_df.loc[future_df['OrderDate'] == current_date, 'TotalOrderAmount'] = pred
    full_df.loc[full_df['OrderDate'] == current_date, 'TotalOrderAmount'] = pred

# 3rd line: forecast of revenues with bundling
extra_daily_rev = get_average_added_profit()

print(f"Average added profit per day from bundling: {extra_daily_rev}")

# Add the extra daily revenue from bundling to the forecast
future_bundled_df = future_df.copy()
future_bundled_df['TotalOrderAmount'] += extra_daily_rev

# Plot the historical + forecast
plt.figure(figsize=(12,6))
plt.plot(daily_revenue['OrderDate'], daily_revenue['TotalOrderAmount'], label='Historical Daily Revenue')
plt.plot(future_df['OrderDate'], future_df['TotalOrderAmount'], label=f'Forecast Next {fh} Days', linestyle='--', marker='')
plt.plot(future_bundled_df['OrderDate'], future_bundled_df['TotalOrderAmount'], label=f'Bundled Forecast Next {fh} Days', linestyle='--', marker='')
plt.title(f'Daily Revenue and {fh}-Day Forecast (XGBoost)')
plt.xlabel('Date')
plt.ylabel('Revenue')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
