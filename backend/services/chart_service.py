import pandas as pd
import numpy as np


def generate_chart_data(df, chart_type, x_column, y_column=None):
    if chart_type == 'bar':
        if y_column:
            data = df.groupby(x_column)[y_column].sum().reset_index()
            return {
                'labels': data[x_column].astype(str).tolist(),
                'datasets': [{
                    'label': y_column,
                    'data': data[y_column].tolist()
                }]
            }
        else:
            data = df[x_column].value_counts().reset_index()
            data.columns = [x_column, 'count']
            return {
                'labels': data[x_column].astype(str).tolist(),
                'datasets': [{
                    'label': 'Count',
                    'data': data['count'].tolist()
                }]
            }

    elif chart_type == 'line':
        if y_column:
            if pd.api.types.is_datetime64_any_dtype(df[x_column]):
                data = df.sort_values(x_column)
                return {
                    'labels': data[x_column].astype(str).tolist(),
                    'datasets': [{
                        'label': y_column,
                        'data': data[y_column].tolist()
                    }]
                }
            else:
                data = df.groupby(x_column)[y_column].sum().reset_index()
                return {
                    'labels': data[x_column].astype(str).tolist(),
                    'datasets': [{
                        'label': y_column,
                        'data': data[y_column].tolist()
                    }]
                }
        else:
            data = df[x_column].value_counts().sort_index().reset_index()
            data.columns = [x_column, 'count']
            return {
                'labels': data[x_column].astype(str).tolist(),
                'datasets': [{
                    'label': 'Count',
                    'data': data['count'].tolist()
                }]
            }

    elif chart_type == 'pie':
        if y_column:
            data = df.groupby(x_column)[y_column].sum().reset_index()
        else:
            data = df[x_column].value_counts().reset_index()
            data.columns = [x_column, 'count']
            y_column = 'count'
        return {
            'labels': data[x_column].astype(str).tolist(),
            'datasets': [{
                'label': y_column,
                'data': data[y_column if y_column else 'count'].tolist()
            }]
        }

    elif chart_type == 'histogram':
        if not y_column:
            y_column = x_column
        data = df[y_column].dropna()
        return {
            'labels': [f"{i:.1f}-{i+1:.1f}" for i in range(int(data.min()), int(data.max()))],
            'datasets': [{
                'label': 'Frequency',
                'data': np.histogram(data, bins='auto')[0].tolist()
            }],
            'bins': np.histogram_bin_edges(data, bins='auto').tolist()
        }

    elif chart_type == 'scatter':
        if x_column and y_column:
            data = df[[x_column, y_column]].dropna()
            return {
                'labels': data[x_column].tolist(),
                'datasets': [{
                    'label': f'{y_column} vs {x_column}',
                    'data': [{'x': float(r[0]), 'y': float(r[1])} for r in data.values]
                }]
            }

    elif chart_type == 'box':
        numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if y_column and y_column in numerical_cols:
            data = df[y_column].dropna()
            q1 = float(data.quantile(0.25))
            q3 = float(data.quantile(0.75))
            iqr = q3 - q1
            return {
                'labels': [y_column],
                'datasets': [{
                    'label': y_column,
                    'data': [{
                        'min': float(data.min()),
                        'q1': q1,
                        'median': float(data.median()),
                        'q3': q3,
                        'max': float(data.max()),
                        'outliers': data[(data < q1 - 1.5 * iqr) | (data > q3 + 1.5 * iqr)].tolist()
                    }]
                }]
            }

    elif chart_type == 'heatmap':
        numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if len(numerical_cols) > 1:
            corr = df[numerical_cols].corr().round(2)
            return {
                'labels': numerical_cols,
                'datasets': numerical_cols,
                'data': corr.values.tolist()
            }

    return None
