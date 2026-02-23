const output = document.getElementById("output");
const templates = {
  python_none: {
    language: "python",
    error_log: "Traceback (most recent call last):\n  File \"app.py\", line 14, in run\n    result = process(data)\nTypeError: 'NoneType' object is not subscriptable",
    code: "def process(data):\n    return data['id']\n\ndef run(data):\n    result = process(data)\n    return result",
  },
  js_undefined: {
    language: "javascript",
    error_log: "TypeError: Cannot read properties of undefined (reading 'id')\n    at getUserId (index.js:5:18)",
    code: "function getUserId(user) {\n  return user.profile.id;\n}\n\nmodule.exports = { getUserId };",
  },
  timeout_retry: {
    language: "python",
    error_log: "Request failed after 1 attempt: timeout=5s\nServiceUnavailableError",
    code: "import requests\n\ndef fetch(url):\n    resp = requests.get(url, timeout=5)\n    resp.raise_for_status()\n    return resp.json()",
  },
};

async function post(path, payload) {
  const apiUrl = document.getElementById("apiUrl").value.trim();
  const res = await fetch(`${apiUrl}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed (${res.status})`);
  }

  return res.json();
}

function collect() {
  return {
    language: document.getElementById("language").value,
    error_log: document.getElementById("errorLog").value.trim(),
    code: document.getElementById("code").value.trim(),
    strategy: document.getElementById("strategy").value,
  };
}

document.getElementById("templateSelect").addEventListener("change", (event) => {
  const key = event.target.value;
  if (!key || !templates[key]) {
    return;
  }
  const sample = templates[key];
  document.getElementById("language").value = sample.language;
  document.getElementById("errorLog").value = sample.error_log;
  document.getElementById("code").value = sample.code;
});

document.getElementById("copyBtn").addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(output.textContent || "");
    const prev = output.textContent;
    output.textContent = "Copied current output to clipboard.";
    setTimeout(() => {
      output.textContent = prev;
    }, 1000);
  } catch {
    output.textContent = "Clipboard access failed. Copy manually.";
  }
});

document.getElementById("analyzeBtn").addEventListener("click", async () => {
  const data = collect();
  if (!data.error_log || !data.code) {
    output.textContent = "Please provide both error log and code.";
    return;
  }

  output.textContent = "Running analysis...";
  try {
    const res = await post("/api/v1/analyze", {
      language: data.language,
      error_log: data.error_log,
      code: data.code,
    });

    output.textContent = [
      `Severity: ${res.severity}`,
      `Confidence: ${res.confidence}`,
      `Provider: ${res.provider}`,
      "",
      "Root Cause:",
      res.root_cause,
    ].join("\n");
  } catch (err) {
    output.textContent = `Error: ${err.message}`;
  }
});

document.getElementById("repairBtn").addEventListener("click", async () => {
  const data = collect();
  if (!data.error_log || !data.code) {
    output.textContent = "Please provide both error log and code.";
    return;
  }

  output.textContent = "Generating patch...";
  try {
    const res = await post("/api/v1/repair", data);
    output.textContent = [
      `Provider: ${res.provider}`,
      "",
      "Patch:",
      res.patch,
      "",
      "Explanation:",
      res.explanation,
      "",
      "Tests to add:",
      ...res.tests_to_add.map((t, i) => `${i + 1}. ${t}`),
    ].join("\n");
  } catch (err) {
    output.textContent = `Error: ${err.message}`;
  }
});
