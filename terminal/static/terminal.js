const terminal = new Terminal({ cursorBlink: true });
const fitAddon = new FitAddon.FitAddon();
const socket = io.connect("/terminal");
let terminalContent = "";

function initPytty() {
  terminal.loadAddon(fitAddon);
  terminal.open(document.getElementById("terminal"));
  fitAddon.fit();
  terminal.onKey((event) => socket.emit("input", event.key));
  socket.on("output", (data) => {
    terminal.write(data);
    terminalContent += data;
  });
}

window.onunload = function () {
  navigator.sendBeacon(
    "/shutdown",
    new Blob([JSON.stringify(terminalContent)], {
      type: "application/json",
    })
  );
};

initPytty();
