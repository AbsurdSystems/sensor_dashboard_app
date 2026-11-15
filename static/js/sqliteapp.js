

class SqliteApp_AdminInterface extends WebApp
{

	load_navigation_menu(roles, loadarea)
	{
		let appobjname = this.appobjname;
		if(roles.includes("administrator"))
		{
			$.getJSON("/view/select/adminmenuoptions", function(data, status)
			{	

				let the_html = "<div class=\"dropdown\">";
				the_html = the_html.concat("<button id=\"admin_btn\" onclick=\'$(\"#admin_menu\").toggle();\' class=\"dropbtn\">Administration<i class=\"fa fa-caret-down\"></i></button>");
				the_html = the_html.concat("<div id=\"admin_menu\" class=\"dropdown-content\">");

				for (const row of data)
				{
					console.log(row);
					let url_name = row.url_name;
					let menu_name = row.menu_name;
					let description = row.description;
					if(row["type"] == "View")
					{
						the_html = the_html.concat(`<a href=\"#\" onclick=\'${appobjname}.open_generic_view_window(\"${url_name}\",\"${menu_name}\",\"${description}\"); theapp.close_all_menus();\'>${menu_name}</a>`);
					}
					else
					{
						the_html = the_html.concat(`<a href=\"#\" onclick=\'${appobjname}.open_generic_table_window(\"${url_name}\",\"${menu_name}\",\"${description}\"); theapp.close_all_menus();\'>${menu_name}</a>`);
					}
				}

				/*the_html = the_html.concat(`<a href=\"#\" onclick=\'${this.appobjname}.open_generic_view_window(\"userlist\"); theapp.close_all_menus();\'>View Group Membership</a>`);
				the_html = the_html.concat(`<a href=\"#\" onclick=\'${this.appobjname}.open_generic_table_window(\"userlist\"); theapp.close_all_menus();\'>Edit User List</a>`);
				the_html = the_html.concat(`<a href=\"#\" onclick=\'${this.appobjname}.open_generic_table_window(\"grouplist\"); theapp.close_all_menus();\'>Edit Group List</a>`);*/
				the_html = the_html.concat("</div></div>");
				$(`#${loadarea}`).append(the_html);
			});
		}
	}


	request_generic_view_data(view_name)
	{
		let appobjname = this.appobjname;
		$.getJSON(`/view/describe/${view_name}`, function(data, status)
		{	
			let view_header_html = "";
			let primary_key_name = "";
			for (const row of data)
			{
				if(row["pk"] == 1)
				{
					primary_key_name = row["name"];
				}
				view_header_html = view_header_html.concat("<th>", row["name"], "</th>");
			}

			$.getJSON(`/view/select/${view_name}`, function(data, status)
			{	
				console.log("Displaying results");
				let the_html = "<table class=\"trans_list\">";
				the_html = the_html.concat("<tr>", view_header_html ,"</tr>");
				for (const row of data)
				{
					the_html = the_html.concat("<tr>");
					for(let column_name in row)
					{
						if(row[column_name] == null)
						{
							the_html = the_html.concat("<td></td>");
						}
						else
						{
							the_html = the_html.concat("<td>", row[column_name] ,"</td>");
						}
					}
                    the_html = the_html.concat("</tr>");
				}
				the_html = the_html.concat("</table>");
				$("#view_section").html(the_html);
			});
		});

	}


	open_generic_view_window(view_name, menu_name, description)
	{
		let the_html = "<div>";
		the_html = the_html.concat(`<h3>${menu_name}</h3>`);
		the_html = the_html.concat(`<p>${description}</p>`);
		the_html = the_html.concat("<table class=\"button_bar\"><tr>");
		the_html = the_html.concat("<td><button id=\"refresh_button\">Refresh</button></td></tr></table>");
		the_html = the_html.concat("<div id=\"view_section\"></div>");
		the_html = the_html.concat("</div>");

		the_html = the_html.concat("<script>");
		the_html = the_html.concat(`$(\"#refresh_button\").click(function() { ${this.appobjname}.request_generic_view_data(\"${view_name}\"); });`);
		the_html = the_html.concat("</script>");

		console.log("Building the View Grid");
		$(this.htmlarea).html(the_html);

		this.request_generic_view_data(view_name);
	}



