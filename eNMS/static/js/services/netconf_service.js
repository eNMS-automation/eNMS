/*
global
eNMS: false
*/

// eslint-disable-next-line
function job(id) {    
    // timout of 50ms required to wait for form data to load
    setTimeout(() => {                        
        // allocate the dropdown
        const operation_dropdown_id = "netconf_service-nc_type";
        const operation_dropdown = getJQueryObject(operation_dropdown_id, id);        

        // maintain state        
        let input_data = JSON.parse($("#input_data").val()); // this is the data passed in through the view        
        const fields = input_data["fields"]
        const netconf_type = input_data["netconf_type"]
        
        // get the current dropdown value and update UI
        let operation = operation_dropdown.val()            
        updateElements(fields, netconf_type, operation)
        
        ///////////// CHANGE HANDLER /////////////////
        // have to be defined before they can be used later in the code
        operation_dropdown.change(() => {                    
            // get the data from the selected element and update
            operation = getSelectedValue(operation_dropdown_id, id);
            updateElements(fields, netconf_type, operation)
        })    
    }, 50)
    
      
    // HELPERS    
    function updateElements(field_list, netconf_types, selected_type) {        
         // make all fields invisible
         for (var key in field_list) {
            hideElement(field_list[key])
        }

        // enable fields per selection
        fields_to_show = netconf_types[selected_type]
        for (var key in fields_to_show) {
            console.log(fields_to_show[key])
            showElement(fields_to_show[key])
        }
    }

    function hideElement(name) {        
        // disables visibility for a field
        $(`label[for=${name}]`).hide()
        if (id) {
            $(`#netconf_service-${name}-${id}`).parent().hide()
        } else {
            $(`#netconf_service-${name}`).parent().hide()    
        }
    }

    function showElement(name) {
        // enables visibility for a field
        $(`label[for=${name}]`).show()
        if (id) {
            $(`#netconf_service-${name}-${id}`).parent().show()
        } else {
            $(`#netconf_service-${name}`).parent().show()
        }
    }

    function getSelectedValue(dropdown_id, id) {
        // returns the currently selected value for a dropdown
        let value = null
        if (id) {
            value = $(`#${dropdown_id}-${id} option:selected`).val();            
        } else {
            value = $(`#${dropdown_id} option:selected`).val();
        }
        return value
    }
   
    function getJQueryObject(object_id, id) {        
        // returns the JQuery object of an object
        // if id is passed in we have an existing service
        let e = null;
        if (id) {
            e = $(`#${object_id}-${id}`);
        } else {
            e = $(`#${object_id}`);
        }
        return e;
    }
}

    
    


