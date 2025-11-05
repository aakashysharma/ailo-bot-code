# 🔮 AILO Web Interface

A modern, browser-based chat interface for AILO (AI-powered Learning Oracle).

## 🎯 Features

- **Modern Chat UI**: Clean, responsive design that works on desktop and mobile
- **Real-time Responses**: Async message handling with typing indicators
- **Session Management**: Each browser session maintains its own conversation history
- **Statistics Dashboard**: View knowledge base stats and chat history
- **Save Conversations**: Export your chat history to text files
- **Status Monitoring**: Live status updates showing AILO's readiness

## 🚀 Quick Start

### 1. Prerequisites

Make sure you have:
- ✅ LM Studio running with Gemma model loaded
- ✅ Python dependencies installed (see `requirements.txt`)
- ✅ AILO knowledge base files in `utdanning_data/processed/`

### 2. Start the Web Server

```bash
python start_ailo_web.py
```

Or run directly:

```bash
python ailo_web.py
```

### 3. Open in Browser

Navigate to:
- http://localhost:8080
- http://127.0.0.1:8080

⏱️ **First Launch**: AILO will take 1-2 minutes to load 33,873 documents into memory. The status banner will show when it's ready.

## 📁 Project Structure

```
ailo-bot-code/
├── ailo_web.py              # Flask web server (backend)
├── start_ailo_web.py        # Launcher script
├── templates/
│   └── index.html           # Main web page template
├── static/
│   ├── style.css            # Styling
│   └── script.js            # Frontend logic
└── exports/
    └── conversations/       # Saved chat logs (auto-created)
```

## 🎨 User Interface

### Main Components

1. **Header**
   - AILO branding and title
   - Action buttons: Statistics, Clear, Save

2. **Status Banner**
   - ⏳ Loading: AILO is initializing
   - ✅ Ready: System ready to chat
   - ❌ Error: Connection or loading issues

3. **Chat Area**
   - Welcome message with usage guide
   - User messages (blue, right-aligned)
   - Assistant responses (gray, left-aligned)
   - System messages (centered, info style)

4. **Input Area**
   - Text input with auto-resize
   - Send button (disabled when not ready)
   - Keyboard shortcuts:
     - `Enter`: Send message
     - `Shift+Enter`: New line

### Actions

- **💬 Chat**: Ask questions about education and careers
- **📊 Statistics**: View document count, model info, and chat history
- **🗑️ Clear**: Reset conversation history (with confirmation)
- **💾 Save**: Export current conversation to timestamped file

## 🔧 API Endpoints

The Flask backend provides these REST endpoints:

### GET `/`
Returns the main HTML page

### GET `/api/status`
Check if AILO is ready
```json
{
  "ready": true,
  "documents": 33873
}
```

### POST `/api/chat`
Send a message and get response
```json
Request:
{
  "message": "Hva kan du fortelle meg om datautdanning?"
}

Response:
{
  "success": true,
  "response": "AILO's response here..."
}
```

### POST `/api/clear`
Clear conversation history
```json
{
  "success": true
}
```

### POST `/api/save`
Save conversation to file
```json
{
  "success": true,
  "filename": "conversation_20250131_143022.txt"
}
```

### GET `/api/stats`
Get system statistics
```json
{
  "success": true,
  "stats": {
    "total_documents": 33873,
    "messages_in_history": 12,
    "total_chunks": 33873,
    "model": "gemma-3n-E4B-it-MLX-bf16",
    "temperature": 0.3,
    "top_k": 10
  }
}
```

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Check what's using port 8080
lsof -i :8080

# Kill the process or change port in ailo_web.py
```

### AILO Won't Load

1. Check LM Studio is running
2. Verify data files exist in `utdanning_data/processed/`
3. Check terminal logs for error messages
4. Ensure sufficient RAM (model needs ~8GB)

### Connection Errors

1. Verify Flask is running (check terminal)
2. Try http://127.0.0.1:5000 instead of localhost
3. Check firewall settings
4. Look for CORS errors in browser console

### Slow Responses

1. First message always takes longer (model initialization)
2. Reduce `top_k` in ailo_chatbot.py for faster retrieval
3. Check LM Studio GPU acceleration settings
4. Monitor system resources (RAM, CPU)

## 📝 Session Management

- Each browser tab/window gets a unique session ID
- Chat history is maintained per session
- Sessions persist until:
  - Browser is closed
  - Cache is cleared
  - "Clear" button is clicked
  - Server restarts

## 💾 Saved Conversations

Files are saved to: `exports/conversations/`

Format: `conversation_YYYYMMDD_HHMMSS.txt`

## 🎨 Customization

### Styling

Edit `static/style.css` to customize:
- Color scheme (CSS variables in `:root`)
- Layout and spacing
- Animations and transitions
- Responsive breakpoints

### Frontend Behavior

Edit `static/script.js` to modify:
- Message formatting
- API call handling
- UI interactions
- Auto-scroll behavior

### Backend

Edit `ailo_web.py` to change:
- Port and host settings
- Session management
- Error handling
- Logging configuration

## 🚀 Production Deployment

For production use, consider:

1. **Use a Production WSGI Server**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 ailo_web:app
   ```

2. **Enable HTTPS**
   - Use nginx or Apache as reverse proxy
   - Add SSL certificates

3. **Environment Variables**
   - Store secrets in .env file
   - Use proper secret key for sessions

4. **Logging**
   - Configure production logging
   - Monitor error logs

5. **Performance**
   - Enable caching where appropriate
   - Use CDN for static assets
   - Monitor resource usage

## 📄 License

Same license as the AILO project.

## 🤝 Contributing

To contribute improvements to the web interface:

1. Test changes locally
2. Ensure responsive design works on mobile
3. Maintain accessibility standards
4. Update this README with new features
5. Check browser console for errors

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section
2. Review browser console logs
3. Check Flask terminal output
4. Verify LM Studio connection

---

Made with ❤️ for Norwegian education and career guidance
