import pandas as pd
import numpy as np
import os
import json
from backend.config import Config


def detect_column_types(df):
    numerical_cols = list(df.select_dtypes(include=[np.number]).columns)
    categorical_cols = list(df.select_dtypes(include=['object', 'category']).columns)
    date_cols = []

    for col in df.columns:
        if col in categorical_cols:
            try:
                pd.to_datetime(df[col], errors='coerce')
                if pd.to_datetime(df[col], errors='coerce').notna().sum() > len(df) * 0.5:
                    date_cols.append(col)
                    categorical_cols.remove(col)
            except:
                pass

    return numerical_cols, categorical_cols, date_cols


def clean_dataset(file_path, upload_id, user_id):
    config = Config()
    df = pd.read_csv(file_path)

    numerical_cols, categorical_cols, date_cols = detect_column_types(df)

    missing_before = df.isnull().sum().to_dict()
    missing_before = {str(k): int(v) for k, v in missing_before.items()}

    duplicates_before = int(df.duplicated().sum())

    for col in numerical_cols:
        df[col] = df[col].fillna(df[col].median())

    for col in categorical_cols:
        df[col] = df[col].fillna(df[col].mode()[0] if not df[col].mode().empty else 'Unknown')

    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors='coerce')
        df[col] = df[col].fillna(method='ffill')

    df = df.drop_duplicates()

    missing_after = df.isnull().sum().to_dict()
    missing_after = {str(k): int(v) for k, v in missing_after.items()}

    duplicates_after = int(df.duplicated().sum())

    outlier_report = {}
    for col in numerical_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
        outlier_report[col] = {
            'lower_bound': float(lower_bound) if not pd.isna(lower_bound) else None,
            'upper_bound': float(upper_bound) if not pd.isna(upper_bound) else None,
            'outlier_count': int(len(outliers)),
            'outlier_percentage': round(float(len(outliers) / len(df) * 100), 2) if len(df) > 0 else 0
        }

    cleaned_filename = f"cleaned_{upload_id}_{os.path.basename(file_path)}"
    cleaned_path = os.path.join(config.CLEANED_FOLDER, cleaned_filename)
    df.to_csv(cleaned_path, index=False)

    summary = {
        'original_rows': int(len(df) + duplicates_before),
        'original_columns': int(len(df.columns)),
        'cleaned_rows': int(len(df)),
        'cleaned_columns': int(len(df.columns)),
        'numerical_columns': numerical_cols,
        'categorical_columns': categorical_cols,
        'date_columns': date_cols,
        'duplicates_removed': duplicates_before - duplicates_after
    }

    missing_report = {
        'missing_before': missing_before,
        'missing_after': missing_after,
        'total_missing_before': int(sum(missing_before.values())),
        'total_missing_after': int(sum(missing_after.values()))
    }

    return df, summary, missing_report, outlier_report, cleaned_path
