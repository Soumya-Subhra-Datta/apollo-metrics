import pandas as pd
import json
from flask import Blueprint, request, jsonify, session
from backend.database.db import get_db_connection
from backend.utils.helpers import login_required
from backend.services.llm_service import ask_dataset_question
from backend.services.eda_service import generate_eda

query_bp = Blueprint('query', __name__)


@query_bp.route('/api/query', methods=['POST'])
@login_required
def ask_question():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    upload_id = data.get('upload_id')
    question = data.get('question', '').strip()

    if not upload_id or not question:
        return jsonify({'error': 'upload_id and question are required'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            'SELECT file_path, file_name, total_rows, total_columns FROM uploads WHERE id = %s AND user_id = %s',
            (upload_id, session['user_id'])
        )
        upload = cursor.fetchone()

        if not upload:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Upload not found'}), 404

        df = pd.read_csv(upload['file_path'])

        eda_results = generate_eda(df, upload['file_path'])

        numerical_stats = eda_results.get('numerical_stats', {})
        categorical_stats = eda_results.get('categorical_stats', {})
        insights = eda_results.get('insights', [])
        overview = eda_results.get('overview', {})
        missing_report = eda_results.get('missing_report', {})

        dataset_summary = {
            'file_name': upload['file_name'],
            'total_rows': upload['total_rows'],
            'total_columns': upload['total_columns'],
            'columns': overview.get('column_names', []),
            'numerical_columns': overview.get('numerical_cols_list', []),
            'categorical_columns': overview.get('categorical_cols_list', []),
            'date_columns': overview.get('date_cols_list', []),
            'missing_values_total': overview.get('missing_values', 0),
            'duplicate_rows': overview.get('duplicate_rows', 0),
            'numerical_statistics': numerical_stats,
            'categorical_summary': {k: {'unique_values': v.get('unique_values', 0),
                                        'top_values': list(v.get('top_values', {}).keys())[:5],
                                        'top_value_counts': list(v.get('top_values', {}).values())[:5]}
                                     for k, v in categorical_stats.items()},
            'missing_report': missing_report,
            'insights': insights[:5]
        }

        answer = ask_dataset_question(question, dataset_summary)

        cursor.execute(
            'INSERT INTO user_queries (user_id, upload_id, question, answer) VALUES (%s, %s, %s, %s)',
            (session['user_id'], upload_id, question, answer)
        )
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            'question': question,
            'answer': answer
        }), 200

    except Exception as e:
        return jsonify({'error': f'Query failed: {str(e)}'}), 500


@query_bp.route('/api/query/history/<int:upload_id>', methods=['GET'])
@login_required
def get_query_history(upload_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            'SELECT id, question, answer, created_at FROM user_queries WHERE upload_id = %s AND user_id = %s ORDER BY created_at DESC',
            (upload_id, session['user_id'])
        )
        queries = cursor.fetchall()
        cursor.close()
        conn.close()

        for q in queries:
            if q.get('created_at'):
                q['created_at'] = q['created_at'].strftime('%Y-%m-%d %H:%M:%S')

        return jsonify({'queries': queries}), 200

    except Exception as e:
        return jsonify({'error': f'Failed to fetch query history: {str(e)}'}), 500


@query_bp.route('/api/query/history/<int:upload_id>', methods=['DELETE'])
@login_required
def clear_query_history(upload_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'DELETE FROM user_queries WHERE upload_id = %s AND user_id = %s',
            (upload_id, session['user_id'])
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'Query history cleared successfully'}), 200
    except Exception as e:
        return jsonify({'error': f'Failed to clear history: {str(e)}'}), 500


@query_bp.route('/api/query/history', methods=['DELETE'])
@login_required
def clear_all_query_history():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'DELETE FROM user_queries WHERE user_id = %s',
            (session['user_id'],)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'All query history cleared successfully'}), 200
    except Exception as e:
        return jsonify({'error': f'Failed to clear history: {str(e)}'}), 500
