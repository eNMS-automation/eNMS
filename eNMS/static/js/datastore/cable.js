import { tables } from "../table.js";

tables.cable = class extends tables.data {};
tables.cable.prototype.type = "cable";
