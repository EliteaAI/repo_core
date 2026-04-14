var config_row = {};


remote_table_formatter = () => [
  '<button type="button" class="btn btn-secondary btn-sm action-edit mx-1"><i class="bi bi-gear"></i></button>',
].join('')


remote_table_events = {
  'click .action-edit': (e, value, row) => {
    config_row = row;
    $("#modal-edit-config").modal("show");
  },
}


$("#modal-edit-config").on("show.bs.modal", function (e) {
  $("#form-edit-config").get(0).reset();
  $("#modal-edit-plugin").text(config_row.pylon_id + " - " + config_row.name);
});


$("#btn-cfg-load").click(function() {
  axios.post(
    window.url_prefix + "/api/v1/repo_core/remote",
    {
      "action": "load",
      "pylon_id": config_row.pylon_id,
      "name": config_row.name,
    }
  )
  .then(function (response) {
    $("#input-cfg-edit").val(response.data.config);
  })
  .catch(function (error) {
    console.log(error);
  });
});


$("#btn-cfg-load-raw").click(function() {
  axios.post(
    window.url_prefix + "/api/v1/repo_core/remote",
    {
      "action": "load_raw",
      "pylon_id": config_row.pylon_id,
      "name": config_row.name,
    }
  )
  .then(function (response) {
    $("#input-cfg-edit").val(response.data.config);
  })
  .catch(function (error) {
    console.log(error);
  });
});


$("#btn-cfg-save").click(function() {
  var result = $("#input-cfg-edit").val();
  axios.post(
    window.url_prefix + "/api/v1/repo_core/remote",
    {
      "action": "save",
      "pylon_id": config_row.pylon_id,
      "name": config_row.name,
      "data": result,
    }
  )
  .then(function (response) {
    $("#modal-edit-config").modal("hide");
  })
  .catch(function (error) {
    console.log(error);
  });
});


$("#btn-update").click(function() {
  var data = $("#remote-table").bootstrapTable("getSelections");
  axios.post(
    window.url_prefix + "/api/v1/repo_core/remote",
    {
      "action": "update",
      "data": data,
    }
  )
  .then(function (response) {})
  .catch(function (error) {
    console.log(error);
  });
});


$("#btn-update-with-reqs").click(function() {
  var data = $("#remote-table").bootstrapTable("getSelections");
  axios.post(
    window.url_prefix + "/api/v1/repo_core/remote",
    {
      "action": "update_with_reqs",
      "data": data,
    }
  )
  .then(function (response) {})
  .catch(function (error) {
    console.log(error);
  });
});


$("#btn-purge-reqs").click(function() {
  var data = $("#remote-table").bootstrapTable("getSelections");
  axios.post(
    window.url_prefix + "/api/v1/repo_core/remote",
    {
      "action": "purge_reqs",
      "data": data,
    }
  )
  .then(function (response) {})
  .catch(function (error) {
    console.log(error);
  });
});


$("#btn-delete").click(function() {
  var data = $("#remote-table").bootstrapTable("getSelections");
  axios.post(
    window.url_prefix + "/api/v1/repo_core/remote",
    {
      "action": "delete",
      "data": data,
    }
  )
  .then(function (response) {})
  .catch(function (error) {
    console.log(error);
  });
});


$("#btn-reload").click(function() {
  var data = $("#remote-table").bootstrapTable("getSelections");
  axios.post(
    window.url_prefix + "/api/v1/repo_core/remote",
    {
      "action": "reload",
      "data": data,
    }
  )
  .then(function (response) {})
  .catch(function (error) {
    console.log(error);
  });
});


$("#btn-manual").click(function() {
  var data = $("#ipt-param").val();
  var result = [];
  var pylons_data = data.split(";");
  for (var i_idx in pylons_data) {
    var items = pylons_data[i_idx].split(":");
    var pylon_id = items[0].trim();
    var plugins = items[1].split(",");
    for (var j_idx in plugins) {
      var plugin = plugins[j_idx].trim();
      result.push({
        "pylon_id": pylon_id,
        "name": plugin,
        "state": true,
      });
    }
  }
  axios.post(
    window.url_prefix + "/api/v1/repo_core/remote",
    {
      "action": "update",
      "data": result,
    }
  )
  .then(function (response) {})
  .catch(function (error) {
    console.log(error);
  });
});


$("#btn-export-configs").click(function() {
  var data = $("#remote-table").bootstrapTable("getSelections");
  $("#form-export-configs-data").val(JSON.stringify(data));
  $("#form-export-configs").submit();
});


$("#btn-import-configs").click(function() {
  $("#modal-import-config").modal("show");
});


$("#modal-import-config").on("show.bs.modal", function (e) {
  $("#form-import-config").get(0).reset();
});


$("#btn-cfg-import").click(function() {
  var data = new FormData();
  data.append("action", "import_configs");
  data.append("file", $("#input-cfg-import")[0].files[0]);
  axios.post(window.url_prefix + "/api/v1/repo_core/remote", data)
  .then(function (response) {
    $("#modal-import-config").modal("hide");
  })
  .catch(function (error) {
    console.log(error);
  });
});
