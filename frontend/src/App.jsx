import React, { useState, useRef, useEffect } from 'react';
import './App.css';
import {
  signInWithPopup,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  onAuthStateChanged,
  signOut,
  updateProfile
} from "firebase/auth";
import { auth, googleProvider } from "./firebase";

const AuthModal = ({ onLogin }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [isAuthLoading, setIsAuthLoading] = useState(false);

  useEffect(() => {
    setError('');
  }, [isLogin]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsAuthLoading(true);

    try {
      if (isLogin) {
        const userCredential = await signInWithEmailAndPassword(auth, email, password);
        onLogin({
          id: userCredential.user.uid,
          username: userCredential.user.displayName || userCredential.user.email.split('@')[0],
          email: userCredential.user.email,
          avatar: userCredential.user.photoURL
        });
      } else {
        const userCredential = await createUserWithEmailAndPassword(auth, email, password);
        await updateProfile(userCredential.user, { displayName: username });
        onLogin({
          id: userCredential.user.uid,
          username: username,
          email: userCredential.user.email,
          avatar: null
        });
      }
    } catch (err) {
      console.error(err);
      setError(err.message.replace('Firebase: ', ''));
    } finally {
      setIsAuthLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    setIsAuthLoading(true);
    setError('');
    try {
      const result = await signInWithPopup(auth, googleProvider);
      onLogin({
        id: result.user.uid,
        username: result.user.displayName,
        email: result.user.email,
        avatar: result.user.photoURL
      });
    } catch (err) {
      console.error(err);
      setError(err.message.replace('Firebase: ', ''));
    } finally {
      setIsAuthLoading(false);
    }
  };

  return (
    <div className="auth-overlay">
      <div className="auth-modal fade-in">
        <div className="auth-welcome">
          <h2>Level Up Your Vision</h2>
          <p>Create an account to persist your chat history, save visual insights, and sync across devices.</p>
        </div>

        <div className="primary-actions">
          <button className="google-btn" onClick={handleGoogleLogin} disabled={isAuthLoading}>
            <span className="google-icon">G</span>
            {isAuthLoading ? "Connecting..." : "Continue with Google"}
          </button>
        </div>

        <div className="or-divider">
          <span>or use email</span>
        </div>

        <div className="auth-tabs">
          <button type="button" className={`auth-tab ${isLogin ? 'active' : ''}`} onClick={() => setIsLogin(true)}>Login</button>
          <button type="button" className={`auth-tab ${!isLogin ? 'active' : ''}`} onClick={() => setIsLogin(false)}>Sign Up</button>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          <input type="email" placeholder="Email Address" className="auth-input" value={email} onChange={(e) => setEmail(e.target.value)} required />
          {!isLogin && (
            <input type="text" placeholder="Username" className="auth-input" value={username} onChange={(e) => setUsername(e.target.value)} required />
          )}
          <input type="password" placeholder="Password" className="auth-input" value={password} onChange={(e) => setPassword(e.target.value)} required />
          {error && <p className="auth-error-msg">{error}</p>}
          <button className="auth-btn" disabled={isAuthLoading}>
            {isAuthLoading ? 'Authenticating...' : (isLogin ? 'Enter Engine' : 'Create Account')}
          </button>
        </form>

        <div className="guest-anchor">
          <p>Want to try it first? <button onClick={() => onLogin({ username: 'Guest', isGuest: true })} className="text-link">Continue as Guest</button></p>
          <small>History will only be stored locally in guest mode.</small>
        </div>
      </div>
    </div>
  );
};

function App() {
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState('upload');
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [image, setImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [metadata, setMetadata] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [theme, setTheme] = useState('light');
  const [activeBoundingBox, setActiveBoundingBox] = useState(null);
  const [visionData, setVisionData] = useState(null);
  const [historyList, setHistoryList] = useState([]);

  const [insights, setInsights] = useState({
    mood: { content: "Awaiting context.", confidence: "low" },
    risk: { content: "Monitoring hazards...", confidence: "low" },
    story: { content: "Narrative pending...", confidence: "low" }
  });

  const [selectedMode, setSelectedMode] = useState('NONE');
  const [isModeLocked, setIsModeLocked] = useState(false);
  const [isImageSynced, setIsImageSynced] = useState(false);
  const modes = [
    'MODE 1: STORYTELLING',
    'MODE 2: CHART INTERPRETATION',
    'MODE 3: GENERAL IMAGE ANALYSIS',
    'MODE 4: LEARNING / DIAGRAM EXPLANATION'
  ];

  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  // Authentication & Persistence Hook
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (firebaseUser) => {
      if (firebaseUser) {
        const userData = {
          id: firebaseUser.uid,
          username: firebaseUser.displayName || firebaseUser.email.split('@')[0],
          email: firebaseUser.email,
          avatar: firebaseUser.photoURL,
          isGuest: false
        };
        setUser(userData);
        fetchHistory(firebaseUser.uid);
      } else {
        const savedUser = localStorage.getItem('visionary_user');
        if (savedUser) {
          const parsed = JSON.parse(savedUser);
          if (parsed.isGuest) setUser(parsed);
          else setUser(null);
        } else {
          setUser(null);
        }
      }
    });
    return () => unsubscribe();
  }, []);

  // Guest Session Restore
  useEffect(() => {
    if (user && user.isGuest) {
      const savedGuest = localStorage.getItem('visionary_guest_session');
      if (savedGuest) {
        const parsed = JSON.parse(savedGuest);
        setSessionId(parsed.id);
        setImagePreview(parsed.image_preview);
        setMessages(parsed.messages);
      }
    }
  }, [user]);

  // Guest Session Auto-Save
  useEffect(() => {
    if (user && user.isGuest && messages.length > 0) {
      const guestSession = {
        id: sessionId || 'guest-session',
        image_preview: imagePreview,
        messages: messages,
        last_updated: new Date().toISOString()
      };
      localStorage.setItem('visionary_guest_session', JSON.stringify(guestSession));
    }
  }, [messages, user, sessionId, imagePreview]);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const fetchHistory = async (userId) => {
    try {
      const res = await fetch(`http://localhost:8000/api/auth/history/${userId}`);
      const data = await res.json();
      setHistoryList(data.history || []);
    } catch (e) {
      console.error("History sync failed");
    }
  };

  const handleLogin = (userData) => {
    setUser(userData);
    if (userData.isGuest) {
      localStorage.setItem('visionary_user', JSON.stringify(userData));
    }
  };

  const handleLogout = async () => {
    try {
      await signOut(auth);
    } catch (e) {
      console.error("Sign out error", e);
    }
    setUser(null);
    resetSession();
    localStorage.removeItem('visionary_user');
    localStorage.removeItem('visionary_guest_session');
  };

  const resetSession = () => {
    setMessages([]);
    setSessionId(null);
    setImagePreview(null);
    setImage(null);
    setVisionData(null);
    setSelectedMode('NONE');
    setIsModeLocked(false);
    setIsImageSynced(false);
    setActiveTab('upload');
  };

  const resumeSession = (session) => {
    setSessionId(session.id);
    setImagePreview(session.image_preview);
    setMessages(session.messages);
    setActiveTab('chat');
  };

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImage(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result);
        const img = new Image();
        img.onload = () => {
          setMetadata({
            name: file.name,
            size: `${(file.size / 1024).toFixed(1)} KB`,
            resolution: `${img.width}x${img.height}px`
          });
        };
        img.src = reader.result;
      };
      reader.readAsDataURL(file);
    }
  };

  const parseStructuredResponse = (text) => {
    // Match lines like "Header: content" or "Header (Detail): content"
    const lines = text.split('\n');
    let blocks = [];
    let currentBlock = null;

    lines.forEach(line => {
      // Regex matches Start of line, Uppercase Letter, followed by letters/spaces/parens, then colon
      const match = line.match(/^([A-Z][A-Za-z\s\(\)/]+):/);
      if (match) {
        if (currentBlock) blocks.push(currentBlock);
        currentBlock = { title: match[1].trim(), content: line.substring(match[0].length).trim() };
      } else if (currentBlock) {
        currentBlock.content += (currentBlock.content ? '\n' : '') + line;
      }
    });
    if (currentBlock) blocks.push(currentBlock);

    if (blocks.length > 0) {
      // If we only found one block and it's basically the whole text, maybe it wasn't structured
      if (blocks.length === 1 && blocks[0].content.length < text.length * 0.5) return { observation: text, fullText: text };
      return { blocks };
    }

    return { observation: text, fullText: text };
  };

  const handleSend = async (overrideQuery = null, actionType = null) => {
    const queryToSend = overrideQuery || input;
    if ((!queryToSend.trim() && !image) || isLoading) return;
    const currentInput = queryToSend;
    const currentImage = image;

    setInput('');
    setIsLoading(true);

    if (currentInput || currentImage) {
      setMessages(prev => [...prev, { role: 'user', content: currentInput || "Analyze this image.", image: activeTab === 'chat' && currentImage ? imagePreview : null }]);
    }

    try {
      const formData = new FormData();
      formData.append('query', currentInput || "Initialize reasoning engine.");

      // Only send the image file if it hasn't been synced to the session yet
      if (currentImage && !isImageSynced) {
        formData.append('image', currentImage);
      }

      if (sessionId) formData.append('session_id', sessionId);
      if (user && !user.isGuest) formData.append('user_id', user.id);
      formData.append('mode', selectedMode);
      if (selectedMode !== 'NONE') setIsModeLocked(true);
      if (imagePreview) formData.append('image_preview', imagePreview);

      const response = await fetch('http://localhost:8000/api/chat', { method: 'POST', body: formData });
      const data = await response.json();

      setSessionId(data.session_id);
      setVisionData(data.vision_metadata);
      if (currentImage) setIsImageSynced(true);

      if (data.vision_metadata) {
        setInsights({
          mood: { content: data.visual_summary, confidence: "high" },
          risk: { content: data.risk_assessment, confidence: "medium" },
          story: { content: data.narrative || "Story generation in progress.", confidence: "medium" }
        });
        if (data.vision_metadata.bounding_boxes?.length > 0) {
          setActiveBoundingBox(data.vision_metadata.bounding_boxes[0]);
        }
      }

      const structured = parseStructuredResponse(data.response.text);
      setMessages(prev => [...prev, {
        role: 'assistant',
        ...structured,
        fullText: data.response.text,
        suggestions: data.response.smart_suggestions,
        timestamp: new Date().toLocaleTimeString()
      }]);

    } catch (error) {
      setMessages(prev => [...prev, { role: 'assistant', observation: "Server sync failed." }]);
    } finally {
      setIsLoading(false);
    }
  };

  if (!user) return <AuthModal onLogin={handleLogin} />;

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="header-top">
          <div className="logo-section">
            <span className="brand-icon">👁️‍🗨️</span>
            <h1 className="app-title">Visionary Pro</h1>
          </div>
          <div className="header-controls">
            <button className="theme-toggle" onClick={() => setTheme(t => t === 'light' ? 'dark' : 'light')}>
              {theme === 'light' ? '🌙' : '☀️'}
            </button>
            <div className="user-profile">
              {user.avatar && <img src={user.avatar} className="user-avatar" alt="User" />}
              <span className="user-name">{user.username}</span>
              {user.isGuest && <span className="guest-pill">Guest</span>}
            </div>
            <button onClick={handleLogout} className="logout-btn">Logout</button>
            {isModeLocked && (
              <button
                className="reset-session-pill"
                onClick={resetSession}
                style={{ marginLeft: '15px' }}
              >
                Reset 🔄
              </button>
            )}
          </div>
        </div>

        <nav className="primary-nav">
          {['upload', 'chat', 'reports'].map(tab => (
            <button
              key={tab}
              className={`nav-tab ${activeTab === tab ? 'active' : ''}`}
              onClick={() => setActiveTab(tab)}
            >
              {[tab.toUpperCase()]}
            </button>
          ))}
        </nav>
      </header>

      <main className="tab-content">
        {selectedMode === 'NONE' ? (
          <div className="mode-init-screen">
            <div className="mode-init-header">
              <h2>System Lock: Select Intelligence Protocol</h2>
              <p>You must initialize a mode to unlock the reasoning engine.</p>
            </div>
            <div className="mode-selection-grid">
              {modes.map(m => (
                <div key={m} className="mode-card" onClick={() => {
                  setSelectedMode(m);
                  setIsModeLocked(true);
                  setActiveTab('chat');
                }}>
                  <div className="mode-card-icon">
                    {m === 'MODE 1: STORYTELLING' && '🎭'}
                    {m === 'MODE 2: CHART INTERPRETATION' && '📊'}
                    {m === 'MODE 3: GENERAL IMAGE ANALYSIS' && '🔍'}
                    {m === 'MODE 4: LEARNING / DIAGRAM EXPLANATION' && '📚'}
                  </div>
                  <h3>{m.split(': ')[1]}</h3>
                  <p>Initialize a {m.split(': ')[1].toLowerCase()} session.</p>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <>
            {/* TAB 1: UPLOAD */}
            {activeTab === 'upload' && (
              <div className="upload-view">
                <div style={{ display: 'flex', gap: '40px', width: '100%', maxWidth: '1000px' }}>
                  <div style={{ flex: 2 }}>
                    {!imagePreview ? (
                      <div className="dropzone" onClick={() => fileInputRef.current.click()}>
                        <div className="mode-badge">{selectedMode.split(': ')[1]}</div>
                        <div style={{ fontSize: '48px', marginBottom: '20px' }}>📁</div>
                        <h2>{selectedMode === 'MODE 2: CHART INTERPRETATION' ? 'Chart Data Ingestion' : 'Scene Processing'}</h2>
                        <p>Feed the {selectedMode.split(': ')[1].toLowerCase()} engine with an image</p>
                        <input type="file" ref={fileInputRef} onChange={handleImageUpload} className="hidden" accept="image/*" />
                      </div>
                    ) : (
                      <div className="upload-preview-container">
                        <div className="preview-img-wrapper">
                          <img src={imagePreview} className="preview-img" alt="Uploaded" />
                        </div>
                        <div className="img-metadata">
                          <div className="meta-box"><label>File Name</label><span>{metadata?.name}</span></div>
                          <div className="meta-box"><label>Resolution</label><span>{metadata?.resolution}</span></div>
                          <div className="meta-box"><label>Size</label><span>{metadata?.size}</span></div>
                        </div>
                        <div style={{ display: 'flex', gap: '15px' }}>
                          <button className="action-btn-primary" style={{ flex: 1 }} onClick={() => { handleSend(); setActiveTab('chat'); }}>Begin {selectedMode.split(': ')[1]} Analysis</button>
                          <button className="action-btn-primary" style={{ background: 'var(--accent-gold)' }} onClick={() => { setImage(null); setImagePreview(null); setSessionId(null); setMessages([]); }}>Reset</button>
                        </div>
                      </div>
                    )}
                  </div>
                  <div className="upload-instructions" style={{ flex: 1 }}>
                    <h3>Protocol Instructions</h3>
                    <p>Operating in <strong>{selectedMode.split(': ')[1]}</strong></p>
                    <ul style={{ listStyle: 'none', padding: 0, marginTop: '15px' }}>
                      <li style={{ marginBottom: '10px' }}>✅ Ensure high image clarity</li>
                      <li style={{ marginBottom: '10px' }}>✅ {selectedMode === 'MODE 2: CHART INTERPRETATION' ? 'Labels should be readable' : 'Keep main subjects centered'}</li>
                      <li style={{ marginBottom: '10px' }}>✅ Avoid heavy shadows</li>
                    </ul>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 2: CHAT */}
            {activeTab === 'chat' && (
              <div className="chat-view">
                <div className="chat-main">
                  <div className="messages-window">
                    {messages.length === 0 && (
                      <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-secondary)' }}>
                        {!imagePreview ? (
                          <div className="upload-reminder fade-in">
                            <div style={{ fontSize: '40px', marginBottom: '15px' }}>🖼️</div>
                            <h3>Visual Context Missing</h3>
                            <p>Active Mode: <strong>{selectedMode.split(': ')[1]}</strong></p>
                            <p>Please upload an image to begin.</p>
                            <div style={{ marginTop: '20px', display: 'flex', gap: '10px', justifyContent: 'center' }}>
                              <button className="action-btn-primary" onClick={() => setActiveTab('upload')}>Go to Upload Center</button>
                              <button className="action-btn-primary" style={{ background: 'var(--accent-gold)' }} onClick={() => fileInputRef.current.click()}>Quick Upload</button>
                            </div>
                          </div>
                        ) : (
                          "Please upload an image to begin."
                        )}
                      </div>
                    )}
                    {messages.map((msg, i) => (
                      <div key={i} className={`message-node ${msg.role}`}>
                        <div className="bubble">
                          {msg.image && <img src={msg.image} style={{ width: '100%', borderRadius: '8px', marginBottom: '10px' }} alt="Ctx" />}
                          {msg.role === 'assistant' ? (
                            <div className="reasoning-stack">
                              {msg.blocks ? msg.blocks.map((block, bi) => (
                                <div key={bi} className="reasoning-block">
                                  <strong>{block.title}:</strong> {block.content}
                                </div>
                              )) : (
                                <>
                                  <div className="reasoning-block"><strong>👁️ Observation:</strong> {msg.observation}</div>
                                  {msg.reasoning && <div className="reasoning-block"><strong>🧠 Reasoning:</strong> {msg.reasoning}</div>}
                                  {msg.recommendation && <div className="reasoning-block"><strong>💡 Recommendation:</strong> {msg.recommendation}</div>}
                                </>
                              )}
                            </div>
                          ) : <div>{msg.content}</div>}
                        </div>
                      </div>
                    ))}
                    {isLoading && <div className="message-node assistant"><div className="bubble">Reasoning...</div></div>}
                    <div ref={messagesEndRef} />
                  </div>
                  <div className="chat-status-bar">
                    <span className="active-protocol-tag">
                      PROTOCOL: <strong>{selectedMode.split(': ')[1]}</strong> 🔒
                    </span>
                  </div>
                  <div className="input-dock" style={{ borderTop: '1px solid var(--border-subtle)', padding: '20px' }}>
                    <div className="input-container" style={{ display: 'flex', gap: '15px' }}>
                      <textarea
                        className="main-textarea"
                        placeholder="Probe the visual intelligence..."
                        style={{ flex: 1, padding: '15px', borderRadius: '12px', border: '1px solid var(--border-subtle)', background: 'var(--bg-main)', outline: 'none' }}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
                      />
                      <button className="send-action" onClick={() => handleSend()} style={{ width: '50px', borderRadius: '12px', background: 'var(--primary-olive)', color: '#fff', border: 'none' }}>→</button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 3: REPORTS */}
            {activeTab === 'reports' && (
              <div className="reports-view">
                <div className="report-mockup">
                  <h1 style={{ borderBottom: '2px solid #333', paddingBottom: '20px' }}>Visual Intelligence Audit Report</h1>
                  <div style={{ marginTop: '30px', display: 'flex', gap: '20px' }}>
                    <div style={{ flex: 1 }}>
                      <h4>Session ID</h4><p style={{ fontSize: '0.8rem' }}>{sessionId || "N/A"}</p>
                      <h4>Generated On</h4><p style={{ fontSize: '0.8rem' }}>{new Date().toLocaleDateString()}</p>
                    </div>
                    <div style={{ flex: 1, border: '1px solid #eee', padding: '10px' }}>
                      {imagePreview ? <img src={imagePreview} style={{ width: '100%' }} alt="Report Ctx" /> : "No Image"}
                    </div>
                  </div>
                  <div style={{ marginTop: '40px' }}>
                    <h3>Key Analytical Findings</h3>
                    <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '10px' }}>
                      <thead><tr style={{ background: '#f5f5f5' }}><th style={{ textAlign: 'left', padding: '10px' }}>Metric</th><th style={{ textAlign: 'left', padding: '10px' }}>Value</th></tr></thead>
                      <tbody>
                        {/* Dynamic Metrics from last Assistant Message */}
                        {(() => {
                          const lastMsg = [...messages].reverse().find(m => m.role === 'assistant');
                          const metricsBlock = lastMsg?.blocks?.find(b => b.title.includes('Key Metrics'));
                          const pointsBlock = lastMsg?.blocks?.find(b => b.title.includes('Key Points'));

                          if (metricsBlock || pointsBlock) {
                            return (
                              <>
                                {metricsBlock && (
                                  <tr>
                                    <td style={{ padding: '10px', borderBottom: '1px solid #eee' }}><strong>{metricsBlock.title}</strong></td>
                                    <td style={{ padding: '10px', borderBottom: '1px solid #eee' }}>{metricsBlock.content}</td>
                                  </tr>
                                )}
                                {pointsBlock && (
                                  <tr>
                                    <td style={{ padding: '10px', borderBottom: '1px solid #eee' }}><strong>{pointsBlock.title}</strong></td>
                                    <td style={{ padding: '10px', borderBottom: '1px solid #eee' }}>{pointsBlock.content}</td>
                                  </tr>
                                )}
                                <tr>
                                  <td style={{ padding: '10px', borderBottom: '1px solid #eee' }}>Visual Complexity</td>
                                  <td style={{ padding: '10px', borderBottom: '1px solid #eee' }}>{visionData?.spatial_metrics?.complexity_score?.toFixed(2) || 'N/A'}</td>
                                </tr>
                              </>
                            );
                          }

                          // Fallback to presets if no dynamic blocks found
                          return (
                            <>
                              {selectedMode === 'MODE 1: STORYTELLING' && (
                                <>
                                  <tr><td style={{ padding: '10px', borderBottom: '1px solid #eee' }}>Narrative Depth</td><td style={{ padding: '10px', borderBottom: '1px solid #eee' }}>High (Imaginative)</td></tr>
                                  <tr><td style={{ padding: '10px', borderBottom: '1px solid #eee' }}>Creative Vocabulary</td><td style={{ padding: '10px', borderBottom: '1px solid #eee' }}>Expressive</td></tr>
                                </>
                              )}
                              {selectedMode === 'MODE 2: CHART INTERPRETATION' && (
                                <>
                                  <tr><td style={{ padding: '10px', borderBottom: '1px solid #eee' }}>Data Precision</td><td style={{ padding: '10px', borderBottom: '1px solid #eee' }}>High (Pixel Accurate)</td></tr>
                                  <tr><td style={{ padding: '10px', borderBottom: '1px solid #eee' }}>Detected Trends</td><td style={{ padding: '10px', borderBottom: '1px solid #eee' }}>Analytical Graphing</td></tr>
                                </>
                              )}
                              {selectedMode === 'MODE 3: GENERAL IMAGE ANALYSIS' && (
                                <>
                                  <tr><td style={{ padding: '10px', borderBottom: '1px solid #eee' }}>Semantic Clarity</td><td style={{ padding: '10px', borderBottom: '1px solid #eee' }}>Objective Overview</td></tr>
                                  <tr><td style={{ padding: '10px', borderBottom: '1px solid #eee' }}>Primary Elements</td><td style={{ padding: '10px', borderBottom: '1px solid #eee' }}>{visionData ? Object.keys(visionData.detected_objects).length : 0} Identified</td></tr>
                                </>
                              )}
                              {selectedMode === 'MODE 4: LEARNING / DIAGRAM EXPLANATION' && (
                                <>
                                  <tr><td style={{ padding: '10px', borderBottom: '1px solid #eee' }}>Logic Granularity</td><td style={{ padding: '10px', borderBottom: '1px solid #eee' }}>Step-by-Step Clear</td></tr>
                                  <tr><td style={{ padding: '10px', borderBottom: '1px solid #eee' }}>Technical Depth</td><td style={{ padding: '10px', borderBottom: '1px solid #eee' }}>Educational/Structural</td></tr>
                                </>
                              )}
                            </>
                          );
                        })()}
                        <tr><td style={{ padding: '10px', borderBottom: '1px solid #eee' }}>Active Protocol</td><td style={{ padding: '10px', borderBottom: '1px solid #eee' }}>{selectedMode.split(': ')[1]}</td></tr>
                      </tbody>
                    </table>
                  </div>

                  {/* Intelligence Summary and Highlights */}
                  {(() => {
                    const lastMsg = [...messages].reverse().find(m => m.role === 'assistant');
                    const summaryBlock = lastMsg?.blocks?.find(b => ['The Narrative', 'Key Observations', 'Step-by-Step Explanation', 'Image Overview', 'Observation'].some(t => b.title.includes(t)));
                    const pointsBlock = lastMsg?.blocks?.find(b => b.title.includes('Key Points'));

                    return (
                      <div className="report-narrative-section" style={{ marginTop: '30px', padding: '20px', background: '#fff' }}>
                        <div style={{ marginBottom: '25px' }}>
                          <h3 style={{ borderBottom: '1px solid #eee', paddingBottom: '10px' }}>Intelligence Summary</h3>
                          <p style={{ lineHeight: '1.6', color: '#444', fontSize: '0.95rem' }}>
                            {summaryBlock ? summaryBlock.content : (lastMsg?.observation || "Complete visual summary pending analysis.")}
                          </p>
                        </div>

                        <div>
                          <h3 style={{ borderBottom: '1px solid #eee', paddingBottom: '10px' }}>Key Highlights</h3>
                          <ul style={{ paddingLeft: '20px', color: '#444' }}>
                            {pointsBlock ?
                              pointsBlock.content.split(/[,\n•]/).map((p, i) => p.trim() && (
                                <li key={i} style={{ marginBottom: '8px', fontSize: '0.9rem' }}>{p.trim()}</li>
                              ))
                              : (
                                <>
                                  <li style={{ marginBottom: '8px', fontSize: '0.9rem' }}>Visual context anchoring complete</li>
                                  <li style={{ marginBottom: '8px', fontSize: '0.9rem' }}>Object relationship mapping established</li>
                                </>
                              )
                            }
                          </ul>
                        </div>
                      </div>
                    );
                  })()}
                </div>
                <button className="action-btn-primary" onClick={() => window.print()}>📥 Export as Unified PDF</button>
              </div>
            )}
          </>
        )}
      </main>
    </div >
  );
}

export default App;
