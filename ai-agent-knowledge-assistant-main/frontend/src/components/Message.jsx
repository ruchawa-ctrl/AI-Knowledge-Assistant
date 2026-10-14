export default function Message({ role, content, sources }) {
  const isUser = role === "user";
  return (
    <div className={`msg ${isUser ? "msg-user" : "msg-assistant"}`}>
      <div className="msg-role">{isUser ? "You" : "Assistant"}</div>
      <div className="msg-body">{content}</div>
      {!isUser && sources && sources.length > 0 && (
        <div className="sources">
          <div className="sources-title">Sources</div>
          {sources.map((s, i) => (
            <div className="source" key={`${s.document_id}-${s.chunk_index}-${i}`}>
              <span className="source-tag">[{i + 1}]</span>
              <span className="source-file">{s.filename}</span>
              <span className="source-score">{Math.round(s.score * 100)}%</span>
              <p className="source-snippet">{s.snippet}…</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
