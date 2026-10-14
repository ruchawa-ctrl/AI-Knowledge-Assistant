import { useEffect, useRef, useState } from "react";
import { api } from "./api";
import Sidebar from "./components/Sidebar";
import Message from "./components/Message";

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [uploading, setUploading] = useState(false);
  const [thinking, setThinking] = useState(false);
  const [error, setError] = useState("");
  const scrollRef = useRef(null);

  useEffect(() => {
    refreshDocuments();
    api.history().then(setMessages).catch(() => {});
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages, thinking]);

  function refreshDocuments() {
    api.listDocuments().then(setDocuments).catch(() => {});
  }

  async function handleUpload(file) {
    setUploading(true);
    try {
      await api.uploadDocument(file);
      refreshDocuments();
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(id) {
    await api.deleteDocument(id).catch(() => {});
    refreshDocuments();
  }

  async function send() {
    const text = input.trim();
    if (!text || thinking) return;
    setError("");
    setInput("");
    setMessages((m) => [...m, { role: "user", content: text }]);
    setThinking(true);

    // Placeholder assistant message we fill in as tokens stream in.
    const assistantIndex = messages.length + 1;
    let started = false;
    const patch = (fn) =>
      setMessages((m) => {
        const next = [...m];
        next[assistantIndex] = fn(next[assistantIndex] || {
          role: "assistant",
          content: "",
          sources: [],
        });
        return next;
      });

    try {
      await api.chatStream(text, {
        onSources: (sources) => {
          patch((msg) => ({ ...msg, sources }));
        },
        onToken: (token) => {
          if (!started) {
            started = true;
            setThinking(false);
          }
          patch((msg) => ({ ...msg, content: (msg.content || "") + token }));
        },
        onError: (detail) => {
          patch((msg) => ({ ...msg, content: `⚠️ ${detail}` }));
        },
      });
    } catch (err) {
      setError(err.message);
      patch((msg) => ({ ...msg, content: `⚠️ ${err.message}` }));
    } finally {
      setThinking(false);
    }
  }

  async function clearChat() {
    await api.clearHistory().catch(() => {});
    setMessages([]);
  }

  function onKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  return (
    <div className="app">
      <Sidebar
        documents={documents}
        onUpload={handleUpload}
        onDelete={handleDelete}
        uploading={uploading}
      />

      <main className="chat">
        <header className="chat-header">
          <div>
            <h2>AI Knowledge Assistant</h2>
            <p>Ask questions grounded in your own documents.</p>
          </div>
          <button className="ghost-btn" onClick={clearChat}>
            Clear chat
          </button>
        </header>

        <div className="messages" ref={scrollRef}>
          {messages.length === 0 && (
            <div className="welcome">
              <h3>Welcome</h3>
              <p>
                Upload documents on the left, then ask anything. Answers are
                generated only from your indexed content, with sources.
              </p>
            </div>
          )}
          {messages.map((m, i) => (
            <Message key={i} role={m.role} content={m.content} sources={m.sources} />
          ))}
          {thinking && (
            <div className="msg msg-assistant">
              <div className="msg-role">Assistant</div>
              <div className="typing">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          )}
        </div>

        {error && <div className="banner-error">{error}</div>}

        <div className="composer">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Ask a question about your documents…"
            rows={1}
          />
          <button onClick={send} disabled={thinking || !input.trim()}>
            Send
          </button>
        </div>
      </main>
    </div>
  );
}
