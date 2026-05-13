import pandas as pd
import numpy as np
import json


def generate_eda(df, cleaned_path):
    numerical_cols = list(df.select_dtypes(include=[np.number]).columns)
    categorical_cols = list(df.select_dtypes(include=['object', 'category']).columns)

    date_cols = []
    for col in df.columns:
        if df[col].dtype == 'datetime64[ns]':
            date_cols.append(col)
        elif col in categorical_cols:
            try:
                pd.to_datetime(df[col], errors='coerce')
                if pd.to_datetime(df[col], errors='coerce').notna().sum() > len(df) * 0.5:
                    date_cols.append(col)
            except:
                pass

    overview = {
        'total_rows': int(len(df)),
        'total_columns': int(len(df.columns)),
        'numerical_columns': len(numerical_cols),
        'categorical_columns': len(categorical_cols),
        'date_columns': len(date_cols),
        'missing_values': int(df.isnull().sum().sum()),
        'duplicate_rows': int(df.duplicated().sum()),
        'column_names': list(df.columns),
        'numerical_cols_list': numerical_cols,
        'categorical_cols_list': categorical_cols,
        'date_cols_list': date_cols
    }

    numerical_stats = {}
    for col in numerical_cols:
        numerical_stats[col] = {
            'mean': round(float(df[col].mean()), 2) if not df[col].isnull().all() else 0,
            'median': round(float(df[col].median()), 2) if not df[col].isnull().all() else 0,
            'std': round(float(df[col].std()), 2) if not df[col].isnull().all() else 0,
            'min': round(float(df[col].min()), 2) if not df[col].isnull().all() else 0,
            'max': round(float(df[col].max()), 2) if not df[col].isnull().all() else 0,
            'q1': round(float(df[col].quantile(0.25)), 2) if not df[col].isnull().all() else 0,
            'q3': round(float(df[col].quantile(0.75)), 2) if not df[col].isnull().all() else 0
        }

    categorical_stats = {}
    for col in categorical_cols:
        value_counts = df[col].value_counts().head(10).to_dict()
        categorical_stats[col] = {
            'unique_values': int(df[col].nunique()),
            'top_values': {str(k): int(v) for k, v in value_counts.items()},
            'missing': int(df[col].isnull().sum())
        }

    correlation_matrix = {}
    if len(numerical_cols) > 1:
        corr_df = df[numerical_cols].corr()
        correlation_matrix = {
            'columns': numerical_cols,
            'data': corr_df.round(2).values.tolist()
        }

    date_trends = {}
    for col in date_cols:
        date_series = pd.to_datetime(df[col], errors='coerce')
        if not date_series.isnull().all():
            date_trends[col] = date_series.dt.strftime('%Y-%m-%d').dropna().tolist()

    missing_report = {}
    for col in df.columns:
        missing_count = int(df[col].isnull().sum())
        if missing_count > 0:
            missing_report[col] = {
                'missing_count': missing_count,
                'missing_percentage': round(missing_count / len(df) * 100, 2)
            }

    insights = []
    for col in numerical_cols:
        skew = df[col].skew()
        if abs(skew) > 1:
            insights.append(f"Column '{col}' is highly skewed (skewness={round(skew, 2)}). Consider transformation.")
        elif abs(skew) > 0.5:
            insights.append(f"Column '{col}' is moderately skewed (skewness={round(skew, 2)}).")

    for col in categorical_cols:
        unique_ratio = df[col].nunique() / len(df)
        if unique_ratio > 0.9:
            insights.append(f"Column '{col}' has high cardinality ({df[col].nunique()} unique values). It may not be useful for analysis.")
        elif unique_ratio < 0.05 and df[col].nunique() < 10:
            top_val = df[col].value_counts().index[0]
            top_pct = round(df[col].value_counts().iloc[0] / len(df) * 100, 2)
            insights.append(f"Column '{col}' is dominated by '{top_val}' ({top_pct}% of values).")

    if missing_report:
        insights.append(f"Dataset has {len(missing_report)} column(s) with missing values. Consider addressing these gaps.")

    if df.duplicated().sum() > 0:
        insights.append(f"Dataset contains {int(df.duplicated().sum())} duplicate rows. These were removed during cleaning.")

    if len(numerical_cols) >= 2:
        high_corr_pairs = []
        corr_data = df[numerical_cols].corr()
        for i in range(len(numerical_cols)):
            for j in range(i + 1, len(numerical_cols)):
                val = corr_data.iloc[i, j]
                if abs(val) > 0.7:
                    high_corr_pairs.append(f"'{numerical_cols[i]}' and '{numerical_cols[j]}' (r={round(val, 2)})")
        if high_corr_pairs:
            insights.append(f"Strong correlations detected: {', '.join(high_corr_pairs[:3])}.")

    top_unique_values = {}
    for col in categorical_cols:
        if df[col].nunique() <= 20:
            top_unique_values[col] = df[col].value_counts().head(10).to_dict()

    return {
        'overview': overview,
        'numerical_stats': numerical_stats,
        'categorical_stats': categorical_stats,
        'correlation_matrix': correlation_matrix,
        'date_trends': date_trends,
        'missing_report': missing_report,
        'insights': insights,
        'top_unique_values': top_unique_values,
        'preview': df.head(20).to_dict(orient='records')
    }
