var logs_row = {};
var config_row = {};


pylons_table_formatter = () => [
  '<button type="button" class="btn btn-secondary action-edit mx-1"><i class="bi bi-gear"></i></button>',
  '<button type="button" class="btn btn-secondary action-logs mx-1"><i class="bi bi-file-earmark-text"></i></button>',
].join('')


pylons_table_events = {
  'click .action-logs': (e, value, row) => {
    logs_row = row;
    $("#modal-pylon-logs").modal("show");
  },
  'click .action-edit': (e, value, row) => {
    config_row = row;
    $("#modal-pylon-config").modal("show");
  },
}


$("#modal-pylon-logs").on("show.bs.modal", function (e) {
  $("#modal-logs-pylon").text(logs_row.pylon_id);
  $("#input-logs").val("");
  window.socket.emit("task_logs_subscribe", {"pylon_runtime": "id:" + logs_row.pylon_id});
});


$("#modal-pylon-logs").on("hide.bs.modal", function (e) {
  $("#modal-logs-pylon").text("");
  $("#input-logs").val("");
  window.socket.emit("task_logs_unsubscribe", {"pylon_runtime": "id:" + logs_row.pylon_id});
});


window.socket.on("log_data", (data) => {
  data.forEach((item) => {
    $("#input-logs").val(
      $("#input-logs").val() + item.line + "\n"
    );
  });
});


$("#modal-pylon-config").on("show.bs.modal", function (e) {
  $("#modal-config-pylon").text(config_row.pylon_id);
  $("#input-cfg-edit").val("");
});


$("#btn-cfg-load").click(function() {
  axios.post(
    window.url_prefix + "/api/v1/repo_core/pylons",
    {
      "pylon_id": config_row.pylon_id,
      "action": "load",
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
    window.url_prefix + "/api/v1/repo_core/pylons",
    {
      "pylon_id": config_row.pylon_id,
      "action": "load_raw",
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
    window.url_prefix + "/api/v1/repo_core/pylons",
    {
      "pylon_id": config_row.pylon_id,
      "action": "save",
      "data": result,
    }
  )
  .then(function (response) {
    $("#modal-pylon-config").modal("hide");
  })
  .catch(function (error) {
    console.log(error);
  });
});


$("#btn-cfg-restart").click(function() {
  axios.post(
    window.url_prefix + "/api/v1/repo_core/pylons",
    {
      "pylon_id": config_row.pylon_id,
      "action": "restart",
    }
  )
  .then(function (response) {
    $("#modal-pylon-config").modal("hide");
  })
  .catch(function (error) {
    console.log(error);
  });
});
