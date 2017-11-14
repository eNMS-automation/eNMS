$(function() {

  // test to ensure jQuery is working
  console.log("whee!")

  // disable refresh button
  $("#refresh-btn").prop("disabled", true)
  

  $("#department_select").change(function() {

    // grab value
    var department_id = $("#department_select").val();

    // send value via GET to URL /<department_id>
    var get_request = $.ajax({
      type: 'GET',
      url: '/department/' + department_id + '/',
    });

    // handle response
    get_request.done(function(data){

      // data
      console.log(data)

      // add values to list 
      var option_list = [["", "Select an employee"]].concat(data);
      $("#employee_select").empty();
        for (var i = 0; i < option_list.length; i++) {
          $("#employee_select").append(
            $("<option></option>").attr("value", option_list[i][0]).text(option_list[i][1]));
        }
      // show model list
      $("#employee_select").show();
    });
  });

  $("#submit-btn").click(function() {

    // grab values
    var department = $("#department_select").find(":selected").text();
    var employee = $("#employee_select").find(":selected").text();
    var department_id = $("#department_select").val();
    var employee_id = $("#employee_select").val();

    // append values to the DOM
    $("#chosen_department").html(department);
    $("#chosen_employee").html(employee);
    $("#chosen_department_id").html(department_id);
    $("#chosen_employee_id").html(employee_id);

    // show values selected
    $("#show_selection").show();
    // enable refresh button
    $("#refresh-btn").prop("disabled", false)
    // disable submit button
    $("#submit-btn").prop("disabled", true);

    // disable dropdown inputs
    $("#employee_select").prop("disabled", true);
    $("#department_select").prop("disabled", true);
    $("#employee_select").prop("disabled", true);
  });

  $("#refresh-btn").click(function() {

    // remove values to the DOM
    $("#chosen_department").html("");
    $("#chosen_employee").html("");
    $("#chosen_department_id").html("");
    $("#chosen_employee_id").html("");

    // hide values selected
    $("#show_selection").hide();
    // disable refresh button
    $("#refresh-btn").prop("disabled", true);
    // enable submit button
    $("#submit-btn").prop("disabled", false);
    // hide model list
    $("#employee_select").hide();

    // enable dropdown inputs
    $("#employee_select").prop("disabled", false);
    $("#department_select").prop("disabled", false);

   
  });

});