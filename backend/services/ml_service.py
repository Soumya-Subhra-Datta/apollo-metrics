import pandas as pd
import numpy as np
import os
import json
import warnings
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.svm import SVC
from sklearn.cluster import KMeans
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, mean_absolute_error, mean_squared_error,
    r2_score, silhouette_score
)
from backend.config import Config


def detect_task_type(df, target_column):
    if not target_column or target_column not in df.columns:
        return 'clustering'

    if df[target_column].dtype in ['object', 'category', 'bool']:
        return 'classification'

    unique_vals = df[target_column].nunique()
    if unique_vals <= 20:
        return 'classification'

    return 'regression'


def _to_numeric(df, cols):
    for col in cols:
        if col in df.columns and df[col].dtype not in [np.number, bool]:
            try:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            except:
                le = LabelEncoder()
                df[col] = le.fit_transform(df[col].astype(str))
    return df


def _remove_constant_features(X, feature_names):
    keep = []
    kept_names = []
    for i, name in enumerate(feature_names):
        col = X[:, i]
        if np.nanvar(col) > 1e-10:
            keep.append(i)
            kept_names.append(name)
    if len(keep) == 0:
        return X, feature_names
    return X[:, keep], kept_names


def _safe_inverse_transform(scaler, X, feature_names):
    try:
        return scaler.inverse_transform(X)
    except:
        return X


def _suggest_categorical_target(df, current_target):
    cats = [c for c in df.columns if c != current_target and df[c].dtype in ['object', 'category', 'bool']]
    if cats:
        return cats[0]
    low_card = [c for c in df.columns if c != current_target and df[c].nunique() <= 20]
    if low_card:
        return low_card[0]
    return None


def preprocess_data(df, target_column, task_type):
    df_clean = df.copy()

    for col in df_clean.columns:
        df_clean[col] = df_clean[col].replace([np.inf, -np.inf], np.nan)

    df_clean = df_clean.dropna(how='all', axis=1)

    if task_type == 'clustering':
        feature_df = df_clean.select_dtypes(include=[np.number]).copy()
        feature_df = feature_df.dropna(how='all', axis=1)
        if feature_df.empty:
            feature_df = pd.DataFrame(index=df_clean.index, data={'dummy': np.zeros(len(df_clean))})
        for col in feature_df.columns:
            if feature_df[col].isnull().all():
                feature_df[col] = 0
            else:
                feature_df[col] = feature_df[col].fillna(feature_df[col].median())
        feature_names = feature_df.columns.tolist()
        X_raw = feature_df.values.astype(np.float64)
        X_raw, feature_names = _remove_constant_features(X_raw, feature_names)
        if X_raw.shape[1] == 0:
            X_raw = np.zeros((len(feature_df), 1))
            feature_names = ['dummy']
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_raw)
        return X_scaled, None, scaler, feature_names

    if target_column not in df_clean.columns:
        raise ValueError(f"Target column '{target_column}' not found in dataset.")

    df_clean = df_clean.dropna(subset=[target_column])
    if df_clean.empty:
        raise ValueError("Dataset is empty after removing rows with missing target values.")

    label_encoders = {}
    target_dtype = df_clean[target_column].dtype
    target_unique = df_clean[target_column].nunique()

    if task_type == 'regression' and target_dtype in ['object', 'category', 'bool']:
        raise ValueError(
            f"Target column '{target_column}' is categorical ({target_dtype}). "
            f"Regression requires numeric values. Select a numeric column or change task type to Classification."
        )

    if task_type == 'classification' and target_dtype not in ['object', 'category', 'bool'] and target_unique > 30:
        pass  # warning already emitted in train_models

    if df_clean[target_column].dtype in ['object', 'category', 'bool'] or (task_type == 'classification' and target_dtype not in ['object', 'category', 'bool']):
        le_target = LabelEncoder()
        valid = df_clean[target_column].notna()
        df_clean.loc[valid, target_column] = le_target.fit_transform(
            df_clean.loc[valid, target_column].astype(str)
        )
        label_encoders['target'] = le_target

    df_clean = _to_numeric(df_clean, [c for c in df_clean.columns if c != target_column])

    df_clean = df_clean.fillna(df_clean.median(numeric_only=True))
    df_clean = df_clean.fillna(0)

    feature_cols = [col for col in df_clean.columns if col != target_column]
    numerical_feats = df_clean[feature_cols].select_dtypes(include=[np.number]).columns.tolist()

    if not numerical_feats:
        numerical_feats = ['_dummy']
        df_clean['_dummy'] = 0

    X_raw = df_clean[numerical_feats].values.astype(np.float64)
    y = df_clean[target_column].values

    has_nan_y = pd.isna(y).any()
    if has_nan_y:
        valid_mask = ~pd.isna(y)
        X_raw = X_raw[valid_mask]
        y = y[valid_mask]

    if len(np.unique(y)) < 2:
        raise ValueError(
            f"Target column has only {len(np.unique(y))} unique value(s). "
            "Need at least 2 distinct values for supervised learning."
        )

    X_raw, kept_features = _remove_constant_features(X_raw, numerical_feats)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_raw)

    return X_scaled, y, scaler, kept_features, label_encoders


