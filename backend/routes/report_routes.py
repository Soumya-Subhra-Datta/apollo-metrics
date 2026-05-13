import os
import json
import pandas as pd
from flask import Blueprint, request, jsonify, session, send_file
from backend.database.db import get_db_connection
from backend.utils.helpers import login_required
from backend.services.report_service import generate_report
from backend.services.eda_service import generate_eda
from backend.services.llm_service import explain_ml_results, generate_business_recommendations

report_bp = Blueprint('reports', __name__)


@report_bp.route('/api/reports/generate', methods=['POST'])
@login_required
def create_report():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    upload_id = data.get('upload_id')

    if not upload_id:
        return jsonify({'error': 'upload_id is required'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            'SELECT id, file_name, file_path FROM uploads WHERE id = %s AND user_id = %s',
            (upload_id, session['user_id'])
        )
        upload = cursor.fetchone()

        if not upload:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Upload not found'}), 404

        cursor.execute(
            'SELECT summary, missing_value_report, outlier_report, cleaned_file_path FROM analysis_history WHERE upload_id = %s AND user_id = %s ORDER BY created_at DESC LIMIT 1',
            (upload_id, session['user_id'])
        )
        analysis = cursor.fetchone()

        cursor.execute(
            'SELECT id, target_column, task_type, model_name, metrics, model_path FROM model_results WHERE upload_id = %s AND user_id = %s ORDER BY created_at DESC LIMIT 1',
            (upload_id, session['user_id'])
        )
        model_result = cursor.fetchone()

        cursor.close()
        conn.close()

        df = pd.read_csv(upload['file_path'])
        eda_results = generate_eda(df, upload['file_path'])

        cleaning_summary = {}
        missing_report_dict = {}
        outlier_report_dict = {}
        if analysis:
            if analysis.get('summary'):
                cleaning_summary = json.loads(analysis['summary']) if isinstance(analysis['summary'], str) else analysis['summary']
            if analysis.get('missing_value_report'):
                missing_report_dict = json.loads(analysis['missing_value_report']) if isinstance(analysis['missing_value_report'], str) else analysis['missing_value_report']
            if analysis.get('outlier_report'):
                outlier_report_dict = json.loads(analysis['outlier_report']) if isinstance(analysis['outlier_report'], str) else analysis['outlier_report']

        dataset_summary = {
            'dataset_name': upload['file_name'],
            'Total Rows': len(df),
            'Total Columns': len(df.columns),
            'Numerical Columns': len(eda_results.get('overview', {}).get('numerical_cols_list', [])),
            'Categorical Columns': len(eda_results.get('overview', {}).get('categorical_cols_list', []))
        }

        ml_results_for_llm = None
        if model_result:
            ml_results_for_llm = {
                'task_type': model_result.get('task_type'),
                'target_column': model_result.get('target_column'),
                'best_model': model_result.get('model_name'),
                'all_results': json.loads(model_result.get('metrics', '{}')) if isinstance(model_result.get('metrics'), str) else model_result.get('metrics', {})
            }

        llm_explanation = None
        if ml_results_for_llm:
            llm_explanation = explain_ml_results(ml_results_for_llm, dataset_summary)

        recommendations = generate_business_recommendations(
            dataset_summary,
            {'insights': eda_results.get('insights', [])},
            ml_results_for_llm
        )

        report_name = f"report_{upload_id}_{session['user_id']}"
        report_path = generate_report(
            user_name=session.get('full_name', 'User'),
            dataset_name=upload['file_name'],
            dataset_summary=dataset_summary,
            cleaning_summary=cleaning_summary,
            eda_results=eda_results,
            ml_results=ml_results_for_llm,
            llm_explanation=llm_explanation,
            recommendations=recommendations,
            report_name=report_name
        )

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            'INSERT INTO reports (user_id, upload_id, report_name, report_path) VALUES (%s, %s, %s, %s)',
            (session['user_id'], upload_id, f"{upload['file_name']}_Report.pdf", report_path)
        )
        conn.commit()
        report_id = cursor.lastrowid
        cursor.close()
        conn.close()

        return jsonify({
            'message': 'Report generated successfully',
            'report_id': report_id,
            'report_name': f"{upload['file_name']}_Report.pdf"
        }), 201

    except Exception as e:
        return jsonify({'error': f'Report generation failed: {str(e)}'}), 500


@report_bp.route('/api/reports', methods=['GET'])
@login_required
def get_reports():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'SELECT r.id, r.report_name, r.created_at, u.file_name FROM reports r JOIN uploads u ON r.upload_id = u.id WHERE r.user_id = %s ORDER BY r.created_at DESC',
            (session['user_id'],)
        )
        reports = cursor.fetchall()
        cursor.close()
        conn.close()

        for r in reports:
            if r.get('created_at'):
                r['created_at'] = r['created_at'].strftime('%Y-%m-%d %H:%M:%S')

        return jsonify({'reports': reports}), 200

    except Exception as e:
        return jsonify({'error': f'Failed to fetch reports: {str(e)}'}), 500


@report_bp.route('/api/reports/download/<int:report_id>', methods=['GET'])
@login_required
def download_report(report_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'SELECT report_path, report_name FROM reports WHERE id = %s AND user_id = %s',
            (report_id, session['user_id'])
        )
        report = cursor.fetchone()
        cursor.close()
        conn.close()

        if not report:
            return jsonify({'error': 'Report not found'}), 404

        if not os.path.exists(report['report_path']):
            return jsonify({'error': 'Report file not found on server'}), 404

        return send_file(
            report['report_path'],
            as_attachment=True,
            download_name=report['report_name']
        ), 200

    except Exception as e:
        return jsonify({'error': f'Download failed: {str(e)}'}), 500
