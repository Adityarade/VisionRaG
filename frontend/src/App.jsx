import { useState, useEffect, useRef } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, PieChart, Pie, Cell, Legend } from 'recharts';
import './index.css';

function App() {
  const [file, setFile] = useState(null);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [chatMessage, setChatMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [enableAutoSummary, setEnableAutoSummary] = useState(true);
  const [analytics, setAnalytics] = useState(null);
  const [isChatOpen, setIsChatOpen] = useState(false);
  
  // Advanced Settings State
  const [apiKey, setApiKey] = useState('');
  const [temperature, setTemperature] = useState(0.1);
  const [topK, setTopK] = useState(5);
  const [exportFormat, setExportFormat] = useState('pdf');
  const [includeBbox, setIncludeBbox] = useState(true);
  const chatEndRef = useRef(null);

  // Fetch analytics on load
  useEffect(() => {
    fetch('http://localhost:8000/api/analytics')
      .then(res => res.json())
      .then(data => setAnalytics(data))
      .catch(err => console.error("Could not load analytics", err));
  }, []);

  useEffect(() => {
    // Scroll to bottom of chat when history changes
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory, isChatOpen]);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;
    
    setLoading(true);
    setResults(null);
    const formData = new FormData();
    formData.append('files', file);
    formData.append('conf_threshold', 0.25);
    formData.append('enable_auto_summary', enableAutoSummary);

    try {
      const res = await fetch('http://localhost:8000/api/upload', {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) throw new Error("Upload failed on server.");
      const data = await res.json();
      
      if (data.error) {
          throw new Error(data.error);
      }
      
      setResults(data.results);
      // Refresh analytics after upload
      fetch(`http://localhost:8000/api/analytics?t=${Date.now()}`)
        .then(res => res.json())
        .then(data => setAnalytics(data));
    } catch (err) {
      console.error(err);
      alert("Error: " + err.message);
    } finally {
      setLoading(false);
    }
  };



  const handleChat = async (e, suggestedMsg = null) => {
    if (e) e.preventDefault();
    const msgToProcess = suggestedMsg || chatMessage;
    if (!msgToProcess) return;

    const newMessage = { role: 'user', content: msgToProcess };
    setChatHistory((prev) => [...prev, newMessage]);
    if (!suggestedMsg) setChatMessage('');

    try {
      const res = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msgToProcess }),
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Chat failed on server.");
      }
      
      setChatHistory(prev => [...prev, { role: 'ai', content: '' }]);
      
      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\\n\\n');
        buffer = lines.pop();
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.substring(6));
              if (data.type === 'token') {
                setChatHistory(prev => {
                  const newHistory = [...prev];
                  newHistory[newHistory.length - 1].content += data.content;
                  return newHistory;
                });
              } else if (data.type === 'sources') {
                if (data.content.length > 0) {
                  setChatHistory(prev => {
                    const newHistory = [...prev];
                    let sourceText = "\\n\\n**Sources:**\\n";
                    data.content.forEach((s, i) => {
                       sourceText += `[${i+1}] ${s.filename} (Page ${s.page_num})\\n`;
                    });
                    newHistory[newHistory.length - 1].content += sourceText;
                    return newHistory;
                  });
                }
              }
            } catch (e) {
              console.error("SSE Parse Error:", e);
            }
          }
        }
      }
      
    } catch (err) {
      console.error(err);
      let errorMsg = "⚠️ Connection error. Backend may be offline.";
      if (err.message.includes("429") || err.message.includes("Quota")) {
          errorMsg = "⚠️ Google Gemini Free-Tier limit reached! Please wait 1 minute before asking another question.";
      } else if (err.message && err.message !== "Chat failed on server.") {
          errorMsg = `⚠️ Error: ${err.message}`;
      }
      setChatHistory(prev => [...prev, { role: 'ai', content: errorMsg }]);
    }
  };

  const suggestedQuestions = [
    "What are the main entities detected?",
    "Summarize the uploaded documents.",
    "Extract all numerical data."
  ];

  return (
    <div className="app-container">
      {/* Navigation Bar */}
      <nav className="navbar">
        <div className="nav-brand">
          <img src="/logo.png" alt="VisionRAG Pro Logo" className="logo" />
          <span className="brand-text">VisionRAG Pro</span>
        </div>
        <div className="nav-links">
          <a href="#how-it-works" className="nav-link">How it Works</a>
          <a href="#dashboard" className="nav-link">Workspace</a>
          <a href="#analytics" className="nav-link">Analytics</a>
          <a href="#settings" className="nav-link">Settings</a>
        </div>
        <button className="mobile-menu-btn" onClick={() => setIsSidebarOpen(!isSidebarOpen)}>☰</button>
      </nav>

      {/* Hero Section */}
      <header className="hero">
        <div className="hero-content">
          <h1>Enterprise AI Document Intelligence</h1>
          <p>Instantly process, extract, and chat with your visual documents using NVIDIA Llama 3 and YOLOv8.</p>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="main-content">
        
        {/* How It Works Section */}
        <section id="how-it-works" className="how-it-works-section glass-panel full-width">
          <div className="section-header">
            <span className="icon">💡</span>
            <h2>How It Works</h2>
          </div>
          <div className="steps-container">
            <div className="step-card">
              <div className="step-number">1</div>
              <h3>Upload & Process</h3>
              <p>Drag and drop any PDF or Image. Our YOLOv8 engine automatically detects objects and structures.</p>
            </div>
            <div className="step-card">
              <div className="step-number">2</div>
              <h3>AI Extraction</h3>
              <p>NVIDIA Llama 3.2 Vision visually analyzes the content, extracting OCR text and generating smart summaries.</p>
            </div>
            <div className="step-card">
              <div className="step-number">3</div>
              <h3>Intelligent Chat</h3>
              <p>Ask our AI Assistant anything about your documents using Vector Similarity Search (ChromaDB).</p>
            </div>
          </div>
        </section>

        {/* Analytics Section */}
        <section id="analytics" className="analytics-section glass-panel full-width">
          <div className="section-header">
            <span className="icon">📊</span>
            <h2>System Analytics</h2>
          </div>
          <div className="stats-grid">
            <div className="stat-card">
              <h4>Total Processed</h4>
              <span className="stat-value">{analytics ? analytics.unique_pages : '-'} Pages</span>
            </div>
            <div className="stat-card">
              <h4>Objects Detected</h4>
              <span className="stat-value">{analytics ? analytics.total_objects : '-'}</span>
            </div>
            <div className="stat-card">
              <h4>Vector Chunks</h4>
              <span className="stat-value">{analytics ? analytics.total_chunks : '-'}</span>
            </div>
          </div>
          {analytics && analytics.class_counts && (
            <div className="charts-container" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem', marginTop: '2rem' }}>
              <div className="chart-wrapper glass-panel" style={{ padding: '1.5rem' }}>
                <h4 style={{ textAlign: 'center', marginBottom: '1.5rem', color: '#94a3b8' }}>Object Distribution</h4>
                {Object.keys(analytics.class_counts).length > 0 ? (
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={Object.entries(analytics.class_counts).map(([name, count]) => ({ name, count }))}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                    <XAxis dataKey="name" stroke="#94a3b8" />
                    <YAxis stroke="#94a3b8" allowDecimals={false} />
                    <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }} />
                    <Bar dataKey="count" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
                ) : (
                  <p style={{ textAlign: 'center', color: '#64748b', marginTop: '3rem' }}>No objects detected yet.</p>
                )}
              </div>
              <div className="chart-wrapper glass-panel" style={{ padding: '1.5rem' }}>
                <h4 style={{ textAlign: 'center', marginBottom: '1.5rem', color: '#94a3b8' }}>Class Composition</h4>
                {Object.keys(analytics.class_counts).length > 0 ? (
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={Object.entries(analytics.class_counts).map(([name, count]) => ({ name, count }))}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={90}
                      paddingAngle={5}
                      dataKey="count"
                    >
                      {Object.keys(analytics.class_counts).map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={['#8b5cf6', '#0ea5e9', '#ec4899', '#10b981', '#f59e0b', '#ef4444'][index % 6]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }} />
                    <Legend wrapperStyle={{ color: '#94a3b8' }} />
                  </PieChart>
                </ResponsiveContainer>
                ) : (
                  <p style={{ textAlign: 'center', color: '#64748b', marginTop: '3rem' }}>No data to display.</p>
                )}
              </div>
            </div>
          )}
        </section>



        {/* Dashboard / Ingestion */}
        <section id="dashboard" className="upload-section glass-panel">
          <div className="section-header">
            <span className="icon">📤</span>
            <h2>Ingestion Engine</h2>
          </div>
          <form onSubmit={handleUpload} className="upload-form">
            <div className="file-input-wrapper">
              <input 
                type="file" 
                onChange={(e) => setFile(e.target.files[0])} 
                className="file-input"
                id="fileInput"
              />
              <label htmlFor="fileInput" className="file-label">
                {file ? <span className="file-name">📄 {file.name}</span> : <span>Drag & Drop or Browse Files</span>}
              </label>
            </div>
            
            <button type="submit" disabled={!file || loading} className="primary-btn glow-btn">
              {loading ? (
                <span className="loading-spinner">Processing...</span>
              ) : '🚀 Execute Neural Pipeline'}
            </button>
          </form>
          
          {loading && (
            <div className="progress-container">
              <div className="progress-bar-indeterminate"></div>
              <p className="progress-text">Analyzing image data & extracting AI Insights...</p>
            </div>
          )}

          {results && (
            <div id="gallery" className="results-gallery fade-in">
              <h3>Processing Complete - Visual Search</h3>
              <div className="gallery-grid">
                {results.map((res, idx) => (
                  <div key={idx} className="result-card">
                    <div className="result-img-wrapper">
                      <img src={`http://localhost:8000${res.img_url}`} alt="Processed" />
                      <div className="badge">{res.objects_detected} Objects Found</div>
                    </div>
                    <div className="result-details">
                      <h4>{res.filename} (Page {res.page})</h4>
                      <div className="summary-box">
                        <strong>AI Summary:</strong>
                        <p>{res.summary}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>

        {/* Settings Section */}
        <section id="settings" className="settings-section glass-panel full-width">
          <div className="section-header">
            <span className="icon">⚙️</span>
            <h2>Configuration Modules</h2>
          </div>
          <div className="settings-grid">
            
            {/* Module 1: Processing & Engine */}
            <div className="settings-card glass-panel">
              <h3>Processing & Engine</h3>
              
              <div className="settings-row">
                <label className="toggle-label">
                  <input 
                    type="checkbox" 
                    checked={enableAutoSummary} 
                    onChange={(e) => setEnableAutoSummary(e.target.checked)} 
                  />
                  <span>Enable AI Auto-Summary</span>
                </label>
                <p className="setting-help">Uses NVIDIA Vision to summarize each page visually.</p>
              </div>

              <div className="settings-row" style={{ marginTop: '1rem' }}>
                <label>Creativity (Temperature): {temperature}</label>
                <input 
                  type="range" 
                  min="0" max="1" step="0.1" 
                  value={temperature} 
                  onChange={(e) => setTemperature(parseFloat(e.target.value))}
                  style={{ width: '100%' }}
                />
                <p className="setting-help">Higher = more creative, Lower = more analytical.</p>
              </div>
            </div>

            {/* Module 2: Retrieval & Knowledge Graph */}
            <div className="settings-card glass-panel">
              <h3>Retrieval Settings</h3>

              <div className="settings-row" style={{ marginTop: '1rem' }}>
                <label>Top-K Similarity Results: {topK}</label>
                <input 
                  type="range" 
                  min="1" max="10" step="1" 
                  value={topK} 
                  onChange={(e) => setTopK(parseInt(e.target.value))}
                  style={{ width: '100%' }}
                />
                <p className="setting-help">Number of chunks to fetch for the Chat Assistant.</p>
              </div>
            </div>

            {/* Module 3: Export & Reporting */}
            <div className="settings-card glass-panel">
              <h3>Export & Reporting</h3>
              
              <div className="settings-row">
                <label>Default Export Format</label>
                <select 
                  value={exportFormat} 
                  onChange={(e) => setExportFormat(e.target.value)}
                  className="modern-select"
                >
                  <option value="pdf">Intelligence Report (.pdf)</option>
                  <option value="csv">Data Dump (.csv)</option>
                  <option value="json">Raw Output (.json)</option>
                </select>
              </div>

              <div className="settings-row" style={{ marginTop: '1rem' }}>
                <label className="toggle-label">
                  <input 
                    type="checkbox" 
                    checked={includeBbox} 
                    onChange={(e) => setIncludeBbox(e.target.checked)} 
                  />
                  <span>Include Visual Bounding Boxes</span>
                </label>
                <p className="setting-help">Attach YOLOv8 processed images to final reports.</p>
              </div>
            </div>

          </div>
        </section>
      </main>

      {/* Floating Chatbot Widget */}
      <div className={`floating-chatbot ${isChatOpen ? 'open' : ''}`}>
        <div className="chat-toggle-btn" onClick={() => setIsChatOpen(!isChatOpen)}>
          {isChatOpen ? '✕' : '💬 Chat Assistant'}
        </div>
        
        {isChatOpen && (
          <div className="chat-window-container glass-panel">
            <div className="chat-header">
              <img src="/logo.png" alt="AI" className="chat-header-logo" />
              <h3>VisionRAG Assistant</h3>
            </div>
            
            <div className="chat-history">
              {chatHistory.length === 0 ? (
                <div className="empty-chat-state">
                  <img src="/logo.png" alt="AI Mascot" className="ai-mascot" />
                  <h4>How can I help you?</h4>
                  <div className="suggestions-grid">
                    {suggestedQuestions.map((q, i) => (
                      <button key={i} className="suggestion-chip" onClick={() => handleChat(null, q)}>
                        {q}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                chatHistory.map((msg, idx) => (
                  <div key={idx} className={`chat-bubble-wrapper ${msg.role}`}>
                    {msg.role === 'ai' && <img src="/logo.png" className="avatar ai-avatar" alt="AI" />}
                    <div className={`chat-bubble ${msg.role}`}>
                      {msg.content}
                    </div>
                  </div>
                ))
              )}
              <div ref={chatEndRef} />
            </div>
            
            <form onSubmit={handleChat} className="chat-input-form">
              <input 
                type="text" 
                value={chatMessage} 
                onChange={(e) => setChatMessage(e.target.value)} 
                placeholder="Ask about your documents..."
              />
              <button type="submit" className="send-btn" disabled={!chatMessage && chatHistory.length > 0}>
                ↗
              </button>
            </form>
          </div>
        )}
      </div>

      {/* Footer */}
      <footer className="footer">
        <div className="footer-content">
          <div className="footer-logo">
            <img src="/logo.png" alt="Logo" />
            <span>VisionRAG Pro © 2026</span>
          </div>
          <div className="footer-links">
            <span>Powered by FastAPI & Vite</span>
            <a href="#">Privacy Policy</a>
            <a href="#">Terms of Service</a>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
