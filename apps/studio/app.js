const output = document.getElementById("output");

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
