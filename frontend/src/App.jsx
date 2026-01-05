import React, { useState, useRef, useEffect } from 'react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [image, setImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [settings, setSettings] = useState({
    depth: 'standard',
    safetyMode: true
  });
  const [visualStory, setVisualStory] = useState({
    title: "Start your story...",
    context: "Upload an image to begin the exploration.",
    mood: "Waiting...",
    details: []
  });

  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImage(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSend = async (overrideQuery = null) => {
    const queryToSend = overrideQuery || input;
    if ((!queryToSend.trim() && !image) || isLoading) return;

    const currentInput = queryToSend;
    const currentImage = image;
    const currentPreview = imagePreview;

    setInput('');
    // We keep the image in the state for the focus lock mechanism

    // Add User Bubble
    const userMsg = {
      role: 'user',
      content: currentInput || "Tell me about this image",
      image: currentImage ? currentPreview : null
    };
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const formData = new FormData();
      formData.append('query', currentInput || "Tell me about this image");
      if (currentImage) formData.append('image', currentImage);
      if (sessionId) formData.append('session_id', sessionId);
      formData.append('depth', settings.depth);
      formData.append('safety_mode', settings.safetyMode);

      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      setSessionId(data.session_id);

      // Update the "Visual Story Panel" based on summary or metadata
      if (data.visual_summary) {
        setVisualStory({
          title: "Scene Insights",
          context: data.visual_summary,
          mood: "Analyzed",
          details: data.vision_metadata ? Object.keys(data.vision_metadata.detected_objects).filter(k => k !== 'others').map(k => `${data.vision_metadata.detected_objects[k]} ${k}s`) : []
        });
      }

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.response.text,
        suggestions: data.response.smart_suggestions
      }]);

      // If we uploaded an image, we clear the local upload state but keep the preview for context
      // The Focus Lock is maintained on the server/memory
      if (currentImage) {
        setImage(null);
      }

    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: "I lost my connection to the visual engine. Please check if I'm still online."
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container bg-gradient">
      <header className="app-header glass-effect">
        <div className="logo-section">
          <div className="brand-icon">✨</div>
          <h1 className="app-title">Visionary AI</h1>
        </div>

        <div className="header-controls">
          <div className="control-group">
            <span className="control-label">Safety</span>
            <button
              className={`toggle ${settings.safetyMode ? 'active' : ''}`}
              onClick={() => setSettings(s => ({ ...s, safetyMode: !s.safetyMode }))}
            >
              {settings.safetyMode ? 'ON' : 'OFF'}
            </button>
          </div>
          <div className="control-divider"></div>
          <div className="control-group">
            <span className="control-label">Mode</span>
            <select
              value={settings.depth}
              onChange={(e) => setSettings(s => ({ ...s, depth: e.target.value }))}
              className="depth-select"
            >
              <option value="simple">Simple Chat</option>
              <option value="standard">Standard</option>
              <option value="expert">Expert Analyst</option>
            </select>
          </div>
        </div>
      </header>

      <main className="main-layout">
        <section className="image-panel glass-effect">
          <div className="panel-inner">
            {!imagePreview ? (
              <div className="empty-state" onClick={() => fileInputRef.current.click()}>
                <div className="pulse-icon">📸</div>
                <h2>Drop an image here</h2>
                <p>Start a conversation with a visual story</p>
              </div>
            ) : (
              <div className="image-focus">
                <img src={imagePreview} alt="Target" className="main-image" />
                <div className="image-stats">
                  <div className="stat-pill">Active Focus</div>
                </div>
              </div>
            )}
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleImageUpload}
              style={{ display: 'none' }}
              accept="image/*"
            />
          </div>
        </section>

        <section className="chat-container">
          <div className="messages-window">
            {messages.length === 0 && (
              <div className="onboarding">
                <h2>Hello! I'm your Visual Assistant.</h2>
                <p>Upload a photo and let's explore the details together.</p>
              </div>
            )}
            {messages.map((msg, i) => (
              <div key={i} className={`chat-row ${msg.role}`}>
                <div className="chat-bubble glass-effect">
                  {msg.image && <img src={msg.image} className="chat-inline-img" alt="Context" />}
                  <div className="chat-text">{msg.content}</div>
                </div>
                {msg.suggestions && (
                  <div className="suggestions-row">
                    {msg.suggestions.map((s, si) => (
                      <button key={si} className="suggestion-pill" onClick={() => handleSend(s)}>
                        {s}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {isLoading && (
              <div className="chat-row assistant">
                <div className="chat-bubble glass-effect typing">
                  <span></span><span></span><span></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="input-bar glass-effect">
            <button className="attach-btn" onClick={() => fileInputRef.current.click()}>
              {image ? '✅' : '📎'}
            </button>
            <textarea
              placeholder="Ask anything about the image..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
            />
            <button className="action-btn" onClick={() => handleSend()}>
              Explore
            </button>
          </div>
        </section>

        <aside className="story-panel glass-effect">
          <h3>Visual Story</h3>
          <div className="story-card">
            <label>Current Narrative</label>
            <p>{visualStory.context}</p>
          </div>

          <div className="story-meta">
            <div className="meta-item">
              <span className="label">Scene Mood</span>
              <span className="value">{visualStory.mood}</span>
            </div>
            <div className="meta-item">
              <span className="label">Detected Focus</span>
              <div className="focus-tags">
                {visualStory.details.map((d, i) => <span key={i} className="tag">{d}</span>)}
              </div>
            </div>
          </div>

          <div className="guided-pathways">
            <h4>Suggested Exploration</h4>
            <button className="path-btn" onClick={() => handleSend("What's the overall mood?")}>🎭 Mood Analysis</button>
            <button className="path-btn" onClick={() => handleSend("Describe any safety risks.")}>🛡️ Risk Assessment</button>
            <button className="path-btn" onClick={() => handleSend("Tell me a creative story about this image.")}>✍️ Storytelling</button>
          </div>
        </aside>
      </main>
    </div>
  );
}

export default App;
