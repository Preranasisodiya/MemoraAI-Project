import React, { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import "./App.css";

const API_BASE_URL = "http://127.0.0.1:8000";

export default function App() {
  // ----------------------------------------------------
  // Authentication State
  // ----------------------------------------------------
  const [token, setToken] = useState(
    localStorage.getItem("access_token") || ""
  );
  const [currentUser, setCurrentUser] = useState(null);
  const [authMode, setAuthMode] = useState("login"); // 'login' | 'register'
  const [authName, setAuthName] = useState("");
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState("");
  const [authSuccess, setAuthSuccess] = useState("");

  // ----------------------------------------------------
  // Conversations and Chat State
  // ----------------------------------------------------
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const [chatError, setChatError] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // ----------------------------------------------------
  // Documents and Upload State
  // ----------------------------------------------------
  const [documents, setDocuments] = useState([]);
  const [attachedDocuments, setAttachedDocuments] = useState([]);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showDocsModal, setShowDocsModal] = useState(false);
  const [showAttachModal, setShowAttachModal] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadNotification, setUploadNotification] = useState(null);

  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  // ----------------------------------------------------
  // Check Token & Load Profile on Startup
  // ----------------------------------------------------
  useEffect(() => {
    if (token) {
      fetchCurrentUser(token);
    }
  }, [token]);

  const fetchCurrentUser = async (jwtToken) => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/me`, {
        headers: { Authorization: `Bearer ${jwtToken}` },
      });
      if (res.ok) {
        const data = await res.json();
        setCurrentUser(data);
        loadConversations(jwtToken);
        loadDocuments(jwtToken);
      } else {
        handleLogout();
      }
    } catch {
      // Offline or network error
    }
  };

  const loadConversations = async (jwtToken = token) => {
    if (!jwtToken) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/conversations/`, {
        headers: { Authorization: `Bearer ${jwtToken}` },
      });
      if (res.ok) {
        const data = await res.json();
        setConversations(data);
      }
    } catch (err) {
      console.error("Error loading conversations:", err);
    }
  };

  const loadDocuments = async (jwtToken = token) => {
    if (!jwtToken) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/documents/`, {
        headers: { Authorization: `Bearer ${jwtToken}` },
      });
      if (res.ok) {
        const data = await res.json();
        setDocuments(data);
      }
    } catch (err) {
      console.error("Error loading documents:", err);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, asking]);

  // ----------------------------------------------------
  // Auth Handlers
  // ----------------------------------------------------
  const handleLogin = async (e) => {
    e.preventDefault();
    setAuthError("");
    setAuthSuccess("");

    if (!authEmail.trim() || !authPassword.trim()) {
      setAuthError("Please provide both email and password.");
      return;
    }

    setAuthLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: authEmail.trim(), password: authPassword }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Invalid email or password.");
      }

      localStorage.setItem("access_token", data.access_token);
      setToken(data.access_token);
      setAuthPassword("");
    } catch (err) {
      setAuthError(err.message);
    } finally {
      setAuthLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setAuthError("");
    setAuthSuccess("");

    if (!authName.trim() || !authEmail.trim() || !authPassword.trim()) {
      setAuthError("All fields are required.");
      return;
    }
    if (authPassword.length < 8) {
      setAuthError("Password must be at least 8 characters long.");
      return;
    }

    setAuthLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: authName.trim(),
          email: authEmail.trim(),
          password: authPassword,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Registration failed.");
      }

      setAuthSuccess("Registration successful! Please sign in with your credentials.");
      setAuthMode("login");
      setAuthPassword("");
    } catch (err) {
      setAuthError(err.message);
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    setToken("");
    setCurrentUser(null);
    setConversations([]);
    setCurrentConversationId(null);
    setMessages([]);
    setDocuments([]);
  };

  // ----------------------------------------------------
  // Conversation Handlers
  // ----------------------------------------------------
  const startNewChat = () => {
    setCurrentConversationId(null);
    setMessages([]);
    setChatError("");
    setQuestion("");
    setSidebarOpen(false);
    // Keep pending attachedDocuments if any were selected/uploaded
  };

  const selectConversation = async (convId) => {
    setCurrentConversationId(convId);
    setChatError("");
    setSidebarOpen(false);
    try {
      const res = await fetch(`${API_BASE_URL}/api/conversations/${convId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setMessages(data.messages || []);
        setAttachedDocuments(data.attached_documents || []);
      } else {
        const errData = await res.json().catch(() => null);
        setChatError(errData?.detail || `Failed to load conversation history (Status ${res.status}).`);
      }
    } catch (err) {
      setChatError("Network connection issue while loading conversation history.");
    }
  };

  const deleteConversation = async (e, convId) => {
    e.stopPropagation();
    try {
      const res = await fetch(`${API_BASE_URL}/api/conversations/${convId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        if (currentConversationId === convId) {
          startNewChat();
        }
        loadConversations();
      }
    } catch (err) {
      console.error("Error deleting conversation:", err);
    }
  };

  const handleAttachDocument = async (doc) => {
    if (attachedDocuments.some((d) => d.id === doc.id)) return;

    if (currentConversationId) {
      try {
        const res = await fetch(`${API_BASE_URL}/api/conversations/${currentConversationId}/documents`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ document_id: doc.id }),
        });
        if (res.ok) {
          const updated = await res.json();
          setAttachedDocuments(updated.attached_documents || []);
        }
      } catch (err) {
        console.error("Error attaching document:", err);
      }
    } else {
      // Pre-select document before conversation starts
      setAttachedDocuments((prev) => [...prev, doc]);
    }
    setShowAttachModal(false);
  };

  const handleDetachDocument = async (e, docId) => {
    e?.stopPropagation();
    if (currentConversationId) {
      try {
        const res = await fetch(`${API_BASE_URL}/api/conversations/${currentConversationId}/documents/${docId}`, {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const updated = await res.json();
          setAttachedDocuments(updated.attached_documents || []);
        }
      } catch (err) {
        console.error("Error detaching document:", err);
      }
    } else {
      setAttachedDocuments((prev) => prev.filter((d) => d.id !== docId));
    }
  };

  const handleAskQuestion = async (e) => {
    if (e) e.preventDefault();
    const cleanQuery = question.trim();
    if (!cleanQuery || asking) return;

    // Instantly append user message
    const tempUserMsg = {
      id: Date.now(),
      sender: "user",
      content: cleanQuery,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);
    setQuestion("");
    setAsking(true);
    setChatError("");

    try {
      const docIds = attachedDocuments.map((d) => d.id);
      const res = await fetch(`${API_BASE_URL}/api/ask/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          query: cleanQuery,
          conversation_id: currentConversationId,
          document_ids: docIds.length > 0 ? docIds : null,
          top_k: 5,
        }),
      });

      let data;
      try {
        data = await res.json();
      } catch {
        throw new Error(`Server returned status ${res.status}: Non-JSON response.`);
      }

      if (!res.ok) {
        throw new Error(data.detail || "Unable to generate an answer.");
      }

      // If new conversation was created on backend, track it
      if (!currentConversationId && data.conversation_id) {
        setCurrentConversationId(data.conversation_id);
      }

      const assistantMsg = {
        id: Date.now() + 1,
        sender: "assistant",
        content: data.answer,
        sources: data.sources || [],
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
      loadConversations();
    } catch (err) {
      setChatError(err.message || "An error occurred while answering.");
    } finally {
      setAsking(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleAskQuestion();
    }
  };

  // ----------------------------------------------------
  // Document Upload Handlers
  // ----------------------------------------------------
  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) {
      setSelectedFiles((prev) => [...prev, ...files]);
      setUploadNotification(null);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer.files || []);
    if (files.length > 0) {
      setSelectedFiles((prev) => [...prev, ...files]);
      setUploadNotification(null);
    }
  };

  const uploadAndProcessFiles = async () => {
    if (selectedFiles.length === 0) return;

    setUploading(true);
    setUploadNotification(null);

    const formData = new FormData();
    selectedFiles.forEach((file) => {
      formData.append("files", file);
    });

    try {
      const res = await fetch(`${API_BASE_URL}/api/documents/upload-multiple`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      let data;
      try {
        data = await res.json();
      } catch {
        throw new Error(`Server returned status ${res.status}.`);
      }

      if (!res.ok) {
        throw new Error(data.detail || "Failed to process documents.");
      }

      setUploadNotification({
        type: "success",
        text: data.message || "Documents uploaded and processed successfully.",
      });
      setSelectedFiles([]);
      
      // Refresh documents list from backend immediately
      const docsRes = await fetch(`${API_BASE_URL}/api/documents/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (docsRes.ok) {
        const freshDocs = await docsRes.json();
        setDocuments(freshDocs);

        // Find newly uploaded documents by checking matching filenames from selectedFiles
        const uploadedNames = selectedFiles.map((f) => f.name.toLowerCase());
        const newlyUploaded = freshDocs.filter((d) =>
          uploadedNames.includes((d.filename || "").toLowerCase())
        );

        if (newlyUploaded.length > 0) {
          if (currentConversationId) {
            // Associate them with the current active conversation
            for (const doc of newlyUploaded) {
              await fetch(`${API_BASE_URL}/api/conversations/${currentConversationId}/documents`, {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                  Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({ document_id: doc.id }),
              });
            }
            // Refresh conversation details
            const convRes = await fetch(`${API_BASE_URL}/api/conversations/${currentConversationId}`, {
              headers: { Authorization: `Bearer ${token}` },
            });
            if (convRes.ok) {
              const convData = await convRes.json();
              setAttachedDocuments(convData.attached_documents || []);
            }
          } else {
            // Pre-select the newly uploaded documents for the next conversation
            setAttachedDocuments((prev) => {
              const map = new Map(prev.map((item) => [item.id, item]));
              newlyUploaded.forEach((doc) => map.set(doc.id, doc));
              return Array.from(map.values());
            });
          }
        }
      }
    } catch (err) {
      setUploadNotification({
        type: "error",
        text: err.message || "Failed to upload and process files.",
      });
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteDocument = async (docId) => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/documents/${docId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        // Remove from attached documents if present
        setAttachedDocuments((prev) => prev.filter((d) => d.id !== docId));
        loadDocuments();
      }
    } catch (err) {
      console.error("Error deleting document:", err);
    }
  };

  // ====================================================
  // 1. WELCOME & AUTH SCREEN (If Not Authenticated)
  // ====================================================
  if (!token || !currentUser) {
    return (
      <div className="auth-wrapper">
        <div className="auth-card">
          <div className="auth-brand">
            <div className="brand-icon-large">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2a10 10 0 1 0 10 10H12V2z"></path>
                <path d="M12 12 2.1 12.9"></path>
                <path d="M12 12 16.5 3.5"></path>
              </svg>
            </div>
            <h1>MemoraAI</h1>
            <p>Your AI-Powered Personal Knowledge Intelligence Platform</p>
          </div>

          <div className="auth-tabs">
            <button
              className={`auth-tab ${authMode === "login" ? "active" : ""}`}
              onClick={() => {
                setAuthMode("login");
                setAuthError("");
                setAuthSuccess("");
              }}
            >
              Sign In
            </button>
            <button
              className={`auth-tab ${authMode === "register" ? "active" : ""}`}
              onClick={() => {
                setAuthMode("register");
                setAuthError("");
                setAuthSuccess("");
              }}
            >
              Register
            </button>
          </div>

          {authError && (
            <div className="alert-banner error">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
              <span>{authError}</span>
            </div>
          )}

          {authSuccess && (
            <div className="alert-banner success">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
              <span>{authSuccess}</span>
            </div>
          )}

          {authMode === "login" ? (
            <form className="auth-form" onSubmit={handleLogin}>
              <div className="form-group">
                <label className="form-label">Email Address</label>
                <input
                  type="email"
                  className="form-input"
                  placeholder="name@example.com"
                  value={authEmail}
                  onChange={(e) => setAuthEmail(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Password</label>
                <div className="input-container">
                  <input
                    type={showPassword ? "text" : "password"}
                    className="form-input"
                    placeholder="Enter password"
                    value={authPassword}
                    onChange={(e) => setAuthPassword(e.target.value)}
                    required
                  />
                  <button
                    type="button"
                    className="password-toggle"
                    onClick={() => setShowPassword(!showPassword)}
                    tabIndex="-1"
                  >
                    {showPassword ? (
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>
                    ) : (
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                    )}
                  </button>
                </div>
              </div>

              <button type="submit" className="btn-primary" disabled={authLoading}>
                {authLoading ? "Signing In..." : "Sign In to MemoraAI"}
              </button>

              <p className="auth-footer-text">
                Don't have an account?
                <button
                  type="button"
                  className="auth-link"
                  onClick={() => {
                    setAuthMode("register");
                    setAuthError("");
                    setAuthSuccess("");
                  }}
                >
                  Create one now
                </button>
              </p>
            </form>
          ) : (
            <form className="auth-form" onSubmit={handleRegister}>
              <div className="form-group">
                <label className="form-label">Full Name</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Alex Johnson"
                  value={authName}
                  onChange={(e) => setAuthName(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Email Address</label>
                <input
                  type="email"
                  className="form-input"
                  placeholder="name@example.com"
                  value={authEmail}
                  onChange={(e) => setAuthEmail(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Password (min 8 characters)</label>
                <div className="input-container">
                  <input
                    type={showPassword ? "text" : "password"}
                    className="form-input"
                    placeholder="Create a strong password"
                    value={authPassword}
                    onChange={(e) => setAuthPassword(e.target.value)}
                    required
                  />
                  <button
                    type="button"
                    className="password-toggle"
                    onClick={() => setShowPassword(!showPassword)}
                    tabIndex="-1"
                  >
                    {showPassword ? (
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>
                    ) : (
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                    )}
                  </button>
                </div>
              </div>

              <button type="submit" className="btn-primary" disabled={authLoading}>
                {authLoading ? "Registering..." : "Create Account"}
              </button>

              <p className="auth-footer-text">
                Already registered?
                <button
                  type="button"
                  className="auth-link"
                  onClick={() => {
                    setAuthMode("login");
                    setAuthError("");
                    setAuthSuccess("");
                  }}
                >
                  Sign In
                </button>
              </p>
            </form>
          )}
        </div>
      </div>
    );
  }

  // ====================================================
  // 2. AUTHENTICATED DASHBOARD (Two-Panel Layout)
  // ====================================================
  const activeConversation = conversations.find((c) => c.id === currentConversationId);
  const initials = currentUser?.name
    ? currentUser.name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : "U";

  return (
    <div className="memora-app">
      {/* Mobile Backdrop */}
      {sidebarOpen && (
        <div
          className="sidebar-backdrop"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* ----------------------------------------------
          LEFT SIDEBAR
          ---------------------------------------------- */}
      <aside className={`dashboard-sidebar ${sidebarOpen ? "open" : ""}`}>
        <div className="sidebar-header">
          <div className="brand-wrapper">
            <div className="brand-icon-small">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2a10 10 0 1 0 10 10H12V2z"></path>
                <path d="M12 12 2.1 12.9"></path>
              </svg>
            </div>
            <span className="brand-title">MemoraAI</span>
          </div>

          <button
            className="mobile-menu-btn"
            onClick={() => setSidebarOpen(false)}
            title="Close menu"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>

        <div className="sidebar-action-bar">
          <button className="new-chat-btn" onClick={startNewChat}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
            New Chat
          </button>

          <button
            className="sidebar-nav-btn"
            onClick={() => setShowDocsModal(true)}
          >
            <span style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
              My Documents
            </span>
            <span className="nav-badge">{documents.length}</span>
          </button>
        </div>

        <div className="sidebar-section-title">Chat History</div>

        <div className="conversation-list">
          {conversations.length === 0 ? (
            <div className="empty-history-text">
              No previous chats yet.<br />Ask a question to start one.
            </div>
          ) : (
            conversations.map((conv) => (
              <div
                key={conv.id}
                className={`conversation-item ${
                  currentConversationId === conv.id ? "active" : ""
                }`}
                onClick={() => selectConversation(conv.id)}
              >
                <div className="conversation-title-text" title={conv.title}>
                  {conv.title}
                </div>
                <button
                  className="delete-conv-btn"
                  onClick={(e) => deleteConversation(e, conv.id)}
                  title="Delete chat"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                </button>
              </div>
            ))
          )}
        </div>

        {/* User Profile Area */}
        <div className="sidebar-user-footer">
          <div className="user-profile-info">
            <div className="user-avatar">{initials}</div>
            <div className="user-name-col">
              <span className="user-display-name">{currentUser.name}</span>
              <span className="user-display-email">{currentUser.email}</span>
            </div>
          </div>
          <button
            className="logout-btn"
            onClick={handleLogout}
            title="Log out"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
          </button>
        </div>
      </aside>

      {/* ----------------------------------------------
          MAIN CONTENT AREA
          ---------------------------------------------- */}
      <main className="dashboard-main">
        {/* Top Navbar */}
        <header className="main-topbar">
          <div className="topbar-left">
            <button
              className="mobile-menu-btn"
              onClick={() => setSidebarOpen(true)}
              title="Open menu"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>
            </button>
            <div className="topbar-title-wrap">
              <h2 className="topbar-title">
                {activeConversation ? activeConversation.title : "Your knowledge, one conversation away."}
              </h2>
              {attachedDocuments.length > 0 && (
                <div className="topbar-attached-badge" title="Attached documents for this conversation">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path></svg>
                  <span>{attachedDocuments.length} doc{attachedDocuments.length > 1 ? "s" : ""} attached</span>
                </div>
              )}
            </div>
          </div>

          <div className="topbar-right">
            <button
              className="topbar-action-btn"
              onClick={() => {
                setShowUploadModal(true);
                setUploadNotification(null);
              }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
              Upload Documents
            </button>
          </div>
        </header>

        {/* Chat Scroll Area */}
        <div className="chat-scroll-container">
          <div className="chat-content-width">
            {messages.length === 0 ? (
              <div className="empty-chat-welcome">
                <div className="welcome-icon-box">
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg>
                </div>
                <h2>Your knowledge, one conversation away.</h2>
                <p>
                  Ask questions, explore concepts, and follow up in natural language.
                  MemoraAI provides clear, structured explanations grounded directly in your uploaded documents.
                </p>

                <div className="starter-prompts-grid">
                  <div
                    className="starter-prompt-card"
                    onClick={() => {
                      setQuestion("Summarize the key concepts and definitions from my documents.");
                      textareaRef.current?.focus();
                    }}
                  >
                    <strong>Summarize Core Concepts</strong>
                    <span>Extract key definitions and main takeaways.</span>
                  </div>

                  <div
                    className="starter-prompt-card"
                    onClick={() => {
                      setQuestion("Explain the differences between the main algorithms or methods mentioned.");
                      textareaRef.current?.focus();
                    }}
                  >
                    <strong>Compare Methods</strong>
                    <span>Analyze advantages, disadvantages, and trade-offs.</span>
                  </div>

                  <div
                    className="starter-prompt-card"
                    onClick={() => {
                      setQuestion("What are the most important formulas, rules, or steps to remember?");
                      textareaRef.current?.focus();
                    }}
                  >
                    <strong>Quick Study Guide</strong>
                    <span>Review essential points, steps, and formulas.</span>
                  </div>
                </div>
              </div>
            ) : (
              messages.map((msg, index) => (
                <div
                  key={msg.id}
                  className={`message-row ${msg.sender === "user" ? "user" : "assistant"}`}
                >
                  {msg.sender === "user" ? (
                    <div className="user-message-wrapper">
                      {/* If this is the first user message or conversation has attached documents, display compact attachment card */}
                      {index === 0 && attachedDocuments.length > 0 && (
                        <div className="chat-attachments-container">
                          {attachedDocuments.map((doc) => (
                            <div className="chat-attachment-chip" key={doc.id}>
                              <span className="attachment-icon">
                                {doc.file_type === "pdf" ? "📕" : doc.file_type === "docx" ? "📘" : "📄"}
                              </span>
                              <span className="attachment-name" title={doc.filename}>{doc.filename}</span>
                              <button
                                className="attachment-remove-btn"
                                onClick={(e) => handleDetachDocument(e, doc.id)}
                                title="Detach document"
                              >
                                &times;
                              </button>
                            </div>
                          ))}
                        </div>
                      )}
                      <div className="message-bubble-user">{msg.content}</div>
                    </div>
                  ) : (
                    <div className="message-card-assistant">
                      <div className="assistant-header">
                        <div className="brand-icon-small" style={{ width: 22, height: 22, borderRadius: 6 }}>
                          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M12 2a10 10 0 1 0 10 10H12V2z"></path></svg>
                        </div>
                        <span className="assistant-badge">MemoraAI</span>
                      </div>

                      <div className="markdown-body">
                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                      </div>

                      {msg.sources && msg.sources.length > 0 && (
                        <div className="sources-footer">
                          <span className="sources-label">Sources:</span>
                          {msg.sources.map((src, idx) => (
                            <span className="source-pill" key={idx}>
                              📄 {src.filename}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))
            )}

            {asking && (
              <div className="message-row assistant">
                <div className="thinking-box">
                  <div className="typing-dots">
                    <span className="typing-dot"></span>
                    <span className="typing-dot"></span>
                    <span className="typing-dot"></span>
                  </div>
                  <span>MemoraAI is reading your documents and drafting an answer...</span>
                </div>
              </div>
            )}

            {chatError && (
              <div className="alert-banner error" style={{ width: "100%" }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                <span>{chatError}</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Bottom Question Input Bar */}
        <div className="bottom-input-wrapper">
          {/* Active Attached Documents Pills in Input Tray */}
          {attachedDocuments.length > 0 && (
            <div className="input-attachments-tray">
              <span className="tray-label">Attached:</span>
              {attachedDocuments.map((doc) => (
                <div className="input-attached-pill" key={doc.id}>
                  <span>{doc.file_type === "pdf" ? "📕" : doc.file_type === "docx" ? "📘" : "📄"}</span>
                  <span className="pill-name" title={doc.filename}>{doc.filename}</span>
                  <button
                    type="button"
                    className="pill-close"
                    onClick={(e) => handleDetachDocument(e, doc.id)}
                    title="Remove attachment"
                  >
                    &times;
                  </button>
                </div>
              ))}
            </div>
          )}

          <form className="input-box-container" onSubmit={handleAskQuestion}>
            <button
              type="button"
              className="attach-button"
              onClick={() => setShowAttachModal(true)}
              title="Attach document from library"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path></svg>
            </button>

            <textarea
              ref={textareaRef}
              className="chat-textarea"
              placeholder={
                messages.length > 0
                  ? "Ask a follow-up question..."
                  : "Ask something about your uploaded documents..."
              }
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
              disabled={asking}
            />

            <button
              type="submit"
              className="send-question-btn"
              disabled={!question.trim() || asking}
              title="Send message"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
            </button>
          </form>
          <div className="input-footer-hint">
            Press Enter to send, Shift+Enter for new line. Grounded exclusively in your documents.
          </div>
        </div>
      </main>

      {/* ----------------------------------------------
          MODAL 1: UPLOAD DOCUMENTS / FOLDERS
          ---------------------------------------------- */}
      {showUploadModal && (
        <div className="modal-overlay" onClick={() => setShowUploadModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Upload Documents & Folders</h3>
              <button
                className="modal-close-btn"
                onClick={() => setShowUploadModal(false)}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
              </button>
            </div>

            <div className="modal-body">
              {uploadNotification && (
                <div className={`alert-banner ${uploadNotification.type}`}>
                  <span>{uploadNotification.text}</span>
                </div>
              )}

              <div
                className="upload-dropzone"
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleDrop}
              >
                <svg className="dropzone-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                  <polyline points="17 8 12 3 7 8"></polyline>
                  <line x1="12" y1="3" x2="12" y2="15"></line>
                </svg>

                <div className="dropzone-title">Upload documents or select a folder</div>
                <div className="dropzone-subtitle">
                  Supported formats: PDF, DOCX, TXT. Automatically saved to My Documents.
                </div>

                <div className="dropzone-buttons">
                  <label className="dropzone-file-btn">
                    📄 Choose Files
                    <input
                      type="file"
                      accept=".pdf,.docx,.txt"
                      multiple
                      onChange={handleFileSelect}
                    />
                  </label>

                  <label className="dropzone-file-btn">
                    📁 Choose Folder
                    <input
                      type="file"
                      webkitdirectory=""
                      directory=""
                      multiple
                      onChange={handleFileSelect}
                    />
                  </label>
                </div>
              </div>

              {selectedFiles.length > 0 && (
                <div className="selected-files-box">
                  <div className="selected-files-header">
                    <span>Selected Items ({selectedFiles.length})</span>
                    <button
                      type="button"
                      style={{ fontSize: 12, color: "var(--primary)", fontWeight: 600 }}
                      onClick={() => setSelectedFiles([])}
                    >
                      Clear All
                    </button>
                  </div>
                  <div className="selected-files-list">
                    {selectedFiles.map((file, idx) => (
                      <div className="selected-file-row" key={`${file.name}-${idx}`}>
                        <span className="selected-file-name">
                          {file.webkitRelativePath || file.name}
                        </span>
                        <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
                          {(file.size / 1024).toFixed(0)} KB
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <button
                className="btn-primary"
                onClick={uploadAndProcessFiles}
                disabled={uploading || selectedFiles.length === 0}
              >
                {uploading ? "Processing Documents..." : "Upload and Process"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ----------------------------------------------
          MODAL 2: MY DOCUMENTS
          ---------------------------------------------- */}
      {showDocsModal && (
        <div className="modal-overlay" onClick={() => setShowDocsModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <h3>My Documents</h3>
                <span className="nav-badge">{documents.length}</span>
              </div>
              <button
                className="modal-close-btn"
                onClick={() => setShowDocsModal(false)}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
              </button>
            </div>

            <div className="modal-body">
              {documents.length === 0 ? (
                <div className="empty-history-text">
                  You haven't uploaded any documents yet.
                </div>
              ) : (
                <div className="docs-list-container">
                  {documents.map((doc) => {
                    const isAttached = attachedDocuments.some((d) => d.id === doc.id);
                    return (
                      <div className="doc-list-item" key={doc.id}>
                        <div className="doc-info-col">
                          <span className="doc-type-icon">
                            {doc.file_type === "pdf" ? "📕" : doc.file_type === "docx" ? "📘" : "📄"}
                          </span>
                          <div>
                            <div className="doc-name" title={doc.filename}>{doc.filename}</div>
                            <div className="doc-date">
                              {new Date(doc.created_at).toLocaleDateString(undefined, {
                                year: "numeric",
                                month: "short",
                                day: "numeric",
                              })} &bull; Status: <span style={{ color: "var(--secondary)", fontWeight: 600 }}>Processed</span>
                            </div>
                          </div>
                        </div>

                        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                          <button
                            className={`doc-attach-action-btn ${isAttached ? "attached" : ""}`}
                            onClick={() => {
                              if (isAttached) {
                                handleDetachDocument(null, doc.id);
                              } else {
                                handleAttachDocument(doc);
                              }
                            }}
                          >
                            {isAttached ? "✓ Attached" : "+ Attach to Chat"}
                          </button>

                          <button
                            className="delete-doc-btn"
                            onClick={() => handleDeleteDocument(doc.id)}
                            title="Delete document"
                          >
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              <button
                className="btn-primary"
                onClick={() => {
                  setShowDocsModal(false);
                  setShowUploadModal(true);
                }}
              >
                Upload More Documents
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ----------------------------------------------
          MODAL 3: ATTACH DOCUMENT FROM LIBRARY
          ---------------------------------------------- */}
      {showAttachModal && (
        <div className="modal-overlay" onClick={() => setShowAttachModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Attach Document to Chat</h3>
              <button
                className="modal-close-btn"
                onClick={() => setShowAttachModal(false)}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
              </button>
            </div>

            <div className="modal-body">
              {documents.length === 0 ? (
                <div className="empty-history-text">
                  No documents found in your library.<br />Please upload documents first.
                </div>
              ) : (
                <div className="docs-list-container">
                  {documents.map((doc) => {
                    const isAttached = attachedDocuments.some((d) => d.id === doc.id);
                    return (
                      <div className="doc-list-item" key={doc.id}>
                        <div className="doc-info-col">
                          <span className="doc-type-icon">
                            {doc.file_type === "pdf" ? "📕" : doc.file_type === "docx" ? "📘" : "📄"}
                          </span>
                          <div>
                            <div className="doc-name" title={doc.filename}>{doc.filename}</div>
                            <div className="doc-date">
                              {new Date(doc.created_at).toLocaleDateString(undefined, {
                                year: "numeric",
                                month: "short",
                                day: "numeric",
                              })}
                            </div>
                          </div>
                        </div>

                        <button
                          className={`doc-attach-action-btn ${isAttached ? "attached" : ""}`}
                          onClick={() => {
                            if (isAttached) {
                              handleDetachDocument(null, doc.id);
                            } else {
                              handleAttachDocument(doc);
                            }
                          }}
                        >
                          {isAttached ? "✓ Attached" : "Attach"}
                        </button>
                      </div>
                    );
                  })}
                </div>
              )}

              <button
                className="btn-primary"
                onClick={() => {
                  setShowAttachModal(false);
                  setShowUploadModal(true);
                }}
              >
                Upload New Document
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}