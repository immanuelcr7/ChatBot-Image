# Visual Intelligence Chatbot (Strict Offline Local AI)

A high-performance **Local Conversational Image Recognition System** designed for academic evaluation. This system operates **STRICTLY 100% OFFLINE** with **ZERO** external API calls.

## 🏗️ Strict Local AI Architecture

### 1. Object Detection (YOLOv8)
- Real-time detection of various objects and urban elements.
- Precise instance counting for all recognized categories.

### 2. Scene Description (BLIP-2)
- Local scene understanding using the BLIP model.
- Generates descriptive captions for environment and lighting.

### 3. Text Extraction (EasyOCR)
- Local character recognition for signboards, labels, and posters.

## 🔒 No Internet Required
- **Zero API Keys:** Gemini, OpenAI, and other cloud services are completely removed.
- **Privacy First:** All image data stays on your local RAM/CPU.
- **Academic Reliability:** Guaranteed to work without internet connection.

### Frontend (React + Vite)
- **Premium UI Design** with glassmorphism and gradients
- **Image Upload** with drag & drop support
- **Real-time Chat Interface** with conversation history
- **Vision Data Visualization** showing detected objects and confidence scores
- **Responsive Design** for all devices

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Gemini API key

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create `.env` file:**
   ```bash
   cp .env.example .env
   ```
   
4. **Add your Gemini API key to `.env`:**
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   ```

5. **Run the backend server:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

   Backend will be available at: `http://localhost:8000`
   API Documentation: `http://localhost:8000/docs`

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Run the development server:**
   ```bash
   npm run dev
   ```

   Frontend will be available at: `http://localhost:5173`

## 📋 Features

✅ **Multi-modal Input Processing**
- Image upload (drag & drop or file picker)
- Natural language queries
- Session continuity across conversations

✅ **Advanced Vision Analysis**
- Object detection with confidence scores
- Scene understanding
- OCR capabilities (extracting text from images)

✅ **Intelligent Conversation**
- Context-aware responses
- Follow-up question suggestions
- Safety guardrails for sensitive topics

✅ **Enterprise-Grade Architecture**
- Request validation & sanitization
- Error handling & logging
- Performance monitoring
- Scalable layer-based design

✅ **Premium User Experience**
- Modern, responsive UI
- Real-time feedback
- Smooth animations
- Dark mode optimized

## 🔧 API Endpoints

### `POST /api/chat`
Main chat endpoint for image analysis.

**Request:**
```
FormData:
- image: File (required)
- query: string (required)
- session_id: string (optional)
```

**Response:**
```json
{
  "session_id": "uuid",
  "response": {
    "text": "AI response",
    "follow_up_prompts": ["question1", "question2"]
  },
  "visual_summary": "Scene description",
  "vision_data": {
    "detected_objects": [...],
    "scene_context": "...",
    "confidence_scores": {...}
  },
  "latency": 1.23
}
```

### `GET /api/health`
Health check endpoint.

### `GET /api/metrics`
System monitoring metrics.

## 🎨 Design Philosophy

The UI follows modern web design principles:
- **Vibrant Gradients** for visual appeal
- **Glassmorphism** for depth
- **Micro-animations** for engagement
- **Dark Mode** optimized color palette
- **Responsive Layout** for all screen sizes

## 🔒 Safety Features

- **Medical Disclaimer:** No medical diagnosis
- **Legal Disclaimer:** No legal advice
- **Confidence-based Phrasing:** Clear uncertainty indicators
- **Input Sanitization:** XSS prevention
- **File Validation:** Size and type restrictions

## 📊 Project Structure

```
chat/
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   │   └── chat.py          # API endpoints (Layer 11)
│   │   ├── services/
│   │   │   ├── validation.py    # Layer 2
│   │   │   ├── vision.py        # Layers 3-5
│   │   │   ├── memory.py        # Layer 6
│   │   │   ├── llm.py           # Layers 7-10
│   │   │   └── monitoring.py    # Layer 12
│   │   └── main.py              # FastAPI app
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── App.jsx              # Main React component (Layer 1)
    │   ├── App.css              # Component styles
    │   ├── index.css            # Global design system
    │   └── main.jsx             # React entry point
    ├── index.html
    └── package.json
```

## 🛠️ Technology Stack

**Backend:**
- FastAPI - High-performance web framework
- Pillow - Image processing
- httpx - Async HTTP client for Gemini API
- python-dotenv - Environment management

**Frontend:**
- React 18 - UI library
- Vite - Build tool & dev server
- Modern CSS - Custom design system

**AI:**
- Google Gemini 2.0 Flash - LLM for conversational reasoning
