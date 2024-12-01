// Test
async function sendQuery() {
  const query = document.getElementById("query").value;
  const codebase = document.getElementById("codebase").value;
  const responseBox = document.getElementById("response");

  responseBox.innerHTML = "Processing...";
  if (!query.trim()) {
    responseBox.innerHTML = "<strong>Error:</strong> Query cannot be empty.";
    return;
  }

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, codebase }),
    });

    if (response.ok) {
      const data = await response.json();
      responseBox.innerHTML = `<strong>Response:</strong> ${data.response}`;
    } else {
      responseBox.innerHTML =
        "<strong>Error:</strong> Unable to fetch response.";
    }
  } catch (error) {
    responseBox.innerHTML = `<strong>Error:</strong> ${error.message}`;
  }
}
