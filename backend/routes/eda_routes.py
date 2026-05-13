import os
import json
import pandas as pd
from flask import Blueprint, jsonify, session
from backend.database.db import get_db_connection
from backend.utils.helpers import login_required
from backend.services.cleaning_service import clean_dataset
from backend.services.eda_service import generate_eda

eda_bp = Blueprint('eda', __name__)


@eda_bp.route('/api/eda/<int:upload_id>', methods=['GET'])
@login_required
def perform_eda(upload_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            'SELECT id, file_name, file_path, user_id FROM uploads WHERE id = %s AND user_id = %s',
            (upload_id, session['user_id'])
        )
        upload = cursor.fetchone()

        if not upload:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Upload not found'}), 404

        df = pd.read_csv(upload['file_path'])

        cleaned_df, summary, missing_report, outlier_report, cleaned_path = clean_dataset(
            upload['file_path'], upload_id, session['user_id']
        )

        cursor.execute(
            'SELECT id FROM analysis_history WHERE upload_id = %s AND user_id = %s',
            (upload_id, session['user_id'])
        )
        existing = cursor.fetchone()

        if existing:
            cursor.execute(
                'UPDATE analysis_history SET summary = %s, missing_value_report = %s, outlier_report = %s, cleaned_file_path = %s WHERE upload_id = %s AND user_id = %s',
                (json.dumps(summary), json.dumps(missing_report), json.dumps(outlier_report), cleaned_path, upload_id, session['user_id'])
            )
        else:
            cursor.execute(
                'INSERT INTO analysis_history (upload_id, user_id, summary, missing_value_report, outlier_report, cleaned_file_path) VALUES (%s, %s, %s, %s, %s, %s)',
                (upload_id, session['user_id'], json.dumps(summary), json.dumps(missing_report), json.dumps(outlier_report), cleaned_path)
            )
        conn.commit()

        eda_results = generate_eda(cleaned_df, cleaned_path)

        cursor.close()
        conn.close()

        return jsonify({
            'message': 'EDA completed successfully',
            'file_name': upload['file_name'],
            'cleaning_summary': summary,
            'missing_report': missing_report,
            'outlier_report': outlier_report,
            'eda': eda_results
        }), 200

    except Exception as e:
        return jsonify({'error': f'EDA failed: {str(e)}'}), 500
