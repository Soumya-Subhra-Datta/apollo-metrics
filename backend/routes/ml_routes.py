import os
import json
import pandas as pd
from flask import Blueprint, request, jsonify, session, send_file
from backend.database.db import get_db_connection
from backend.utils.helpers import login_required
from backend.services.ml_service import train_models
from backend.services.eda_service import generate_eda
from backend.services.llm_service import explain_ml_results
from backend.config import Config

ml_bp = Blueprint('ml', __name__)


@ml_bp.route('/api/ml/train', methods=['POST'])
@login_required
def train():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    upload_id = data.get('upload_id')
    target_column = data.get('target_column', '')
    task_type = data.get('task_type', '')

    if not upload_id:
        return jsonify({'error': 'upload_id is required'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            'SELECT file_path, file_name FROM uploads WHERE id = %s AND user_id = %s',
            (upload_id, session['user_id'])
        )
        upload = cursor.fetchone()

        if not upload:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Upload not found'}), 404

        df = pd.read_csv(upload['file_path'])

        if target_column and target_column not in df.columns:
            cursor.close()
            conn.close()
            return jsonify({'error': f'Target column "{target_column}" not found in dataset'}), 400

        config = Config()
        ml_results = train_models(df, target_column, upload_id, session['user_id'], task_type if task_type else None)

        if ml_results.get('error'):
            cursor.close()
            conn.close()
            return jsonify({
                'error': ml_results['error'],
                'results': ml_results,
                'individual_errors': {
                    name: r.get('error', '')
                    for name, r in ml_results.get('all_results', {}).items()
                    if r.get('error')
                }
            }), 500

        metrics_json = {}
        for model_name, result in ml_results.get('all_results', {}).items():
            if 'metrics' in result:
                metrics_json[model_name] = result['metrics']

        cursor.execute(
            'INSERT INTO model_results (user_id, upload_id, target_column, task_type, model_name, metrics, model_path) VALUES (%s, %s, %s, %s, %s, %s, %s)',
            (
                session['user_id'], upload_id,
                ml_results.get('target_column', ''),
                ml_results.get('task_type', ''),
                ml_results.get('best_model', ''),
                json.dumps(metrics_json),
                ml_results.get('model_path', '')
            )
        )
        conn.commit()
        model_result_id = cursor.lastrowid

        eda_summary = generate_eda(df, upload['file_path'])
        dataset_summary = {
            'dataset_name': upload['file_name'],
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'numerical_columns': eda_summary.get('overview', {}).get('numerical_cols_list', []),
            'categorical_columns': eda_summary.get('overview', {}).get('categorical_cols_list', []),
        }

        explanation = explain_ml_results(ml_results, dataset_summary)

        cursor.close()
        conn.close()

        return jsonify({
            'message': 'Model training completed successfully',
            'results': ml_results,
            'model_result_id': model_result_id,
            'llm_explanation': explanation
        }), 200

    except Exception as e:
        return jsonify({'error': f'Model training failed: {str(e)}'}), 500


@ml_bp.route('/api/ml/download/<int:result_id>', methods=['GET'])
@login_required
def download_model(result_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'SELECT model_path, model_name, task_type FROM model_results WHERE id = %s AND user_id = %s',
            (result_id, session['user_id'])
        )
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if not result:
            return jsonify({'error': 'Model result not found'}), 404

        if not result.get('model_path') or not os.path.exists(result['model_path']):
            return jsonify({'error': 'Model file not found on server'}), 404

        ext = '.joblib'
        download_name = f"{result['model_name'].replace(' ', '_')}_{result['task_type']}{ext}"

        return send_file(
            result['model_path'],
            as_attachment=True,
            download_name=download_name
        ), 200

    except Exception as e:
        return jsonify({'error': f'Download failed: {str(e)}'}), 500


@ml_bp.route('/api/ml/results/<int:upload_id>', methods=['GET'])
@login_required
def get_results(upload_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            'SELECT id, target_column, task_type, model_name, metrics, created_at FROM model_results WHERE upload_id = %s AND user_id = %s ORDER BY created_at DESC',
            (upload_id, session['user_id'])
        )
        results = cursor.fetchall()
        cursor.close()
        conn.close()

        for r in results:
            if isinstance(r.get('metrics'), str):
                r['metrics'] = json.loads(r['metrics'])
            if r.get('created_at'):
                r['created_at'] = r['created_at'].strftime('%Y-%m-%d %H:%M:%S')

        return jsonify({'results': results}), 200

    except Exception as e:
        return jsonify({'error': f'Failed to fetch ML results: {str(e)}'}), 500