	request_generic_table_data(table_name)
	{
		let appobjname = this.appobjname;
		$.getJSON(`/view/describe/${table_name}`, function(data, status)
		{	
			let table_header_html = "";
			let primary_key_name = "";
			for (const row of data)
			{
				if(row["pk"] == 1)
				{
					primary_key_name = row["name"];
				}
				table_header_html = table_header_html.concat("<th>", row["name"], "</th>");
			}
			table_header_html = table_header_html.concat("<th>Action</th>");

			$.getJSON(`/view/select/${table_name}`, function(data, status)
			{	
				console.log("Displaying results");
				let the_html = "<table class=\"trans_list\">";
				the_html = the_html.concat("<tr>", table_header_html ,"</tr>");
				for (const row of data)
				{
					the_html = the_html.concat("<tr>");
					for(let column_name in row)
					{
						if(row[column_name] == null)
						{
							the_html = the_html.concat("<td></td>");
						}
						else
						{
							the_html = the_html.concat("<td>", row[column_name] ,"</td>");
						}
					}
					//the_html = the_html.concat("</tr>");
					the_html = the_html.concat(`<td><a onclick=\'${appobjname}.open_edittablerow_dialog(\"`, table_name, "\",\"", primary_key_name, "\",\"", row[primary_key_name], "\");\'>Edit</a>");
                    the_html = the_html.concat(` | <a onclick=\'${appobjname}.open_deletetablerow_dialog(\"`, table_name, "\",\"", primary_key_name, "\",\"", row[primary_key_name], "\");\'>Delete</a></td></tr>");
				}
				the_html = the_html.concat("</table>");
				$("#table_section").html(the_html);
			});
		});

	}


	open_generic_table_window(table_name, menu_name, description)
	{
		let the_html = "<div>";
		the_html = the_html.concat(`<h3>${menu_name}</h3>`);
		the_html = the_html.concat(`<p>${description}</p>`);
		the_html = the_html.concat("<table class=\"button_bar\"><tr><td><button id=\"add_row_button\">Add Row</button></td>");
		the_html = the_html.concat("<td><button id=\"refresh_button\">Refresh</button></td></tr></table>");
		the_html = the_html.concat("<div id=\"table_section\"></div>");
		the_html = the_html.concat("</div>");

		the_html = the_html.concat("<script>");
		the_html = the_html.concat(`$(\"#add_row_button\").click(function() { ${this.appobjname}.open_addtablerow_dialog(\"${table_name}\"); });`);
		the_html = the_html.concat(`$(\"#refresh_button\").click(function() { ${this.appobjname}.request_generic_table_data(\"${table_name}\"); });`);
		the_html = the_html.concat("</script>");

		console.log("Building the UserList Editor");
		$(this.htmlarea).html(the_html);

		this.request_generic_table_data(table_name);
	}


	open_addtablerow_dialog(table_name)
	{
		let appobjname = this.appobjname;
		let the_html = "<div id=\"addrow_dialog_box\" class=\"dialog_box\">";
		the_html = the_html.concat(`<p> Add record for table ${table_name} </p>`);	
		the_html = the_html.concat(`<form id=\"table_addform\" action=\"/table/add/${table_name}\"></form>`);
		the_html = the_html.concat("<button id=\"submit_dialog_button\">Submit</button>");
		the_html = the_html.concat("<button id=\"close_dialog_button\">Close</button>");
		the_html = the_html.concat("</div>");
		the_html = the_html.concat("<script>");
		the_html = the_html.concat(`$(\"#submit_dialog_button\").click(function(event){event.preventDefault(); $.ajax({type: \"POST\", url: $(\"#table_addform\").attr(\"action\"), data: $(\"#table_addform\").serialize(), contentType: \"application/x-www-form-urlencoded\", cache: false, success: function(response) { $(\"#addrow_dialog_box\").remove(); ${appobjname}.request_generic_table_data(\"${table_name}\"); }}); });`);
		the_html = the_html.concat("$(\"#close_dialog_button\").click(function() { $(\"#addrow_dialog_box\").remove(); });");
		the_html = the_html.concat("</script>");
		console.log("Building the Dialog Box");
		$(this.htmlarea).append(the_html);

		$.getJSON(`/view/describe/${table_name}`, function(data, status)
		{	
			let the_html = "<table>";
			let primary_key_name = "";
			for (const row of data)
			{
				if(row["pk"] == 1)
				{
					primary_key_name = row["name"];
				}
				else
				{
					let column_name = row["name"];	
					the_html = the_html.concat(`<tr><td><label for=\"${column_name}\">${column_name}: </label></td><td><input type=\"text\" id=\"${column_name}\" name=\"${column_name}\"></td></tr>`);
				}
			}
			the_html = the_html.concat("</table>");
			$("#table_addform").append(the_html);
		});

	}


