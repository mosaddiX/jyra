#!/usr/bin/env python
"""
Web server for Jyra deployment.
This keeps the application alive on hosting platforms.
"""

import os
import threading
import time
from flask import Flask

# Create a Flask app for the web server
app = Flask(__name__)

@app.route('/')
def home():
    return """
    <html>
    <head>
        <title>Jyra AI Companion</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                line-height: 1.6;
                color: #333;
            }
            h1 {
                color: #2c3e50;
                border-bottom: 2px solid #3498db;
                padding-bottom: 10px;
            }
            .container {
                background-color: #f9f9f9;
                border-radius: 5px;
                padding: 20px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            .status {
                background-color: #e8f5e9;
                border-left: 4px solid #4caf50;
                padding: 10px;
                margin: 20px 0;
            }
            a {
                color: #3498db;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Jyra AI Companion</h1>
            <p>The soul that remembers you</p>
            
            <div class="status">
                <strong>Status:</strong> Online and running
            </div>
            
            <h2>About Jyra</h2>
            <p>Jyra is an emotionally intelligent AI companion designed to engage users in conversations while adopting various personas.</p>
            
            <h2>Features</h2>
            <ul>
                <li>Role Management System</li>
                <li>Memory System</li>
                <li>Sentiment Analysis</li>
                <li>Multi-modal Support</li>
                <li>Community Engagement</li>
            </ul>
            
            <p>To interact with Jyra, find the bot on Telegram.</p>
        </div>
    </body>
    </html>
    """

@app.route('/health')
def health():
    return "OK"

def run_flask():
    """Run the Flask web server."""
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    run_flask()
