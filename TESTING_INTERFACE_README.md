# Residencias Chable - AI Handler Testing Interface

## Overview

This testing interface provides a comprehensive way to test and debug the Residencias Chable AI handler while configuring the Twilio agent. It includes a web-based chat widget, function testing tools, and configuration management.

## Features

### 🚀 **Chat Widget Testing**
- Real-time chat interface to test AI responses
- Message history and export functionality
- Typing indicators and conversation management
- Integration with the web widget message endpoint

### 🔧 **AI Functions Testing**
- **Search Properties**: Test property search functionality
- **Send Photo**: Test photo sending with categories
- **Capture Customer Info**: Test lead capture forms
- **Send Brochure**: Test brochure delivery system

### 🗄️ **Vector Store Testing**
- Test vector store queries and responses
- View search results with similarity scores
- Simulate property database searches

### ⚙️ **Configuration Management**
- AI model selection (fast/balanced/powerful)
- Token limits and temperature settings
- Store ID management
- Settings persistence

### 📊 **System Monitoring**
- Real-time logging system
- Conversation history tracking
- Error reporting and debugging

## Getting Started

### 1. Start the Application

```bash
# Navigate to your project directory
cd ResidenciasChable

# Install dependencies (if not already done)
pip install -r requirements.txt

# Start the FastAPI server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Access the Testing Interface

Open your browser and navigate to:
```
http://localhost:8000
```

You should see the Residencias Chable testing interface with a modern, professional design.

### 3. Test the Chat Widget

1. **Navigate to Chat Widget**: Click on "Chat Widget" in the sidebar
2. **Send a Message**: Type a message in the input field and press Enter
3. **View Response**: The AI handler will process your message and respond
4. **Clear Chat**: Use the "Limpiar Chat" button to start fresh
5. **Export Chat**: Download conversation history as JSON

### 4. Test AI Functions

1. **Navigate to AI Functions**: Click on "AI Functions" in the sidebar
2. **Select Function**: Choose from the available function cards
3. **Fill Parameters**: Enter required information for each function
4. **Test Function**: Click "Test Function" to simulate execution
5. **View Results**: Check the logs for function execution results

### 5. Test Vector Store

1. **Navigate to Vector Store**: Click on "Vector Store" in the sidebar
2. **Enter Query**: Type a search query (e.g., "apartamento en Playa del Carmen")
3. **Execute Search**: Click "Search" to test the vector store
4. **View Results**: See simulated property search results

### 6. Configure Settings

1. **Navigate to Settings**: Click on "Settings" in the sidebar
2. **Adjust Parameters**: Modify AI model settings, token limits, etc.
3. **Save Settings**: Click "Save Settings" to persist changes
4. **Reset to Default**: Use "Reset to Default" if needed

## API Endpoints

### Web Widget Message
```
POST /web-widget/message
```
Processes messages from the web interface for testing.

**Request Body:**
```json
{
    "Body": "Your message here",
    "From": "web_visitor_id",
    "To": "web-widget",
    "Platform": "web"
}
```

**Response:**
```json
{
    "success": true,
    "response": "AI response here",
    "thread_id": "thread_identifier"
}
```

### WhatsApp Webhook
```
POST /message
```
Processes incoming WhatsApp messages (Twilio webhook).

## File Structure

```
app/
├── static/
│   ├── index.html          # Main testing interface
│   ├── css/
│   │   └── styles.css      # Interface styling
│   ├── js/
│   │   └── app.js          # Frontend functionality
│   └── images/             # Image assets
├── main.py                 # FastAPI application
├── single_ai_handler.py    # AI handler implementation
└── ...
```

## Testing Scenarios

### 1. **Basic Conversation Flow**
- Send greetings and questions
- Test Spanish and English responses
- Verify conversation continuity

### 2. **Property Search Testing**
- Test natural language queries
- Verify search result formatting
- Test different property categories

### 3. **Function Execution**
- Test each AI function individually
- Verify parameter validation
- Check error handling

### 4. **Vector Store Integration**
- Test search queries
- Verify result relevance
- Test different query types

### 5. **Error Handling**
- Test invalid inputs
- Verify error messages
- Check system stability

## Troubleshooting

### Common Issues

1. **Interface Not Loading**
   - Check if the server is running on port 8000
   - Verify static files are in the correct location
   - Check browser console for JavaScript errors

2. **Chat Not Working**
   - Verify the `/web-widget/message` endpoint is accessible
   - Check server logs for errors
   - Ensure the AI handler is properly initialized

3. **Functions Not Testing**
   - Check browser console for JavaScript errors
   - Verify function parameters are correctly filled
   - Check the logs section for error messages

4. **Settings Not Saving**
   - Check browser localStorage support
   - Verify form validation
   - Check for JavaScript errors

### Debug Mode

Enable debug logging by checking the browser console and the logs section in the interface. All API calls and function executions are logged for debugging purposes.

## Integration with Twilio

While testing the interface, you can simultaneously configure your Twilio agent:

1. **Set up Twilio webhook** to point to `/message`
2. **Test webhook delivery** using the interface
3. **Monitor conversations** in real-time
4. **Debug AI responses** before going live

## Next Steps

After testing and configuring:

1. **Deploy to production** with proper environment variables
2. **Configure Twilio** with production webhook URLs
3. **Set up monitoring** and logging
4. **Test with real users** in a staging environment

## Support

For issues or questions:
- Check the logs section in the interface
- Review server console output
- Verify configuration settings
- Check API endpoint accessibility

---

**Note**: This testing interface is designed for development and testing purposes. Ensure proper security measures are in place before deploying to production.
