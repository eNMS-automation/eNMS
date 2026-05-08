import { tables } from "../table.js";

tables.secret = class extends tables.data {};
tables.secret.prototype.type = "secret";
