import { useEffect, useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [message, setMessage] = useState(
    "Connecting to MemoraAI backend..."
  );

  const [token, setToken] = useState(
    localStorage.getItem("access_token") || ""
  );

  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadResults, setUploadResults] = useState([]);

  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState([]);
  const [asking, setAsking] = useState(false);

  useEffect(() => {
    fetch(`${API_URL}/api/health`)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error: ${response.status}`);
        }

        return response.json();
      })
      .then((data) => {
        setMessage(`${data.status} - ${data.service}`);
      })
      .catch((error) => {
        console.error("Backend connection error:", error);
        setMessage("Backend connection failed");
      });
  }, []);

  const handleTokenChange = (event) => {
    const value = event.target.value;

    setToken(value);
    localStorage.setItem("access_token", value);
  };

  const handleFileSelection = (event) => {
    const files = Array.from(event.target.files || []);

    setSelectedFiles(files);
    setUploadResults([]);
  };

  const uploadFiles = async () => {
    if (!token.trim()) {
      setMessage("Please enter your JWT token first.");
      return;
    }

    if (selectedFiles.length === 0) {
      setMessage("Please select at least one file.");
      return;
    }

    setUploading(true);
    setUploadResults([]);
    setMessage("Uploading and processing files...");

    const results = [];

    for (const file of selectedFiles) {
      const formData = new FormData();
      formData.append("file", file);

      try {
        const response = await fetch(
          `${API_URL}/api/documents/upload`,
          {
            method: "POST",
            headers: {
              Authorization: `Bearer ${token}`,
            },
            body: formData,
          }
        );

        const data = await response.json();

        if (!response.ok) {
          results.push({
            filename: file.name,
            status: "failed",
            message: data.detail || "Upload failed",
          });
        } else {
          results.push({
            filename: file.name,
            status: "success",
            message: `Processed ${data.chunks_created} chunks`,
          });
        }
      } catch (error) {
        results.push({
          filename: file.name,
          status: "failed",
          message: error.message,
        });
      }

      setUploadResults([...results]);
    }

    setUploading(false);
    setMessage("File processing completed.");
  };

  const askQuestion = async () => {
    if (!token.trim()) {
      setMessage("Please enter your JWT token first.");
      return;
    }

    if (!question.trim()) {
      setMessage("Please enter a question.");
      return;
    }

    setAsking(true);
    setAnswer("");
    setSources([]);
    setMessage("Searching your knowledge and generating an answer...");

    try {
      const response = await fetch(`${API_URL}/api/ask/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          query: question,
          top_k: 5,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Unable to get an answer.");
      }

      setAnswer(data.answer);
      setSources(data.sources || []);
      setMessage("Answer generated successfully.");
    } catch (error) {
      console.error("Ask MemoraAI error:", error);
      setMessage(error.message);
    } finally {
      setAsking(false);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>MemoraAI</h1>
          <p>AI-Powered Personal Knowledge Intelligence Platform</p>
        </div>

        <div className="status">
          <span className="status-dot"></span>
          {message}
        </div>
      </header>

      <main className="container">
        <section className="card">
          <h2>Connect to MemoraAI</h2>

          <p className="description">
            Enter the JWT access token generated after logging in through the
            backend.
          </p>

          <input
            type="password"
            className="token-input"
            placeholder="Paste JWT access token"
            value={token}
            onChange={handleTokenChange}
          />
        </section>

        <section className="card">
          <h2>Add Your Knowledge</h2>

          <p className="description">
            Upload individual documents or select an entire folder.
            Supported formats: PDF, DOCX and TXT.
          </p>

          <div className="upload-options">
            <label className="upload-button">
              📄 Choose File
              <input
                type="file"
                accept=".pdf,.docx,.txt"
                multiple
                onChange={handleFileSelection}
              />
            </label>

            <label className="upload-button">
              📁 Choose Folder
              <input
                type="file"
                webkitdirectory=""
                directory=""
                multiple
                onChange={handleFileSelection}
              />
            </label>
          </div>

          {selectedFiles.length > 0 && (
            <div className="selected-section">
              <h3>
                Selected Files ({selectedFiles.length})
              </h3>

              <div className="file-list">
                {selectedFiles.map((file, index) => (
                  <div
                    className="file-item"
                    key={`${file.name}-${index}`}
                  >
                    <span>📄</span>

                    <div>
                      <strong>{file.name}</strong>

                      {file.webkitRelativePath && (
                        <small>{file.webkitRelativePath}</small>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              <button
                className="process-button"
                onClick={uploadFiles}
                disabled={uploading}
              >
                {uploading
                  ? "Processing..."
                  : "Upload & Process"}
              </button>
            </div>
          )}
        </section>

        {uploadResults.length > 0 && (
          <section className="card">
            <h2>Processing Results</h2>

            <div className="results">
              {uploadResults.map((result, index) => (
                <div
                  className={`result-item ${result.status}`}
                  key={`${result.filename}-${index}`}
                >
                  <div>
                    <strong>{result.filename}</strong>
                    <p>{result.message}</p>
                  </div>

                  <span>
                    {result.status === "success"
                      ? "✓"
                      : "✕"}
                  </span>
                </div>
              ))}
            </div>
          </section>
        )}

        <section className="card">
          <h2>Ask MemoraAI</h2>

          <p className="description">
            Ask questions about the knowledge stored in your documents.
            MemoraAI will retrieve relevant information and generate an
            AI-powered answer.
          </p>

          <textarea
            className="question-input"
            placeholder="Ask something about your documents..."
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                askQuestion();
              }
            }}
            rows="4"
          />

          <button
            className="process-button"
            onClick={askQuestion}
            disabled={asking}
          >
            {asking ? "Thinking..." : "Ask MemoraAI"}
          </button>
        </section>

        {answer && (
          <section className="card">
            <h2>Answer</h2>

            <div className="answer-box">
              <p>{answer}</p>
            </div>

            {sources.length > 0 && (
              <div className="sources-section">
                <h3>Sources</h3>

                <div className="results">
                  {sources.map((source, index) => (
                    <div
                      className="result-item success"
                      key={`${source.document_id}-${source.chunk_id}-${index}`}
                    >
                      <div className="source-content">
                        <strong>{source.filename}</strong>

                        <p>
                          Chunk {source.chunk_id} · Similarity:{" "}
                          {source.similarity.toFixed(4)}
                        </p>

                        <div className="source-snippet">
                          {source.content}
                        </div>
                      </div>

                      <span>📄</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>
        )}
      </main>
    </div>
  );
}

export default App;