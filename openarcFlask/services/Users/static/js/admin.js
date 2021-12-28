$(document).ready(function(){
	//Admin Login Function
	$('#admin_login').click(function(){
		var email = $('#admin_email').val();
		var password = $('#admin_password').val();
		var emailReg = /^([\w-\.]+@([\w-]+\.)+[\w-]{2,4})?$/;
		if((email == '') || (password == '')){
			$("#empty_fields").show().delay(5000).fadeOut();
			return false;
		}
		email_valid = emailReg.test( email )
		if (email_valid == true){
			user_data = {
				'admin_email' : email,
				'admin_password': password
			}
			//Send data to server
			$.ajax({
				type: 'POST',
		        url: "/adminLogin/",
		        data: JSON.stringify(user_data, null, '\t'),
		        contentType: 'application/json;charset=UTF-8',
		        success: function (res) {
		          json_data = JSON.parse(res) 	
		          console.log('json_data',json_data)
		          if (json_data.status == 'success'){
		       		console.log('login success')
		       		window.location.href = '/adminDashboard/';
		          }else{
		          	$("#error_msg").html(json_data.message)
		          	$("#error_msg").show().delay(5000).fadeOut();
		          }
		        }
		    });
		}else{
			$("#invalid_email").show().delay(5000).fadeOut();
			return false;
		}
	})


})