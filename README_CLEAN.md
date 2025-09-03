# 🏠 Residencias Chable - Clean Multi-Channel AI System

## 🎯 Overview

This is a **clean, simplified version** of the Residencias Chable AI system that has been migrated from the old OpenAI Assistant API to a modern **single AI handler** approach.

## ✨ What's New

### ✅ **Single AI Handler** (`single_ai_handler.py`)
- **One file** manages all AI functionality
- **Prompt creation** with dynamic system messages
- **Model selection** (fast/balanced/powerful)
- **Function editing** and management
- **Vector store integration** with store ID

### ✅ **Multi-Channel Support**
- **WhatsApp** - Full messaging with media support
- **Voice** - Audio transcription and processing
- **Web Widget** - Chat interface for websites
- **All channels** use the same AI handler

### ✅ **Clean Architecture**
- **Removed** old assistant-based complexity
- **Simplified** codebase structure
- **Maintained** all business functionality
- **Better** performance and maintainability

## 🗂️ File Structure

```
├── single_ai_handler.py          # 🧠 Single AI handler (NEW)
├── app/
│   ├── main.py                   # 🚀 Main FastAPI app (CLEANED)
│   ├── models.py                 # 📊 Database models
│   ├── db.py                     # 🗄️ Database connection
│   ├── routes.py                 # 🛣️ API routes
│   ├── utils.py                  # 🛠️ Utility functions
│   └── execute_functions.py      # ⚡ Business logic functions
├── requirements.txt              # 📦 Dependencies (CLEANED)
└── README_CLEAN.md              # 📖 This file
```

## 🚀 Getting Started

### 1. **Set Environment Variables**
```bash
OPENAI_API_KEY=your_openai_api_key
STORE_ID=your_vector_store_id
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_WHATSAPP_NUMBER=your_whatsapp_number
```

### 2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 3. **Run the Application**
```bash
python -m app.main
```

Or with uvicorn:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 🔧 How It Works

### **Single AI Handler**
```python
from single_ai_handler import SingleAIHandler

# Initialize with your store ID
handler = SingleAIHandler("your_store_id")

# Process messages
response = await handler.process_message(
    "Busco un apartamento en Playa del Carmen",
    model_speed="balanced"
)

# Edit functions dynamically
handler.edit_function("search_properties", new_description="Enhanced search")

# Add new functions
handler.add_function("new_function", "description", parameters)
```

### **Multi-Channel Processing**
1. **WhatsApp**: `/message` endpoint processes Twilio webhooks
2. **Voice**: Audio transcription → text → AI processing
3. **Web**: `/web-widget/message` handles website chat
4. **All channels** use the same `SingleAIHandler`

## 🎨 Features

### **AI Capabilities**
- **Dynamic prompts** with store ID context
- **Model selection** (speed vs. power)
- **Function calling** with OpenAI
- **Vector store integration**
- **Conversation history**

### **Business Functions**
- **Property search** and recommendations
- **Photo sending** and media handling
- **Customer info capture**
- **Lead qualification**
- **Brochure distribution**

### **Multi-Channel Support**
- **WhatsApp Business API**
- **Voice message transcription**
- **Web widget integration**
- **Unified conversation tracking**

## 🔄 Migration Benefits

### **Before (Old System)**
- ❌ Complex assistant API management
- ❌ Thread and run handling
- ❌ Multiple handler files
- ❌ Slower response times
- ❌ Harder to maintain

### **After (New System)**
- ✅ **Single file** AI management
- ✅ **Direct function calling**
- ✅ **Cleaner codebase**
- ✅ **Faster responses**
- ✅ **Easier maintenance**

## 🧪 Testing

### **Test the AI Handler**
```python
# Test basic functionality
response = await handler.process_message("Hello, how are you?")
print(response)

# Test function editing
success = handler.edit_function("search_properties", new_description="Updated search")
print(f"Function updated: {success}")

# Test vector store
results = handler.call_vector_store("apartamento en Playa del Carmen")
print(f"Found {len(results)} properties")
```

### **Test Multi-Channel**
1. **WhatsApp**: Send message to your Twilio number
2. **Web Widget**: Use the `/web-widget/message` endpoint
3. **Voice**: Send voice note via WhatsApp

## 🚨 Troubleshooting

### **Common Issues**
1. **Import Error**: Make sure `single_ai_handler.py` is in the root directory
2. **Store ID**: Set `STORE_ID` environment variable
3. **OpenAI Key**: Verify your API key is valid
4. **Dependencies**: Run `pip install -r requirements.txt`

### **Debug Mode**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🔮 Future Enhancements

- **Advanced vector store** integration
- **Multi-language** support
- **Analytics dashboard**
- **CRM integration**
- **Mobile app**

## 📚 Support

For questions or issues:
1. Check the environment variables
2. Verify the file structure
3. Check the logs for errors
4. Test the AI handler independently

---

**🎉 Congratulations!** You now have a clean, modern AI system that's easier to maintain and extend.
