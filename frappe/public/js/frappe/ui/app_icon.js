// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt


frappe.provide("frappe.ui")
frappe.ui.app_icon = {
	get_html: function(module, small) {
		var icon = module.icon;
		var color = module.color;
		var icon_style = "";
		if(module.reverse) {
			icon_style = "color: #36414C;";
		}

		if(!color) {
			color = '#4aa3df';
		}

		// first letter
		if(!icon) {
			icon = '<span class="inner" ' +
				(module.reverse ? ('style="' + icon_style + '"') : '')
				+ '>' + module._label[0].toUpperCase() + '</span>';
		} else if(icon.split(".").slice(-1)[0]==="svg") {
			$.ajax({
				url: frappe.urllib.get_full_url(icon),
				dataType: "text",
				async: false,
				success: function(data) {
					icon = data;
				}
			})
			icon = '<object>'+ icon+'</object>';
		} else {
			icon = '<i class="'+ icon+'" title="' + module._label + '" style="'+ icon_style + '"></i>';
		}

		return '<div class="app-icon'+ (small ? " app-icon-small" : "")
			+'" style="background-color: '+ color +'" title="'+ module._label +'">'+icon+'</div>'
	}
}
