$(document).ready(function(){
	//Allow only alphabets in plan name
	$('#plan_name').keypress(function (e) {
	    var regex = new RegExp("^[a-zA-Z ]+$");
	    var strigChar = String.fromCharCode(!e.charCode ? e.which : e.charCode);
	    if (regex.test(strigChar)) {
	        return true;
	    }
	    return false
  	});


  	//Allow only numbers in Price
	// $('#monthly_plan_price').keypress(function (e) {
	//     var regex = new RegExp("^[0-9]+$");
	//     var strigChar = String.fromCharCode(!e.charCode ? e.which : e.charCode);
	//     if (regex.test(strigChar)) {
	//         return true;
	//     }
	//     return false
 //  	});

	//save new plan data
	$('#save_plan_button').click(function(){
		var plan_name = $('#plan_name').val();
		var monthly_plan_price = $('#monthly_plan_price').val();
		var yearly_price = $('#yearly_plan_price').val();
		var monthly_plan_payment = $('#monthly_plan_payment').val();
		var yearly_plan_payment = $('#yearly_plan_payment').val();
		var reconnection_fees = $('#reconnection_fees').val();
		var link_up_charges = $('#link_up_charges').val();
		var description = $('#plan_description').val();
		var bidding_fees = $('#bidding_fees').val();
		var free_days = $('#free_days').val();
		var plan_type = $('#plan_type').val();
		console.log('description',description)
		if((plan_name == '') || (monthly_plan_price == '') || (yearly_price='')){
			$("#empty_fields").show().delay(5000).fadeOut();
			return false;
		}else{
			var yearly_price = $('#yearly_plan_price').val();
			var plan_type = $('#plan_type').val();
			plan_data = {
				'plan_name' : plan_name,
				'plan_type' : plan_type,
				'yearly_plan_price': yearly_price,
				'monthly_plan_price' : monthly_plan_price,
				'monthly_plan_payment' : monthly_plan_payment,
				'yearly_plan_payment' : yearly_plan_payment,
				'reconnection_fees' : reconnection_fees,
				'link_up_charges' : link_up_charges,
				'bidding_fees' : bidding_fees,
				'free_days' : free_days,
				'description' : description,
			}
			//Send data to server
			$.ajax({
				type: 'POST',
		        url: "/addNewPlan/",
		        data: JSON.stringify(plan_data, null, '\t'),
		        contentType: 'application/json;charset=UTF-8',
		        success: function (res) {
		          json_data = JSON.parse(res) 	
		          console.log('json_data',json_data)
		          if (json_data.status == 'success'){
		          	$('#plan_name').val('');
					$('#monthly_plan_price').val('');
					$('#yearly_plan_price').val('');
					$('#yearly_plan_payment').val('');
					$('#monthly_plan_payment').val('');
					$('#reconnection_fees').val('');
					$('#link_up_charges').val('');
					$('#bidding_fees').val('');
					$('#free_days').val('');
					$('textarea#plan_description').val('');
		       		$("#success_msg").show('').delay(5000).fadeOut();
		          }else{
		          	$("#error_msg").html(json_data.message)
		          	$("#error_msg").show().delay(5000).fadeOut();
		          }
		        }
		    });
		}

	})


	//Delete a plan
	$('.delete_plan').click(function(){
		plan_id = $(this).attr("data-id");
		var result = confirm("Want to delete?");
		plan_data = {'plan_id':plan_id}
		console.log('plan_data',plan_data)
		if (result) {
		    $.ajax({
				type: 'POST',
		        url: "/deletePlan/",
		        data: JSON.stringify(plan_data, null, '\t'),
		        contentType: 'application/json;charset=UTF-8',
		        success: function (res) {
		          json_data = JSON.parse(res) 	
		          console.log('delete plan--->',json_data)
		          if (json_data.status == 'success'){
		       		$("#success_msg").show('').delay(5000).fadeOut();
		       		window.location.reload();
		          }else{
		          	$("#error_msg").html(json_data.message)
		          	$("#error_msg").show().delay(5000).fadeOut();
		          }
		        }
		    });
		}
	})


	//Edit a plan
	$('#edit_plan_button').click(function(){
		plan_id = $(this).attr("data-id");
		var plan_name = $('#plan_name').val();
		var monthly_plan_price = $('#monthly_plan_price').val();
		var yearly_price = $('#yearly_plan_price').val();
		var monthly_plan_payment = $('#monthly_plan_payment').val();
		var yearly_plan_payment = $('#yearly_plan_payment').val();
		var reconnection_fees = $('#reconnection_fees').val();
		var link_up_charges = $('#link_up_charges').val();
		var description = $('#plan_description').val();
		var bidding_fees = $('#bidding_fees').val();
		var free_days = $('#free_days').val();
		var plan_type = $('#plan_type').val();
		if((plan_name == '') || (plan_description == '')){
			$("#empty_fields").show().delay(5000).fadeOut();
			return false;
		}else{
			plan_data = {
				'plan_name' : plan_name,
				'plan_type' : plan_type,
				'yearly_plan_price': yearly_price,
				'monthly_plan_price' : monthly_plan_price,
				'monthly_plan_payment' : monthly_plan_payment,
				'yearly_plan_payment' : yearly_plan_payment,
				'reconnection_fees' : reconnection_fees,
				'link_up_charges' : link_up_charges,
				'bidding_fees' : bidding_fees,
				'free_days' : free_days,
				'description' : description,
			}
			url: "/updatePlan/"+plan_id
		    $.ajax({
				type: 'POST',
		        url: url,
		        data: JSON.stringify(plan_data, null, '\t'),
		        contentType: 'application/json;charset=UTF-8',
		        success: function (res) {
		          json_data = JSON.parse(res) 	
		          console.log('json_data',json_data)
		          if (json_data.status == 'success'){
		       		$("#success_msg").show('').delay(5000).fadeOut();
		       		window.location.href='/plans';
		          }else{
		          	$("#error_msg").html(json_data.message)
		          	$("#error_msg").show().delay(5000).fadeOut();
		          }
		        }
		    });
	  	}
	})

	//Add Brokerage
	$('#update_button').click(function(){
		// var brokerage_percentage = 

	})

})