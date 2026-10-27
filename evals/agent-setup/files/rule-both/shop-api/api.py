# Demo material.
from flask import Flask
app = Flask(__name__)

@app.get('/v1/health')
def health():
    return {'ok': True}
