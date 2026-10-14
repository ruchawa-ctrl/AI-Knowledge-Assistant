const BASE = "/api";

async function handle(res) {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch (_) {}
    throw new Error(detail);
  }
  return res.json();
}

export const api = {
  listDocuments: () => fetch(`${BASE}/documents`).then(handle),

  uploadDocument: (file) => {
    const form = new FormData();
    form.append("file", file);
    return fetch(`${BASE}/documents`, { method: "POST", body: form }).then(handle);
  },

  deleteDocument: (id) =>
    fetch(`${BASE}/documents/${id}`, { method: "DELETE" }).then(handle),

  chat: (message) =>
    fetch(`${BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    }).then(handle),

  // Streams NDJSON events: {type:"sources"|"token"|"error"|"done", ...}
  chatStream: async (message, { onSources, onToken, onError }) => {
    const res = await fetch(`${BASE}/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    if (!res.ok || !res.body) {
      throw new Error(`Request failed (${res.status})`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";
      for (const line of lines) {
        if (!line.trim()) continue;
        let evt;
        try {
          evt = JSON.parse(line);
        } catch (_) {
          continue;
        }
        if (evt.type === "sources") onSources?.(evt.sources);
        else if (evt.type === "token") onToken?.(evt.text);
        else if (evt.type === "error") onError?.(evt.detail);
      }
    }
  },

  history: () => fetch(`${BASE}/chat/history`).then(handle),

  clearHistory: () =>
    fetch(`${BASE}/chat/history`, { method: "DELETE" }).then(handle),
};
