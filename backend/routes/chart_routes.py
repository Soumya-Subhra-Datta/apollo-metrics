import pandas as pd
from flask import Blueprint, request, jsonify, session
from backend.database.db import get_db_connection
from backend.utils.helpers import login_required
from backend.services.chart_service import generate_chart_data

chart_bp = Blueprint('charts', __name__)


@chart_bp.route('/api/charts/generate', methods=['POST'])
@login_required
def generate_chart():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    upload_id = data.get('upload_id')
    chart_type = data.get('chart_type', '').lower()
    x_column = data.get('x_column')
    y_column = data.get('y_column')

    if not upload_id or not chart_type:
        return jsonify({'error': 'upload_id and chart_type are required'}), 400

    valid_charts = ['bar', 'line', 'pie', 'histogram', 'scatter', 'box', 'heatmap']
    if chart_type not in valid_charts:
        return jsonify({'error': f'Unsupported chart type. Supported types: {", ".join(valid_charts)}'}), 400

    if not x_column:
        return jsonify({'error': 'X-axis column is required'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            'SELECT file_path FROM uploads WHERE id = %s AND user_id = %s',
            (upload_id, session['user_id'])
        )
        upload = cursor.fetchone()
        cursor.close()
        conn.close()

        if not upload:
            return jsonify({'error': 'Upload not found'}), 404

        df = pd.read_csv(upload['file_path'])

        if x_column not in df.columns:
            return jsonify({'error': f'Column "{x_column}" not found in dataset'}), 400

        if y_column and y_column not in df.columns:
            return jsonify({'error': f'Column "{y_column}" not found in dataset'}), 400

        chart_data = generate_chart_data(df, chart_type, x_column, y_column)

        if chart_data is None:
            return jsonify({'error': f'Could not generate {chart_type} chart with the selected columns. Try different columns or chart type.'}), 400

        return jsonify({
            'chart_type': chart_type,
            'chart_data': chart_data
        }), 200

    except Exception as e:
        return jsonify({'error': f'Chart generation failed: {str(e)}'}), 500
