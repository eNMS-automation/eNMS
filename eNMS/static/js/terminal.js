/*
global
device: false
FitAddon: false
io: false
session: false
Terminal: false
*/

const terminal = new Terminal({ cursorBlink: true });
const fitAddon = new FitAddon.FitAddon();
const socket = io("/terminal", { query: `session=${session}&device=${device}` });
let terminalContent = "";

function initTerminal() {
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

initTerminal();
