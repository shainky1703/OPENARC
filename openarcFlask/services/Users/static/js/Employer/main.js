(function ($) {

	"use strict";

	var fullHeight = function () {

		$('.js-fullheight').css('height', $(window).height());
		$(window).resize(function () {
			$('.js-fullheight').css('height', $(window).height());
		});

	};
	fullHeight();

	$('#sidebarCollapse').on('click',function () {
		$('#sidebar').toggleClass('active');
	});

	$('#sidebarCollapse').on('click',function () {
		$('.logo-img').hide();
	});
	
	// $('#sidebarCollapse').hover(function () {
	// 	$('#sidebar').toggleClass('active');
	// });
})(jQuery);