	open_edittablerow_dialog(table_name, primary_key_name, row_id)
	{
		let appobjname = this.appobjname;
		let the_html = "<div id=\"updaterow_dialog_box\" class=\"dialog_box\">";
		the_html = the_html.concat(`<p> Update record for table ${table_name} </p>`);	
		the_html = the_html.concat(`<form id=\"table_updateform\" action=\"/table/update/${table_name}?${primary_key_name}=${row_id}\"></form>`);
		the_html = the_html.concat("<button id=\"submit_dialog_button\">Submit</button>");
		the_html = the_html.concat("<button id=\"close_dialog_button\">Close</button>");
		the_html = the_html.concat("</div>");
		the_html = the_html.concat("<script>");
		the_html = the_html.concat(`$(\"#submit_dialog_button\").click(function(event){event.preventDefault(); $.ajax({type: \"POST\", url: $(\"#table_updateform\").attr(\"action\"), data: $(\"#table_updateform\").serialize(), contentType: \"application/x-www-form-urlencoded\", cache: false, success: function(response) { $(\"#updaterow_dialog_box\").remove(); ${appobjname}.request_generic_table_data(\"${table_name}\"); }}); });`);
		the_html = the_html.concat("$(\"#close_dialog_button\").click(function() { $(\"#updaterow_dialog_box\").remove(); });");
		the_html = the_html.concat("</script>");
		console.log("Building the Dialog Box");
		$(this.htmlarea).append(the_html);

		$.getJSON(`/view/describe/${table_name}`, function(data, status)
		{
			let the_html = "<table>";
			let table_info = data;
			for (const row of table_info)
			{
				let column_name = row["name"];	
				if(row["pk"] == 1)
				{
					the_html = the_html.concat(`<tr><td><label>${column_name}: </label></td><td>${row_id}</td></tr>`);
				}
				else
				{
					the_html = the_html.concat(`<tr><td><label for=\"${column_name}\">${column_name}: </label></td><td><input type=\"text\" id=\"${column_name}\" name=\"${column_name}\"></td></tr>`);
				}
			}
			the_html = the_html.concat("</table>");
			$("#table_updateform").append(the_html);

			$.getJSON(`/table/fetch/${table_name}?${primary_key_name}=${row_id}`, function(data, status)
			{
				for (const row of table_info)
				{
					if(row["pk"] != 1)
					{
						let column_name = row["name"];
						$(`#${column_name}`).val(data[column_name]);
					}
				}
			});
		});

	}


	open_deletetablerow_dialog(table_name, primary_key_name, row_id)
	{
		let the_html = "<div id=\"deleterow_dialog_box\" class=\"dialog_box\">";
		the_html = the_html.concat(`<p id=\"deleterow_message\"> Delete record for table ${table_name}? </p>`);	
		the_html = the_html.concat("<button id=\"delete_dialog_button\">Delete</button>");
		the_html = the_html.concat("<button id=\"close_dialog_button\">Close</button>");
		the_html = the_html.concat("</div>");
		the_html = the_html.concat("<script>");
		the_html = the_html.concat(`$(\"#delete_dialog_button\").click(function(event){event.preventDefault(); $.ajax({type: \"GET\", url: \"/table/delete/${table_name}?${primary_key_name}=${row_id}\", cache: false, success: function(response) { console.log(\"Delete completed\"); $(\"#deleterow_message\").html(response); $(\"#delete_dialog_button\").remove(); ${this.appobjname}.request_generic_table_data(\"${table_name}\"); }}); });`); 
		the_html = the_html.concat("$(\"#close_dialog_button\").click(function() { $(\"#deleterow_dialog_box\").remove(); });");
		the_html = the_html.concat("</script>");
		console.log("Building the Dialog Box");
		$(this.htmlarea).append(the_html);
	}

}



