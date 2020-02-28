/*
global
CodeMirror: false
*/

(function(CodeMirror) {
  "use strict";

  CodeMirror.defineMode("logs", function() {
    let external = {
      startState: function() {
        return {
          tokenize: function(stream) {
            if (stream.match(/\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\.\d{6}/)) {
              return "number";
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

  CodeMirror.defineMode("network", function() {
    let external = {
      startState: function() {
        return {
          tokenize: function(stream) {
            if (stream.match(/interface/)) return "keyword";
            if (stream.match(/^(?!.*\.$)((1?\d?\d|25[0-5]|2[0-4]\d)(\.|\/\d{2}|$)){4}/)) return "variable-2";
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
