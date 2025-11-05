#!/usr/bin/env python3
"""
AILO Web Interface
A web-based chat interface for the AI-powered Learning Oracle
"""

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import asyncio
import secrets
from datetime import datetime
from pathlib import Path
import json
import logging

# Import AILO chatbot
from ailo_chatbot import AILOChatbot

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
CORS(app)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('AILO-Web')

# Global AILO instance (shared across sessions)
ailo = None
ailo_ready = False


def get_or_create_ailo():
    """Get or create the global AILO instance."""
    global ailo, ailo_ready
    
    if ailo is None:
        logger.info("Initializing AILO chatbot...")
        ailo = AILOChatbot()
        
        # Load knowledge base
        logger.info("Loading knowledge base...")
        ailo.load_knowledge_base()
        
        if not ailo.knowledge_base:
            logger.error("Failed to load knowledge base!")
            ailo_ready = False
            return None
        
        logger.info(f"✓ AILO ready with {len(ailo.knowledge_base)} documents")
        ailo_ready = True
    
    return ailo


@app.route('/')
def index():
    """Main chat interface page."""
    # Initialize session if needed
    if 'session_id' not in session:
        session['session_id'] = secrets.token_hex(16)
        session['created_at'] = datetime.now().isoformat()
    
    return render_template('index.html')


@app.route('/api/status', methods=['GET'])
def status():
    """Check if AILO is ready."""
    global ailo_ready, ailo
    
    if not ailo_ready:
        get_or_create_ailo()
    
    return jsonify({
        'ready': ailo_ready,
        'knowledge_base_size': len(ailo.knowledge_base) if ailo else 0,
        'session_id': session.get('session_id', 'unknown')
    })


@app.route('/api/chat', methods=['POST'])
async def chat():
    """Handle chat messages."""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({
                'error': 'Empty message'
            }), 400
        
        # Get AILO instance
        ailo_instance = get_or_create_ailo()
        if not ailo_instance:
            return jsonify({
                'error': 'AILO is not ready. Please ensure the knowledge base is loaded.',
                'suggestion': 'Run: python main.py'
            }), 503
        
        # Get response from AILO
        logger.info(f"Processing message: {user_message[:50]}...")
        response = await ailo_instance.chat(user_message)
        
        return jsonify({
            'response': response,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in chat: {e}", exc_info=True)
        return jsonify({
            'error': f'An error occurred: {str(e)}'
        }), 500


@app.route('/api/clear', methods=['POST'])
def clear_conversation():
    """Clear conversation history."""
    try:
        ailo_instance = get_or_create_ailo()
        if ailo_instance:
            ailo_instance.clear_conversation()
            return jsonify({
                'success': True,
                'message': 'Conversation history cleared'
            })
        else:
            return jsonify({
                'error': 'AILO not initialized'
            }), 503
            
    except Exception as e:
        logger.error(f"Error clearing conversation: {e}")
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/api/save', methods=['POST'])
def save_conversation():
    """Save conversation to file."""
    try:
        ailo_instance = get_or_create_ailo()
        if not ailo_instance:
            return jsonify({
                'error': 'AILO not initialized'
            }), 503
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = session.get('session_id', 'unknown')
        filename = f"ailo_web_conversation_{session_id}_{timestamp}.json"
        
        ailo_instance.save_conversation(filename)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'message': f'Conversation saved to {filename}'
        })
        
    except Exception as e:
        logger.error(f"Error saving conversation: {e}")
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get statistics about the current session."""
    try:
        ailo_instance = get_or_create_ailo()
        if not ailo_instance:
            return jsonify({
                'error': 'AILO not initialized'
            }), 503
        
        return jsonify({
            'knowledge_base_size': len(ailo_instance.knowledge_base),
            'conversation_length': len(ailo_instance.conversation_history),
            'session_id': session.get('session_id', 'unknown'),
            'session_created': session.get('created_at', 'unknown'),
            'indexed_categories': {
                category: len(docs) 
                for category, docs in ailo_instance.indexed_data.items()
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({
            'error': str(e)
        }), 500


def run_async_chat(user_message):
    """Helper to run async chat in sync context."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(ailo.chat(user_message))
    finally:
        loop.close()


if __name__ == '__main__':
    # Initialize AILO on startup
    logger.info("=" * 80)
    logger.info("Starting AILO Web Interface")
    logger.info("=" * 80)
    
    # Pre-load AILO
    get_or_create_ailo()
    
    if ailo_ready:
        logger.info("\n✓ AILO is ready!")
        logger.info("Starting web server on http://localhost:8080")
        logger.info("=" * 80)
        
        # Run Flask app
        app.run(
            host='0.0.0.0',
            port=8080,
            debug=False,  # Set to False in production
            threaded=True
        )
    else:
        logger.error("\n✗ Failed to initialize AILO")
        logger.error("Please ensure the knowledge base is available")
        logger.error("Run: python main.py")
