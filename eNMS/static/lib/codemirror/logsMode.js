/*
global
CodeMirror: false
*/

(function(CodeMirror) {
  "use strict";

  CodeMirror.defineMode("logs", function(conf, parserConf) {
    let stringPrefixes = new RegExp(
      "^(([rbuf]|(br)|(fr))?('{3}|\"{3}|['\"]))",
      "i"
    );
    let external = {
      startState: function(basecolumn) {
        return {
          tokenize: function(stream, state) {
            if (stream.eatSpace()) return null;
            if (stream.match(/\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\.\d{6}/)) {
              return "number";
            }
            if (stream.match(stringPrefixes)) {
              return state.tokenize(stream, state);
            }
            if (stream.match(/DEVICE.*\s:\s/)) return "comment";
            if (stream.match(/SERVICE.*?\s[-|:]\s/)) return "variable-2";
            if (stream.match(/warning/)) return "keyword";
            if (stream.match(/debug|info/)) return "string";
            if (stream.match(/error|critical/)) return "error";
            stream.next();
          },
        };
      },
      token: function(stream, state) {
        return state.tokenize(stream, state);
      },
    };
    return external;
  });
})(CodeMirror);