def train_models(df, target_column, upload_id, user_id, task_type=None):
    config = Config()
    task_warning = None

    if not task_type:
        task_type = detect_task_type(df, target_column)

    if target_column and target_column in df.columns:
        col_dtype = df[target_column].dtype
        n_unique = df[target_column].nunique()
        is_numeric = col_dtype in ['int64', 'float64', 'int32', 'float32']
        is_categorical = col_dtype in ['object', 'category', 'bool']

        if task_type == 'classification' and is_numeric and n_unique > 30:
            suggested = _suggest_categorical_target(df, target_column)
            task_warning = (
                f"Target column '{target_column}' is numeric with {n_unique} unique values (continuous). "
                f"Classification works best with discrete labels (few unique values). "
                + (f"Did you mean to select '{suggested}' as the target? " if suggested else "")
                + f"Training with {n_unique} class labels anyway."
            )
            warnings.warn(task_warning)
        elif task_type == 'regression' and (is_categorical or n_unique <= 10):
            if is_categorical:
                warnings.warn(
                    f"Target column '{target_column}' is categorical ({col_dtype}). "
                    f"Regression requires numeric values. Consider using Classification instead."
                )
            else:
                warnings.warn(
                    f"Target column '{target_column}' has only {n_unique} unique values. "
                    f"Regression typically works best with continuous values. "
                    f"Consider using Classification instead."
                )

    try:
        if task_type == 'clustering':
            X, _, scaler, feature_names = preprocess_data(df, target_column, task_type)
        else:
            X, y, scaler, feature_names, label_encoders = preprocess_data(df, target_column, task_type)
    except ValueError as e:
        return {
            'task_type': task_type,
            'target_column': target_column,
            'best_model': None,
            'best_score': 0,
            'all_results': {},
            'error': str(e),
            'task_warning': task_warning
        }

    results = {}
    best_model = None
    best_score = 0
    best_model_name = None

    if task_type == 'classification':
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        models = {
            'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
            'Decision Tree': DecisionTreeClassifier(random_state=42),
            'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42)
        }

        if X.shape[1] <= 50 and len(np.unique(y)) <= 10:
            models['SVM'] = SVC(kernel='rbf', random_state=42, probability=True)

        for model_name, model in models.items():
            try:
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)

                metrics = {
                    'accuracy': round(accuracy_score(y_test, y_pred), 4),
                    'precision': round(precision_score(y_test, y_pred, average='weighted', zero_division=0), 4),
                    'recall': round(recall_score(y_test, y_pred, average='weighted', zero_division=0), 4),
                    'f1_score': round(f1_score(y_test, y_pred, average='weighted', zero_division=0), 4),
                }

                cm = confusion_matrix(y_test, y_pred).tolist()
                results[model_name] = {
                    'metrics': metrics,
                    'confusion_matrix': cm
                }

                if metrics['accuracy'] > best_score:
                    best_score = metrics['accuracy']
                    best_model = model
                    best_model_name = model_name
            except Exception as e:
                results[model_name] = {'error': str(e)}

        if len(np.unique(y)) == 2:
            for model_name in list(results.keys()):
                if 'metrics' in results[model_name]:
                    m = results[model_name]['metrics']
                    if m.get('precision', 0) < 0.5 or m.get('recall', 0) < 0.5:
                        pass

    elif task_type == 'regression':
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        models = {
            'Linear Regression': LinearRegression(),
            'Decision Tree Regressor': DecisionTreeRegressor(random_state=42),
            'Random Forest Regressor': RandomForestRegressor(n_estimators=100, random_state=42)
        }

        for model_name, model in models.items():
            try:
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)

                mae = mean_absolute_error(y_test, y_pred)
                mse = mean_squared_error(y_test, y_pred)
                rmse = np.sqrt(mse)
                r2 = r2_score(y_test, y_pred)

                metrics = {
                    'mae': round(mae, 4),
                    'mse': round(mse, 4),
                    'rmse': round(rmse, 4),
                    'r2_score': round(r2, 4)
                }

                results[model_name] = {'metrics': metrics}

                if r2 > best_score:
                    best_score = r2
                    best_model = model
                    best_model_name = model_name
            except Exception as e:
                results[model_name] = {'error': str(e)}

    elif task_type == 'clustering':
        n_clusters = min(5, len(df))
        if n_clusters < 2:
            n_clusters = 2

        model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = model.fit_predict(X)

        sil_score = silhouette_score(X, cluster_labels) if n_clusters > 1 and n_clusters < len(X) else 0

        cluster_centers_df = pd.DataFrame(
            scaler.inverse_transform(model.cluster_centers_),
            columns=feature_names
        )
        cluster_summary = cluster_centers_df.round(2).to_dict(orient='records')

        metrics = {
            'silhouette_score': round(float(sil_score), 4),
            'n_clusters': n_clusters,
            'inertia': round(float(model.inertia_), 2)
        }

        results['K-Means Clustering'] = {
            'metrics': metrics,
            'cluster_summary': cluster_summary,
            'cluster_labels': cluster_labels.tolist()
        }

        best_model = model
        best_model_name = 'K-Means Clustering'
        best_score = sil_score

    if best_model and best_model_name:
        model_filename = f"model_{upload_id}_{best_model_name.replace(' ', '_')}.joblib"
        model_path = os.path.join(config.MODELS_FOLDER, model_filename)
        joblib.dump(best_model, model_path)

        return {
            'task_type': task_type,
            'target_column': target_column if target_column else 'None (Clustering)',
            'best_model': best_model_name,
            'best_score': float(round(best_score, 4)),
            'all_results': results,
            'model_path': model_path,
            'feature_names': feature_names,
            'n_features': len(feature_names),
            'task_warning': task_warning
        }

    return {
        'task_type': task_type,
        'target_column': target_column,
        'best_model': None,
        'best_score': 0,
        'all_results': results,
        'error': 'No models could be trained successfully.',
        'task_warning': task_warning
    }
