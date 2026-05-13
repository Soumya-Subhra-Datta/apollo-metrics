from flask import Blueprint, jsonify, session
from backend.database.db import get_db_connection
from backend.utils.helpers import login_required

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/api/dashboard/summary', methods=['GET'])
@login_required
def get_dashboard_summary():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute('SELECT COUNT(*) as total FROM uploads WHERE user_id = %s', (session['user_id'],))
        total_uploads = cursor.fetchone()['total']

        cursor.execute('SELECT COUNT(*) as total FROM user_queries WHERE user_id = %s', (session['user_id'],))
        total_queries = cursor.fetchone()['total']

        cursor.execute('SELECT COUNT(*) as total FROM model_results WHERE user_id = %s', (session['user_id'],))
        total_models = cursor.fetchone()['total']

        cursor.execute('SELECT COUNT(*) as total FROM reports WHERE user_id = %s', (session['user_id'],))
        total_reports = cursor.fetchone()['total']

        cursor.execute(
            'SELECT id, file_name, total_rows, total_columns, uploaded_at FROM uploads WHERE user_id = %s ORDER BY uploaded_at DESC LIMIT 5',
            (session['user_id'],)
        )
        recent_uploads = cursor.fetchall()

        cursor.execute(
            'SELECT q.id, q.question, q.answer, q.created_at, u.file_name FROM user_queries q JOIN uploads u ON q.upload_id = u.id WHERE q.user_id = %s ORDER BY q.created_at DESC LIMIT 5',
            (session['user_id'],)
        )
        recent_queries = cursor.fetchall()

        cursor.execute(
            'SELECT m.id, m.model_name, m.task_type, m.target_column, m.created_at, u.file_name FROM model_results m JOIN uploads u ON m.upload_id = u.id WHERE m.user_id = %s ORDER BY m.created_at DESC LIMIT 5',
            (session['user_id'],)
        )
        recent_models = cursor.fetchall()

        cursor.close()
        conn.close()

        for item in recent_uploads:
            if item.get('uploaded_at'):
                item['uploaded_at'] = item['uploaded_at'].strftime('%Y-%m-%d %H:%M:%S')

        for item in recent_queries:
            if item.get('created_at'):
                item['created_at'] = item['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            if item.get('answer'):
                item['answer'] = item['answer'][:200] + '...' if len(item['answer']) > 200 else item['answer']

        for item in recent_models:
            if item.get('created_at'):
                item['created_at'] = item['created_at'].strftime('%Y-%m-%d %H:%M:%S')

        return jsonify({
            'user': {
                'full_name': session.get('full_name', 'User'),
                'email': session.get('email', '')
            },
            'stats': {
                'total_uploads': total_uploads,
                'total_queries': total_queries,
                'total_models': total_models,
                'total_reports': total_reports
            },
            'recent_uploads': recent_uploads,
            'recent_queries': recent_queries,
            'recent_models': recent_models
        }), 200

    except Exception as e:
        return jsonify({'error': f'Failed to load dashboard: {str(e)}'}), 500
