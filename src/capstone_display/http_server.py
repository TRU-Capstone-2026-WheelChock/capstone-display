from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>HDAWCS Live Display</title>

  <style>
    * { box-sizing: border-box; }

    body {
      font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
      background-color: #f0f2f5;
      margin: 0;
      padding: 0;
      color: #333;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }

    /* HEADER */
    header {
      width: 100%;
      background-color: #48b39c; /* lighter teal */
      padding: 15px 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      min-height: 110px;
    }

    .header-title {
      display: flex;
      flex-direction: column;
      justify-content: center;
      flex: 1;
    }

    .header-title h1 {
      margin: 0;
      font-size: 2.1em;
      font-weight: 700;
      color: white;
    }

    .header-title h2 {
      margin: 5px 0 0 0;
      font-size: 0.75em;
      font-weight: 500;
      color: #000;
      line-height: 1.2;
      opacity: 0.85;
    }

    .header-right {
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      justify-content: center;
      gap: 5px;
      margin-left: 20px;
    }

    .header-right img {
      height: 40px;
      object-fit: contain;
    }

    /* MAIN CONTENT */
    main {
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      gap: 20px;
      padding: 20px;
    }

    .sensor-card {
      background-color: #fff;
      border-radius: 10px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.15);
      padding: 15px;
      display: flex;
      flex-direction: column;
      align-items: center;
      width: auto;
      min-width: 120px;
    }

    .sensor-title {
      font-weight: bold;
      margin-bottom: 8px;
      font-size: 1.1em;
      color: #264653;
      text-align: center;
    }

    .info-row {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      margin-top: 6px;
    }

    .label {
      font-weight: bold;
      font-size: 0.9em;
    }

    .value-box {
      padding: 4px 10px;
      border-radius: 5px;
      font-size: 0.9em;
      text-align: center;
      min-width: 80px;
    }

    .human-main {
      font-size: 1.1em;
      font-weight: bold;
      padding: 6px 12px;
    }

    /* COLORS */
    .active-true { background-color: #5dade2; color: #0b3c5d; }
    .active-false { background-color: #5a5a5a; color: #ffffff; }
    .human-true { background-color: #58d68d; color: #145a32; }
    .human-false { background-color: #ec7063; color: #641e16; }

    /* MAJORITY BOX */
    .majority-box {
      max-width: 400px;
      width: auto;
      margin: 20px auto 40px auto;
      background-color: #fff;
      border-radius: 10px;
      padding: 15px 20px;
      font-size: 1.2em;
      font-weight: bold;
      border: 3px solid #ccc;
      text-align: center;
    }

    .majority-true { color: #145a32; border-color: #58d68d; }
    .majority-false { color: #641e16; border-color: #ec7063; }

    /* FOOTER */
    footer {
      width: 100%;
      background-color: #264653;
      color: #fff;
      display: flex;
      justify-content: center;
      align-items: center; /* vertical alignment */
      gap: 20px;
      padding: 20px;
      font-size: 1.2em;
      margin-top: auto;
    }

    .chock-label { font-weight: bold; }

    .chock-value {
      padding: 6px 12px;
      border-radius: 5px;
      min-width: 80px;
      text-align: center;
    }

    .chock-idle { background-color: #5dade2; color: #0b3c5d; }
    .chock-deployed { background-color: #58d68d; color: #145a32; }
    .chock-moving { background-color: #ec7063; color: #641e16; }

    .clock {
      font-family: monospace;
      background-color: #e9c46a;
      padding: 10px 20px;
      border-radius: 5px;
    }

    /* DEFAULT SENSOR MESSAGE */
    .no-sensors {
      font-size: 1em;
      text-align: center;
      padding: 20px;
      background-color: #fff;
      border-radius: 10px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
      display: inline-flex;
      flex-direction: column;
      gap: 10px;
    }

    .no-sensors .line1 { font-size: 1.2em; font-weight: bold; }
    .no-sensors .line2 { font-size: 1em; }
  </style>
</head>

<body>
<header>
  <div class="header-title">
    <h1>HDAWCS Live Display</h1>
    <h2>Human-Detecting Automatic Wheel Chock Deployment System</h2>
  </div>

  <div class="header-right">
    <img src="https://www.tru.ca/__shared/assets/TRU_Logo_Horizontal_RGB-reversed37472.png">
    <img src="https://ci3.googleusercontent.com/meips/ADKq_NbxZFXzxut7A-r0DknIYAoEyzFjnyvsn8Kzj54VluKVUZEDn2FkbyIswtAYpZq2EhuTtN-UKdwbGnFegHmKElzCbLIDeh3dWcgSlHKXg3vo1VYv2VbILA=s0-d-e1-ft#https://arctechnologies.ca/assets/img/ArcNewLogoTransparentv1.png">
  </div>
</header>

<main id="sensors-container">
  <div class="no-sensors" id="no-sensors-msg">
    <span class="line1">No sensors connected</span>
    <span class="line2">Please connect sensor(s) to enable the HDAWCS</span>
  </div>
</main>

<div id="majority-box" class="majority-box">
  Majority Vote: Unknown
</div>

<footer>
  <div class="info-row">
    <span class="chock-label">Chock Status:</span>
    <span class="chock-value chock-idle" id="chock-status">Idle</span>
  </div>
  <div class="clock" id="clock">--:--:--</div>
</footer>

<script>
function updateClock() {
  document.getElementById("clock").textContent = new Date().toLocaleTimeString();
}
setInterval(updateClock, 1000);
updateClock();

async function updateSensors() {
  try {
    const r = await fetch("/state");
    if (r.status === 200) {
      const data = await r.json();
      const container = document.getElementById("sensors-container");
      container.innerHTML = "";

      let humanCount = 0;
      let totalSensors = 0;

      for (const [key, value] of Object.entries(data)) {
        if (key === "chockStatus") {
          const chockEl = document.getElementById("chock-status");
          chockEl.textContent = value;
          chockEl.classList.remove("chock-idle","chock-deployed","chock-moving");

          if(value.toLowerCase() === "idle") chockEl.classList.add("chock-idle");
          else if(value.toLowerCase() === "deployed") chockEl.classList.add("chock-deployed");
          else if(value.toLowerCase() === "moving") chockEl.classList.add("chock-moving");

          continue;
        }

        totalSensors++;
        if (value.human === true) humanCount++;

        const card = document.createElement("div");
        card.className = "sensor-card";

        const title = document.createElement("div");
        title.className = "sensor-title";
        title.textContent = key;

        const statusRow = document.createElement("div");
        statusRow.className = "info-row";

        const statusLabel = document.createElement("span");
        statusLabel.className = "label";
        statusLabel.textContent = "Status:";

        const statusValue = document.createElement("span");
        statusValue.className = "value-box " + (value.active ? "active-true" : "active-false");
        statusValue.textContent = value.active ? "Active" : "Inactive";

        statusRow.appendChild(statusLabel);
        statusRow.appendChild(statusValue);

        const humanRow = document.createElement("div");
        humanRow.className = "info-row";

        const humanLabel = document.createElement("span");
        humanLabel.className = "label";
        humanLabel.textContent = "Human:";

        const humanValue = document.createElement("span");
        humanValue.className = "value-box human-main " + (value.human ? "human-true" : "human-false");
        humanValue.textContent = value.human ? "Detected" : "Clear";

        humanRow.appendChild(humanLabel);
        humanRow.appendChild(humanValue);

        card.appendChild(title);
        card.appendChild(statusRow);
        card.appendChild(humanRow);

        container.appendChild(card);
      }

      // Show "No sensors" default message if no sensors detected
      if (totalSensors === 0) {
        container.innerHTML = `
          <div class="no-sensors">
            <span class="line1">No sensors connected</span>
            <span class="line2">Please connect sensor(s) to enable the HDAWCS</span>
          </div>`;
        document.getElementById("majority-box").style.display = "none"; // hide majority box
      } else {
        document.getElementById("majority-box").style.display = "block";
      }

      const majorityBox = document.getElementById("majority-box");
      const majority = humanCount > totalSensors / 2;

      majorityBox.textContent = `Majority Vote: ${majority ? "HUMAN DETECTED" : "CLEAR"}`;
      majorityBox.classList.remove("majority-true", "majority-false");
      majorityBox.classList.add(majority ? "majority-true" : "majority-false");
    }
  } catch (err) {
    console.error("Failed to fetch state:", err);
  }
}

setInterval(updateSensors, 1000);
updateSensors();
</script>

</body>
</html>
"""


def _make_handler(get_latest_json: Callable[[], str | None]) -> type[BaseHTTPRequestHandler]:
    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path == "/state":
                payload = get_latest_json()
                if payload is None:
                    self.send_response(204)
                    self.end_headers()
                else:
                    body = payload.encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
            elif self.path == "/":
                body = _HTML.encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format: str, *args: object) -> None:
            pass  # suppress default access logs

    return _Handler


async def serve(
    host: str,
    port: int,
    get_latest_json: Callable[[], str | None],
    logger: logging.Logger,
) -> None:
    server = ThreadingHTTPServer((host, port), _make_handler(get_latest_json))
    logger.info("HTTP server is UP http://%s:%d/", host, port)
    await asyncio.to_thread(server.serve_forever)
