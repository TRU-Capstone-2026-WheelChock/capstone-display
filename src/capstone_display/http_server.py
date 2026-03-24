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
* {
  box-sizing: border-box;
}

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

.page-container {
  width: 100%;
  flex: 1;
  display: flex;
  flex-direction: column;
}

header {
  width: 100%;
  background-color: #3cb8ad;
  padding: 15px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 110px;
}

.header-title {
  display: flex;
  flex-direction: column;
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
  opacity: 0.85;
}

.header-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 5px;
}

.header-right img {
  height: 40px;
  object-fit: contain;
}

main {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 20px;
  padding: 20px;
  max-width: 1000px;
  margin: 0 auto;
}

.sensor-card {
  background-color: #fff;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  padding: 15px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.sensor-title {
  font-weight: bold;
  margin-bottom: 8px;
  font-size: 1.1em;
  color: #264653;
}

.info-row {
  display: flex;
  align-items: center;
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
  min-width: 80px;
  text-align: center;
}

.human-main {
  font-size: 1.1em;
  font-weight: bold;
  padding: 6px 12px;
}

.active-true { background-color: #5dade2; color: #0b3c5d; }
.human-true { background-color: #58d68d; color: #145a32; }
.human-false { background-color: #ec7063; color: #641e16; }

.majority-box {
  max-width: 400px;
  width: fit-content;
  margin: 20px auto;
  background-color: #fff;
  border-radius: 10px;
  padding: 15px 30px;
  font-size: 1.2em;
  font-weight: bold;
  border: 3px solid #ccc;
  text-align: center;
  display: none;
}

.majority-true { color: #145a32; border-color: #58d68d; }
.majority-false { color: #641e16; border-color: #ec7063; }

footer {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  padding: 20px;
  font-size: 1.2em;
  background-color: #264653;
  color: #fff;
}

.chock-label { font-weight: bold; }

.chock-value {
  padding: 6px 12px;
  border-radius: 5px;
  background-color: #5dade2; /* always blue */
  color: #ffffff;
  font-weight: bold;
}

.override-box {
  padding: 6px 12px;
  border-radius: 5px;
  font-weight: bold;
  color: #fff;
  min-width: 80px;
  text-align: center;
}

.override-true { background-color: #58d68d; }
.override-false { background-color: #ec7063; }

.clock {
  font-family: monospace;
  background-color: #e9c46a;
  padding: 10px 20px;
  border-radius: 5px;
}
</style>
</head>

<body>
<div class="page-container">

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

<main id="sensors-container"></main>

<div id="majority-box" class="majority-box">Majority Vote: Unknown</div>

<footer>
  <div class="info-row">
    <span class="chock-label">Chock Status:</span>
    <span class="chock-value" id="chock-status">Idle</span>
  </div>

  <div class="info-row">
    <span class="chock-label">Override Mode:</span>
    <span id="override-status" class="override-box override-false">FALSE</span>
  </div>

  <div class="clock" id="clock">--</div>
</footer>

</div>

<script>
function updateClock(timestamp) {
  if(timestamp){
    document.getElementById("clock").textContent = timestamp;
  }
}

async function updateSensors() {
  try {
    const r = await fetch("/state");
    if (r.status === 200) {
      const data = await r.json();
      const container = document.getElementById("sensors-container");
      container.innerHTML = "";

      const sensorDict = data.sensor_display_dict || {};
      const sensorKeys = Object.keys(sensorDict);
      let humanCount = 0;

      for(const key of sensorKeys){
        const sensor = sensorDict[key];
        if(sensor.is_there_human) humanCount++;

        const card = document.createElement("div");
        card.className = "sensor-card";

        const title = document.createElement("div");
        title.className = "sensor-title";
        title.textContent = sensor.sensor_name;

        const statusRow = document.createElement("div");
        statusRow.className = "info-row";

        statusRow.innerHTML = `
          <span class="label">Status:</span>
          <span class="value-box active-true">Active</span>
        `;

        const humanRow = document.createElement("div");
        humanRow.className = "info-row";

        humanRow.innerHTML = `
          <span class="label">Human:</span>
          <span class="value-box human-main ${sensor.is_there_human ? "human-true" : "human-false"}">
            ${sensor.is_there_human ? "Detected" : "Clear"}
          </span>
        `;

        card.appendChild(title);
        card.appendChild(statusRow);
        card.appendChild(humanRow);

        container.appendChild(card);
      }

      // Chock status (always styled blue)
      document.getElementById("chock-status").textContent = data.moter_mode || "Unknown";

      // Override
      const overrideEl = document.getElementById("override-status");
      overrideEl.textContent = data.is_override_mode ? "TRUE" : "FALSE";
      overrideEl.className = "override-box " + (data.is_override_mode ? "override-true" : "override-false");

      // Timestamp (no flicker)
      updateClock(data.timestamp);

      // Majority vote
      const majorityBox = document.getElementById("majority-box");
      if(sensorKeys.length === 0){
        majorityBox.style.display = "none";
      } else {
        majorityBox.style.display = "block";

        if(humanCount > sensorKeys.length/2){
          majorityBox.textContent = "Majority Vote: DETECTED";
          majorityBox.className = "majority-box majority-true";
        }
        else if(humanCount < sensorKeys.length/2){
          majorityBox.textContent = "Majority Vote: CLEAR";
          majorityBox.className = "majority-box majority-false";
        }
        else {
          majorityBox.textContent = "Majority Vote: Unknown";
          majorityBox.className = "majority-box";
        }
      }

    }
  } catch(err){
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
