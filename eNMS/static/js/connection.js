const term = new Terminal({ cursorBlink: true });
const fitAddon = new FitAddon.FitAddon();
const socket = io.connect("/terminal");

function initConnection() {
  term.loadAddon(fitAddon);
  term.open(document.getElementById("terminal"));
  fitAddon.fit();
  term.write("Connecting...");
  term.onKey((event) => socket.emit("input", event.key));
  socket.on("output", (data) => term.write(data));
}

initConnection();
