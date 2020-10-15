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
    terminalContent += data
  });
}

window.onbeforeunload = function closingCode() {
  $.ajax({
    type: "POST",
    async: false,
    url: "/shutdown",
    data: JSON.stringify(data),
    contentType: "application/json",
    dataType: "json",
  });
};

initPytty();
