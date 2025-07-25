#!/usr/bin/env python3
"""
Simple test to verify Flask can run
"""
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return '<h1>Flask is working!</h1>'

if __name__ == '__main__':
    print("Starting simple Flask test...")
    print("Visit: http://localhost:5002")
    app.run(host='127.0.0.1', port=5002, debug=False)