import os
import pandas as pd
from flask import Blueprint, request, jsonify, session
from werkzeug.utils import secure_filename
from backend.database.db import get_db_connection
from backend.utils.helpers import login_required, allowed_file, generate_unique_filename
from backend.config import Config

upload_bp = Blueprint('upload', __name__)


@upload_bp.route('/api/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only CSV and Excel (.xls, .xlsx) files are allowed.'}), 400

    try:
        config = Config()
        original_filename = secure_filename(file.filename)
        unique_filename = generate_unique_filename(original_filename)
        file_path = os.path.join(config.UPLOAD_FOLDER, unique_filename)
        file.save(file_path)

        ext = original_filename.rsplit('.', 1)[1].lower()
        if ext == 'csv':
            df = pd.read_csv(file_path)
        elif ext in ('xls', 'xlsx'):
            try:
                df = pd.read_excel(file_path)
            except (ImportError, ValueError) as e:
                os.remove(file_path)
                return jsonify({'error': f'Excel support requires openpyxl/xlrd: {e}'}), 400
            csv_path = file_path.rsplit('.', 1)[0] + '.csv'
            try:
                df.to_csv(csv_path, index=False)
                os.remove(file_path)
                file_path = csv_path
            except Exception:
                for p in [file_path, csv_path]:
                    if os.path.exists(p):
                        os.remove(p)
                return jsonify({'error': 'Failed to convert Excel file to CSV.'}), 400

        if df.empty:
            os.remove(file_path)
            return jsonify({'error': 'The uploaded file is empty.'}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            'INSERT INTO uploads (user_id, file_name, file_path, total_rows, total_columns) VALUES (%s, %s, %s, %s, %s)',
            (session['user_id'], original_filename, file_path, int(len(df)), int(len(df.columns)))
        )
        conn.commit()
        upload_id = cursor.lastrowid

        columns_info = []
        for col in df.columns:
            columns_info.append({
                'name': col,
                'dtype': str(df[col].dtype),
                'missing': int(df[col].isnull().sum()),
                'unique': int(df[col].nunique())
            })

        cursor.close()
        conn.close()

        return jsonify({
            'message': 'File uploaded successfully',
            'upload_id': upload_id,
            'file_name': original_filename,
            'total_rows': int(len(df)),
            'total_columns': int(len(df.columns)),
            'columns': columns_info,
            'preview': df.head(10).to_dict(orient='records')
        }), 201

    except pd.errors.EmptyDataError:
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'error': 'The uploaded file is empty or corrupt.'}), 400
    except pd.errors.ParserError:
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'error': 'Could not parse the file. Please check its format.'}), 400
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


@upload_bp.route('/api/uploads', methods=['GET'])
@login_required
def get_uploads():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'SELECT id, file_name, total_rows, total_columns, uploaded_at FROM uploads WHERE user_id = %s ORDER BY uploaded_at DESC',
            (session['user_id'],)
        )
        uploads = cursor.fetchall()
        cursor.close()
        conn.close()

        for u in uploads:
            u['uploaded_at'] = u['uploaded_at'].strftime('%Y-%m-%d %H:%M:%S') if u.get('uploaded_at') else None

        return jsonify({'uploads': uploads}), 200

    except Exception as e:
        return jsonify({'error': f'Failed to fetch uploads: {str(e)}'}), 500


@upload_bp.route('/api/uploads/<int:upload_id>', methods=['GET'])
@login_required
def get_upload(upload_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            'SELECT id, file_name, file_path, total_rows, total_columns, uploaded_at FROM uploads WHERE id = %s AND user_id = %s',
            (upload_id, session['user_id'])
        )
        upload = cursor.fetchone()
        cursor.close()
        conn.close()

        if not upload:
            return jsonify({'error': 'Upload not found'}), 404

        df = pd.read_csv(upload['file_path'])

        columns_info = []
        for col in df.columns:
            columns_info.append({
                'name': col,
                'dtype': str(df[col].dtype),
                'missing': int(df[col].isnull().sum()),
                'unique': int(df[col].nunique()),
                'sample_values': df[col].dropna().head(3).tolist()
            })

        upload['uploaded_at'] = upload['uploaded_at'].strftime('%Y-%m-%d %H:%M:%S') if upload.get('uploaded_at') else None

        return jsonify({
            'upload': upload,
            'columns': columns_info,
            'preview': df.head(10).to_dict(orient='records')
        }), 200

    except Exception as e:
        return jsonify({'error': f'Failed to fetch upload details: {str(e)}'}), 500


@upload_bp.route('/api/uploads/<int:upload_id>', methods=['DELETE'])
@login_required
def delete_upload(upload_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            'SELECT file_path FROM uploads WHERE id = %s AND user_id = %s',
            (upload_id, session['user_id'])
        )
        upload = cursor.fetchone()

        if not upload:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Upload not found'}), 404

        import os
        if os.path.exists(upload['file_path']):
            os.remove(upload['file_path'])

        cursor.execute('DELETE FROM reports WHERE upload_id = %s AND user_id = %s', (upload_id, session['user_id']))
        cursor.execute('DELETE FROM model_results WHERE upload_id = %s AND user_id = %s', (upload_id, session['user_id']))
        cursor.execute('DELETE FROM user_queries WHERE upload_id = %s AND user_id = %s', (upload_id, session['user_id']))
        cursor.execute('DELETE FROM analysis_history WHERE upload_id = %s AND user_id = %s', (upload_id, session['user_id']))
        cursor.execute('DELETE FROM uploads WHERE id = %s AND user_id = %s', (upload_id, session['user_id']))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({'message': 'Dataset and all related data deleted successfully'}), 200

    except Exception as e:
        return jsonify({'error': f'Failed to delete upload: {str(e)}'}), 500
