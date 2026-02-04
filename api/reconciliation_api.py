"""Deprecated duplicate API.

This module used to provide a standalone reconciliation API. The main application
now provides these endpoints in `app.py`. Keeping this file to avoid import errors,
but it should not be used going forward.
"""

from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'deprecated',
        'message': 'Use main app.py endpoints',
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
