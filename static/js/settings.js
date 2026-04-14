window.cm = CodeMirror.fromTextArea(
  $("#settings-textarea").get(0),
  {
    mode: "yaml",
    theme: "twilight",
    lineNumbers: true,
    lint: true,
    gutters: [
      "CodeMirror-lint-markers",
    ]
  }
);


$("#load-settings").on("click", function() {
  axios.get(
    window.url_prefix + "/api/v1/repo_core/settings"
  ).then(
    function(response) {
      window.cm.setValue(response.data.settings);
    }
  ).catch(
    function(error) {
      console.log(error);
    }
  );
});


$("#save-settings").on("click", function() {
  axios.post(
    window.url_prefix + "/api/v1/repo_core/settings",
    {
      "settings": window.cm.getValue(),
    }
  ).then(
    function(response) {
      if (response.data.ok) {
        window.cm.setValue("");
      }
    }
  ).catch(
    function(error) {
      console.log(error);
    }
  );
});
