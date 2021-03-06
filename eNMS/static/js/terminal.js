/*
global
csrfToken: false
device: false
FitAddon: false
io: false
session: false
Terminal: false
*/

const terminal = new Terminal({ cursorBlink: true });
const fitAddon = new FitAddon.FitAddon();
const socket = io("/terminal", { query: `session=${session}` });
let terminalContent = "";

function initTerminal() {
  terminal.loadAddon(fitAddon);
  terminal.open(document.getElementById("terminal"));
  fitAddon.fit();
  terminal.onKey((event) => socket.emit("input", event.key));
  socket.emit("join", session);
  socket.on("output", (data) => {
    terminal.write(data);
    terminalContent += data;
  });
}

window.onunload = function () {
  fetch(`/save_session/${session}`, {
    method: "POST",
    body: JSON.stringify({ content: terminalContent }),
    headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
  });
};

initTerminal();
