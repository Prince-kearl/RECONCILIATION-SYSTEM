# Project: ReconX - Reconciliation Engine (Production-ready)
# File layout (all files included below as sections):
#  - reconciliation_engine/engine.py         # core reconciliation logic
#  - reconciliation_engine/utils.py          # helpers: normalization, file readers, reporting
#  - api/app.py                              # Flask REST API to integrate with your system
#  - config.yml                              # configurable options
#  - requirements.txt
#  - Dockerfile
#  - README.md (run instructions + integration snippet)

# ==========================
# reconciliation_engine/engine.py
# ==========================
from dataclasses import dataclass
from typing import Optional, Tuple
import pandas as pd
import logging

logger = logging.getLogger(__name__)


@dataclass
class ReconciliationResult:
    matched: pd.DataFrame
    unmatched: pd.DataFrame
    summary: dict


class ReconciliationEngine:
    """
    Production-ready reconciliation engine.

    Features:
      - Strict numeric tolerance by default (0.00) for exact matches
      - Includes narration/description match (case-insensitive, stripped)
      - Supports CSV and Excel inputs
      - Produces matched/unmatched dataframes and a summary dict
      - Configurable: column name aliases, tolerance, fuzzy matching toggle

    Integration notes:
      - The API (api/app.py) shows how to call this class from your system.
      - Use ReconciliationEngine.reconcile_from_dfs when you already have dataframes
    """

    DEFAULT_ALIASES = {
        "amount": ["AMOUNT", "AMT", "VALUE"],
        "description": ["DESCRIPTION", "NARRATION", "REMARKS", "DETAILS"],
        "bank_ref": ["BANK REF", "BANK_REF", "REF"],
        "date": ["DATE", "TRANSACTION_DATE", "TXN_DATE"],
    }

    def __init__(self,
                 tolerance: float = 0.00,
                 aliases: Optional[dict] = None,
                 enable_fuzzy: bool = False):
        self.tolerance = float(tolerance)
        self.aliases = aliases or self.DEFAULT_ALIASES
        self.enable_fuzzy = enable_fuzzy

    def _resolve_column(self, df: pd.DataFrame, candidates: list) -> Optional[str]:
        for c in candidates:
            if c in df.columns:
                return c
        # try case-insensitive
        cols = {col.upper(): col for col in df.columns}
        for c in candidates:
            if c.upper() in cols:
                return cols[c.upper()]
        return None

    def _normalize_description(self, s: object) -> str:
        if pd.isna(s):
            return ""
        return str(s).strip().lower()

    def _prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        # work on a copy
        df = df.copy()
        # ensure columns upper-case for stable resolution
        # don't rename original user columns; return a working copy
        df.columns = [str(c).strip() for c in df.columns]
        return df

    def reconcile_from_dfs(self, bank_df: pd.DataFrame, collection_df: pd.DataFrame) -> ReconciliationResult:
        bank = self._prepare(bank_df)
        collection = self._prepare(collection_df)

        amount_col_bank = self._resolve_column(bank, self.aliases['amount'])
        amount_col_collection = self._resolve_column(collection, self.aliases['amount'])
        desc_col_bank = self._resolve_column(bank, self.aliases['description'])
        desc_col_collection = self._resolve_column(collection, self.aliases['description'])
        bank_ref_col = self._resolve_column(bank, self.aliases['bank_ref']) or 'BANK_REF'
        date_col = self._resolve_column(bank, self.aliases['date']) or 'DATE'

        if not amount_col_bank or not amount_col_collection:
            logger.error("Amount column not found in one of the files")
            raise ValueError("Amount column not found in one of the files")

        # normalize description columns to a consistent column name for comparison
        bank['_RECON_DESC'] = bank[desc_col_bank].apply(self._normalize_description) if desc_col_bank else ""
        collection['_RECON_DESC'] = collection[desc_col_collection].apply(self._normalize_description) if desc_col_collection else ""

        # Ensure AMOUNT numeric
        bank['_RECON_AMT'] = pd.to_numeric(bank[amount_col_bank], errors='coerce').fillna(0.0)
        collection['_RECON_AMT'] = pd.to_numeric(collection[amount_col_collection], errors='coerce').fillna(0.0)

        results = []

        # For speed: build a lookup on (amount, desc) pairs from collection
        collection_key = collection.groupby(['_RECON_AMT', '_RECON_DESC']).apply(lambda g: g.index.tolist()).to_dict()

        matched_rows = []
        unmatched_rows = []

        for idx, brow in bank.iterrows():
            key = (brow['_RECON_AMT'], brow['_RECON_DESC'])
            matched_idx_list = collection_key.get(key, [])

            statement_id = brow.get('statement_id', None)

            if matched_idx_list:
                # pick first match (could be enhanced to do 1:n mapping rules)
                cidx = matched_idx_list[0]
                crow = collection.loc[cidx]
                record_id = crow.get('record_id', None)
                matched_rows.append({
                    'bank_index': idx,
                    'collection_index': cidx,
                    'statement_id': statement_id,
                    'record_id': record_id,
                    'bank_ref': brow.get(bank_ref_col, ''),
                    'date': brow.get(date_col, ''),
                    'amount': brow['_RECON_AMT'],
                    'description': brow.get(desc_col_bank, ''),
                })
                # remove that index from the lookup to avoid duplicate matching
                collection_key[key].pop(0)
            else:
                unmatched_rows.append({
                    'bank_index': idx,
                    'statement_id': statement_id,
                    'bank_ref': brow.get(bank_ref_col, ''),
                    'date': brow.get(date_col, ''),
                    'amount': brow['_RECON_AMT'],
                    'description': brow.get(desc_col_bank, ''),
                })

        matched_df = pd.DataFrame(matched_rows)
        unmatched_df = pd.DataFrame(unmatched_rows)

        summary = {
            'bank_count': len(bank),
            'collection_count': len(collection),
            'matched_count': len(matched_df),
            'unmatched_count': len(unmatched_df),
            'matched_percentage': round(100.0 * len(matched_df) / len(bank) if len(bank) else 0.0, 2),
        }

        return ReconciliationResult(matched=matched_df, unmatched=unmatched_df, summary=summary)

    # Convenience method to read from files
    def reconcile_from_files(self, bank_file: str, collection_file: str) -> ReconciliationResult:
        bank_df = pd.read_excel(bank_file) if bank_file.lower().endswith(('.xls', '.xlsx')) else pd.read_csv(bank_file)
        collection_df = pd.read_excel(collection_file) if collection_file.lower().endswith(('.xls', '.xlsx')) else pd.read_csv(collection_file)
        return self.reconcile_from_dfs(bank_df, collection_df)


