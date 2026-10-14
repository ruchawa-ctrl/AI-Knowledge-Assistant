import { useRef, useState } from "react";

export default function Sidebar({ documents, onUpload, onDelete, uploading }) {
  const fileRef = useRef(null);
  const [error, setError] = useState("");

  async function handleFile(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setError("");
    try {
      await onUpload(file);
    } catch (err) {
      setError(err.message);
    } finally {
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="brand-dot" />
        <h1>Knowledge Base</h1>
      </div>

      <button
        className="upload-btn"
        onClick={() => fileRef.current?.click()}
        disabled={uploading}
      >
        {uploading ? "Indexing…" : "+ Add document"}
      </button>
      <input
        ref={fileRef}
        type="file"
        accept=".pdf,.txt,.md,.csv"
        onChange={handleFile}
        hidden
      />
      {error && <p className="error">{error}</p>}

      <div className="doc-list">
        {documents.length === 0 && (
          <p className="empty">No documents yet. Upload a PDF or text file to start.</p>
        )}
        {documents.map((d) => (
          <div className="doc-item" key={d.id}>
            <div className="doc-meta">
              <span className="doc-name" title={d.filename}>
                {d.filename}
              </span>
              <span className="doc-sub">{d.num_chunks} chunks</span>
            </div>
            <button className="doc-del" onClick={() => onDelete(d.id)} title="Delete">
              ×
            </button>
          </div>
        ))}
      </div>

      <footer className="sidebar-foot">RAG · FastAPI · Chroma</footer>
    </aside>
  );
}
