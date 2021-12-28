$(document).ready(function(){
	//Get Users data for chart
	$.ajax({
		type: 'GET',
        url: "/getUsersChartData",
        success: function (res) {
          json_data = JSON.parse(res) 	
          console.log('json_data',json_data.enquirers)
          //Users chart 
          var chartColors = {
			  red: 'rgb(255, 99, 132)',
			  orange: 'rgb(255, 159, 64)',
			  yellow: 'rgb(255, 205, 86)',
			  green: 'rgb(75, 192, 192)',
			  blue: 'rgb(54, 162, 235)',
			  purple: 'rgb(153, 102, 255)',
			  grey: 'rgb(231,233,237)'
			};

			var MONTHS = json_data.months
			var config = {
			  	type: 'line',
			  	data: {
					    labels: MONTHS,
					    datasets: [{
					      label: "Members",
					      backgroundColor: chartColors.red,
					      borderColor: chartColors.red,
					      data: json_data.members,
					      fill: false,
					    }, {
					      label: "Employers",
					      fill: false,
					      backgroundColor: chartColors.blue,
					      borderColor: chartColors.blue,
					      data: json_data.enquirers,
					    }]
		  			},
		  			options: {
					    responsive: true,
					    title: {
					      display: true,
					      text: 'Users Registered Per Month'
					    },
					    tooltips: {
					      mode: 'label',
					    },
					    hover: {
					      mode: 'nearest',
					      intersect: true
					    },
					    scales: {
					      xAxes: [{
					        display: true,
					        scaleLabel: {
					          display: true,
					          labelString: 'Month'
					        }
					      }],
					      yAxes: [{
					        display: true,
					        scaleLabel: {
					          display: true,
					          labelString: 'Value'
					        }
					      }]
					    }
				  	}
			};
			var ctx = document.getElementById("users-chart").getContext("2d");
			window.myLine = new Chart(ctx, config);
          
    	}
    });


	//Get Subscriptions data for chart
	$.ajax({
		type: 'GET',
        url: "/getSubscriptionsChartData",
        success: function (res) {
          json_data = JSON.parse(res) 	
          console.log('json_data',json_data)
          //Users chart 
          var chartColors = {
			  red: 'rgb(255, 99, 132)',
			  orange: 'rgb(255, 159, 64)',
			  yellow: 'rgb(255, 205, 86)',
			  green: 'rgb(75, 192, 192)',
			  blue: 'rgb(54, 162, 235)',
			  purple: 'rgb(153, 102, 255)',
			  grey: 'rgb(231,233,237)'
			};

			var MONTHS = json_data.months
			var config = {
			  	type: 'line',
			  	data: {
					    labels: MONTHS,
					    datasets: [{
					      label: "Revenue GBP",
					      backgroundColor: chartColors.red,
					      borderColor: chartColors.red,
					      data: json_data.revenue,
					      fill: false,
					    }]
		  			},
		  			options: {
					    responsive: true,
					    title: {
					      display: true,
					      text: 'Revenue generated per month'
					    },
					    tooltips: {
					      mode: 'label',
					    },
					    hover: {
					      mode: 'nearest',
					      intersect: true
					    },
					    scales: {
					      xAxes: [{
					        display: true,
					        scaleLabel: {
					          display: true,
					          labelString: 'Month'
					        }
					      }],
					      yAxes: [{
					        display: true,
					        scaleLabel: {
					          display: true,
					          labelString: 'Value'
					        }
					      }]
					    }
				  	}
			};
			var ctx = document.getElementById("subscriptions-chart").getContext("2d");
			window.myLine = new Chart(ctx, config);
    	}
    })
    

})