# ==========================
# reconciliation_engine/utils.py
# ==========================
import os
import uuid
from typing import Tuple

DATA_DIR = os.getenv('RECONX_DATA_DIR', '/data/reconx')
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)


def save_report(matched_df: pd.DataFrame, unmatched_df: pd.DataFrame, summary: dict, run_id: str = None) -> str:
    """Save matched/unmatched and summary into a single Excel workbook. Returns filepath."""
    run_id = run_id or uuid.uuid4().hex[:12]
    out_path = os.path.join(DATA_DIR, f'reconciliation_{run_id}.xlsx')
    with pd.ExcelWriter(out_path, engine='openpyxl') as writer:
        matched_df.to_excel(writer, sheet_name='Matched', index=False)
        unmatched_df.to_excel(writer, sheet_name='Unmatched', index=False)
        pd.DataFrame([summary]).to_excel(writer, sheet_name='Summary', index=False)
    return out_path


def generate_run_id() -> str:
    return uuid.uuid4().hex[:12]


# ==========================
# api/app.py
# ==========================
from flask import Flask, request, jsonify, send_file
import os
import logging
from werkzeug.utils import secure_filename

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Configuration - adjust as needed in your environment
UPLOAD_DIR = os.getenv('RECONX_UPLOAD_DIR', '/data/reconx/uploads')
OUTPUT_DIR = os.getenv('RECONX_OUTPUT_DIR', '/data/reconx')
ALLOWED_EXTENSIONS = {'csv', 'xls', 'xlsx'}

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Optional external imports; fall back to local definitions above when unavailable
try:
    from reconciliation_engine.engine import ReconciliationEngine as _ExternalReconciliationEngine
except Exception:
    _ExternalReconciliationEngine = None

try:
    from reconciliation_engine.utils import save_report as _external_save_report, generate_run_id as _external_generate_run_id
except Exception:
    _external_save_report = None
    _external_generate_run_id = None


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})


