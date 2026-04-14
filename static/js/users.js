users_table_formatter = () => [
  '<button type="button" class="btn btn-secondary action-edit mx-1"><i class="bi bi-gear"></i></button>',
  '<button type="button" class="btn btn-danger action-delete mx-1"><i class="bi bi-trash"></i></button>',
].join('')


users_table_events = {
  'click .action-delete': (e, value, row) => {
    if (!window.confirm("Delete?" + " " + row.email)) {
      return;
    }
    axios.delete(
      window.url_prefix + "/api/v1/repo_core/users" + "/?user_id=" + row.id
    )
    .then(function (response) {
      if (response.data.ok) {
        $("#users-table").bootstrapTable("refresh");
      }
    })
    .catch(function (error) {
      console.log(error);
    });
  },
  'click .action-edit': (e, value, row) => {
    axios.post(
      window.url_prefix + "/api/v1/repo_core/users",
      {
        "user_id": row.id,
      }
    )
    .then(function (response) {
      if (response.data.ok) {
        $("#edit-user-modal-form").trigger("reset");
        $("#edit-user-modal-form-id").val(response.data.user_id);
        $("#edit-user-modal-form-email").val(response.data.user_email);
        $("#edit-user-modal-form-name").val(response.data.user_name);
        $("#edit-user-modal-form-token").val(response.data.user_token);
        $("#edit-user-modal").modal("show");
      }
    })
    .catch(function (error) {
      console.log(error);
    });
  },
}


$("#new-user-modal").on("show.bs.modal", function() {
  $("#new-user-modal-form").trigger("reset");
});


$("#new-user-modal-save").on("click", function() {
  var form_data = $("#new-user-modal-form").serializeArray();
  var data = {};
  form_data.forEach(item => {
    data[item.name] = item.value;
  });
  axios.put(
    window.url_prefix + "/api/v1/repo_core/users",
    data
  ).then(
    function(response) {
      if (response.data.ok) {
        $("#new-user-modal").modal("hide");
        $("#users-table").bootstrapTable("refresh");
      }
    }
  ).catch(
    function(error) {
      console.log(error);
    }
  );
});


$("#edit-user-modal-save").on("click", function() {
  var form_data = $("#edit-user-modal-form").serializeArray();
  var data = {};
  form_data.forEach(item => {
    data[item.name] = item.value;
  });
  axios.patch(
    window.url_prefix + "/api/v1/repo_core/users",
    data
  ).then(
    function(response) {
      if (response.data.ok) {
        $("#edit-user-modal").modal("hide");
        $("#users-table").bootstrapTable("refresh");
      }
    }
  ).catch(
    function(error) {
      console.log(error);
    }
  );
});
