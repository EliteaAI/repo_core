var logs_row = {};


$(".refresh-table-button").click(function() {
  $($(this).data("target")).bootstrapTable("refresh", {});
});


tasks_table_formatter = () => [
  '<button type="button" class="btn btn-secondary action-logs mx-1"><i class="bi bi-file-earmark-text"></i></button>',
  '<button type="button" class="btn btn-danger action-stop mx-1"><i class="bi bi-stop-circle"></i></button>',
].join('')


tasks_table_events = {
  'click .action-logs': (e, value, row) => {
    logs_row = row;
    $("#modal-task-logs").modal("show");
  },
  'click .action-stop': (e, value, row) => {
    axios.delete(
      window.url_prefix + "/api/v1/repo_core/tasks" + "/?task_id=" + row.task_id
    )
    .then(function (response) {
      if (response.data.ok) {
        $("#table-task").bootstrapTable("refresh");
      }
    })
    .catch(function (error) {
      console.log(error);
    });
  },
}


$("#btn-start-task").click(function() {
  var task = $("#task-selector").val();
  var param = $("#task-param").val();
  axios.put(
    window.url_prefix + "/api/v1/repo_core/tasks",
    {
      "task": task,
      "param": param,
    }
  )
  .then(function (response) {
    if (response.data.ok) {
      $("#table-task").bootstrapTable("refresh", {});
    }
  })
  .catch(function (error) {
    console.log(error);
  });
});


$("#modal-task-logs").on("show.bs.modal", function (e) {
  $("#modal-logs-task").text(logs_row.task_id);
  $("#input-logs").val("");
  window.socket.emit("task_logs_subscribe", {"tasknode_task": "id:" + logs_row.task_id});
});


$("#modal-task-logs").on("hide.bs.modal", function (e) {
  $("#modal-logs-task").text("");
  $("#input-logs").val("");
  window.socket.emit("task_logs_unsubscribe", {"tasknode_task": "id:" + logs_row.task_id});
});


window.socket.on("log_data", (data) => {
  data.forEach((item) => {
    $("#input-logs").val(
      $("#input-logs").val() + item.line + "\n"
    );
  });
});
