$(document).ready(function(){
	
	//Add Subscription
	$('#add_subscription_button').click(function(){
		var plan_user = $('#plan_user').val();
		var plan_name = $('#plan_name').val();
		if((plan_name == '') || (plan_user == '')){
			$("#empty_fields").show().delay(5000).fadeOut();
			return false;
		}else{
			plan_data = {
					'plan_name' : plan_name,
					'plan_user': plan_user,
				}
		    $.ajax({
				type: 'POST',
		        url: "/addNewSubscription",
		        data: JSON.stringify(plan_data, null, '\t'),
		        contentType: 'application/json;charset=UTF-8',
		        success: function (res) {
		          json_data = JSON.parse(res) 	
		          console.log('json_data',json_data)
		          if (json_data.status == 'success'){
		       		$("#success_msg").show('').delay(5000).fadeOut();
		       		window.location.href='/subscriptions';
		          }else{
		          	$("#error_msg").html(json_data.message)
		          	$("#error_msg").show().delay(5000).fadeOut();
		          }
		        }
		    });

		}
	})


	//Delete a Subscription
	$('.delete_subscription').click(function(){
		subscription_id = $(this).attr("data-id");
		var result = confirm("Want to delete?");
		subscription_data = {'subscription_id':subscription_id}
		console.log('subscription_data',subscription_data)
		if (result) {
		    $.ajax({
				type: 'POST',
		        url: "/deleteSubscription/",
		        data: JSON.stringify(subscription_data, null, '\t'),
		        contentType: 'application/json;charset=UTF-8',
		        success: function (res) {
		          json_data = JSON.parse(res) 	
		          console.log('delete subscription--->',json_data)
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


	//Edit a Subscription
	$('#edit_subscription_button').click(function(){
		var subscription_id = $(this).attr("data-id");
		var plan_user = $('#plan_user').val();
		var plan_name = $('#plan_name').val();
		if((plan_name == '') || (plan_user == '')){
			$("#empty_fields").show().delay(5000).fadeOut();
			return false;
		}else{
			subscription_data = {
					'plan_name' : plan_name,
					'plan_user' : plan_user
				}
		    $.ajax({
				type: 'POST',
		        url: "/updateSubscription/"+subscription_id,
		        data: JSON.stringify(subscription_data, null, '\t'),
		        contentType: 'application/json;charset=UTF-8',
		        success: function (res) {
		          json_data = JSON.parse(res) 	
		          console.log('json_data',json_data)
		          if (json_data.status == 'success'){
		       		$("#success_msg").show('').delay(5000).fadeOut();
		       		window.location.href='/subscriptions';
		          }else{
		          	$("#error_msg").html(json_data.message)
		          	$("#error_msg").show().delay(5000).fadeOut();
		          }
		        }
		    });
	  	}
	})
		
})