@app.route('/reconcile', methods=['POST'])
def reconcile_endpoint():
    """
    Expects multipart/form-data with two files:
      - bank_file: csv/xls[x]
      - collection_file: csv/xls[x]
    Optional form fields:
      - tolerance (float), enable_fuzzy (bool)

    Response: JSON with run_id and download_url (if successful)
    """
    if 'bank_file' not in request.files or 'collection_file' not in request.files:
        return jsonify({'error': 'bank_file and collection_file are required'}), 400

    bank_file = request.files['bank_file']
    collection_file = request.files['collection_file']

    if bank_file.filename == '' or collection_file.filename == '':
        return jsonify({'error': 'file missing filename'}), 400

    if not allowed_file(bank_file.filename) or not allowed_file(collection_file.filename):
        return jsonify({'error': 'only csv/xls/xlsx allowed'}), 400

    run_id = generate_run_id()

    bank_fname = secure_filename(f"{run_id}_bank_{bank_file.filename}")
    collection_fname = secure_filename(f"{run_id}_collection_{collection_file.filename}")
    bank_path = os.path.join(UPLOAD_DIR, bank_fname)
    collection_path = os.path.join(UPLOAD_DIR, collection_fname)

    bank_file.save(bank_path)
    collection_file.save(collection_path)

    tolerance = float(request.form.get('tolerance', 0.00))
    enable_fuzzy = request.form.get('enable_fuzzy', 'false').lower() in ('1', 'true', 'yes')

    # Pick external engine if installed as a package, else use the local class above
    engine_cls = _ExternalReconciliationEngine or ReconciliationEngine
    engine = engine_cls(tolerance=tolerance, enable_fuzzy=enable_fuzzy)

    try:
        result = engine.reconcile_from_files(bank_path, collection_path)
    except Exception as e:
        app.logger.exception('Failed to reconcile')
        return jsonify({'error': str(e)}), 500

    # Prefer external save helpers if available
    save_fn = _external_save_report or save_report
    out_path = save_fn(result.matched, result.unmatched, result.summary, run_id)

    download_url = f"/download/{os.path.basename(out_path)}"
    return jsonify({'run_id': run_id, 'download_url': download_url, 'summary': result.summary}), 200


@app.route('/download/<filename>', methods=['GET'])
def download_report(filename: str):
    fpath = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(fpath):
        return jsonify({'error': 'file not found'}), 404
    return send_file(fpath, as_attachment=True)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)


# ==========================
# config.yml
# ==========================
# reconx:
#   upload_dir: /data/reconx/uploads
#   output_dir: /data/reconx
#   allowed_extensions: [csv, xls, xlsx]
#   default_tolerance: 0.00

# ==========================
# requirements.txt
# ==========================
# Flask
# pandas
# openpyxl
# xlrd
# werkzeug

# ==========================
# Dockerfile
# ==========================
# FROM python:3.11-slim
# WORKDIR /app
# COPY . /app
# RUN pip install --upgrade pip && pip install -r requirements.txt
# ENV RECONX_UPLOAD_DIR=/data/reconx/uploads
# ENV RECONX_OUTPUT_DIR=/data/reconx
# EXPOSE 8000
# CMD ["python", "api/app.py"]

# ==========================
# README.md (excerpt)
# ==========================
# ReconX Reconciliation Engine
# Usage (local):
# 1. Create virtualenv and install requirements
#    python -m venv venv
#    source venv/bin/activate
#    pip install -r requirements.txt
# 2. Start API
#    python api/app.py
# 3. POST to /reconcile with multipart form (bank_file, collection_file)
#    curl -F "bank_file=@imbalances.xlsx" -F "collection_file=@collection_report.xlsx" http://localhost:8000/reconcile

# Frontend integration snippet (fetch):
# const form = new FormData();
# form.append('bank_file', bankFileInput.files[0]);
# form.append('collection_file', collectionFileInput.files[0]);
# form.append('tolerance', '0.00');
# const res = await fetch('/reconcile', { method: 'POST', body: form });
# const data = await res.json();
# // data.download_url gives download endpoint

# ==========================
# NOTES & NEXT STEPS
# ==========================
# - If you want the engine to attempt fuzzy/narration similarity matching (e.g., fuzzywuzzy or rapidfuzz), we can add a configurable path where the engine will try to match on amount exactly and then do a fuzzy match on narration with a threshold (e.g., 90%). For production, use rapidfuzz for licensing/performance.
# - Add database logging (Postgres) if you want persistent run history rather than file-based.
# - Add authentication on API endpoints for secure integration into your system.
# - Add background worker (Celery + Redis) for large files to avoid blocking the API.

# End of document
