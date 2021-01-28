/*
global
FitAddon: false
io: false
Terminal: false
*/

const terminal = new Terminal({ cursorBlink: true });
const fitAddon = new FitAddon.FitAddon();
const terminalPortString = window.location.pathname.split("/")[1];
const socket = io("/terminal", { path: `/${terminalPortString}/socket.io` });
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

window.onunload = function() {
  navigator.sendBeacon(
    `/${terminalPortString}/shutdown`,
    new Blob([JSON.stringify(terminalContent)], {
      type: "application/json",
    })
  );
};

initTerminal();
