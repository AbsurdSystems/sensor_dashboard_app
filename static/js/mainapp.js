

/*
class Car {
  constructor(brand) {
    this.carname = brand;
  }
  present() {
    return 'I have a ' + this.carname;
  }
}

class Model extends Car {
  constructor(brand, mod) {
    super(brand);
    this.model = mod;
  }
  show() {
    return this.present() + ', it is a ' + this.model;
  }
}


let myCar = new Model("Ford", "Mustang");
document.getElementById("demo").innerHTML = myCar.show();
*/


function getTimeStamp() 
{
   var now = new Date();
   let ampm = ((now.getHours() > 12) ? 'PM' : 'AM');
   return ((now.getMonth() + 1) + '/' +
          (now.getDate()) + '/' +
           now.getFullYear() + " " +
           now.getHours() + ':' +
           ((now.getMinutes() < 10)
               ? ("0" + now.getMinutes())
                : (now.getMinutes())) + ':' +
            ((now.getSeconds() < 10)
                ? ("0" + now.getSeconds())
                : (now.getSeconds())) + ampm);
}


class WebApp
{ 

	constructor(appname, loadarea = "mainwindow")
	{
		this.appobjname = appname;
		this.counter = 1;
		this.htmlarea = `#${loadarea}`;
		console.log(`Created WebApp: ${appname} ${this.htmlarea}`);
	}

	close_all_menus()
	{
		$(".dropdown-content").css("display", "none");
	}

	open_dialog_box(box_content)
	{
		let the_html = "<div id=\"message_dialog_box\" class=\"dialog_box\">";
		//the_html = the_html.concat(`<p> Counter:${this.counter} </p>`);
		the_html = the_html.concat(box_content);
		the_html = the_html.concat("<button id=\"close_dialog_box\">Close</button>");
		the_html = the_html.concat("</div>");
		the_html = the_html.concat("<script>");
		the_html = the_html.concat("$(\"#close_dialog_box\").click(function() { $(\"#message_dialog_box\").remove() });")
		the_html = the_html.concat("</script>");
		this.counter += 1;
		console.log("Building the Dialog Box");
		$(this.htmlarea).append(the_html);
	}


}


class MainApp extends WebApp
{

	load_navigation_menu(loadarea)
	{
		let the_html = "<div class=\"dropdown\">";
		the_html = the_html.concat("<button id=\"dashboards_btn\" onclick=\'$(\"#dashboards_menu\").toggle();\' class=\"dropbtn\">Dashboards	<i class=\"fa fa-caret-down\"></i></button>");
		the_html = the_html.concat("<div id=\"dashboards_menu\" class=\"dropdown-content\">");
		the_html = the_html.concat(`<a href=\"#\" onclick=\"${this.appobjname}.load_diskinfo(); ${this.appobjname}.close_all_menus();\">Disk Information</a>`);
		the_html = the_html.concat("<a href=\"#\">Link B</a>");
		the_html = the_html.concat("<a href=\"#\">Link C</a>");	
		the_html = the_html.concat("</div></div>");
		$(`#${loadarea}`).append(the_html);
	}


	load_diskinfo(message=null)
	{
		$(this.htmlarea).html("<p><h3> Loading partition info now... </h3></p>");
		console.log("Opening disk partition page");
		let htmlarea = this.htmlarea;

		$.getJSON("/lsblk", function(data, status)
		{
			console.log("Displaying results");
			let the_html = "<p>";
			if(message === null)
			{
				let curr_ts = getTimeStamp();
				the_html = the_html.concat("Loaded values at ", curr_ts);
			}
			else
			{
				the_html = the_html.concat(message);
			}
			the_html = the_html.concat("</p><table class=\"trans_list\"><tr><th>Name</th><th>File System Type</th><th>Mount point</th></tr>");
			for (const blockdevice of data["blockdevices"])
			{
				for (const partition of blockdevice["children"])
				{
					the_html = the_html.concat("<tr><td>", partition.name ,"</td><td>", partition.fstype, "</td><td>", partition.mountpoint, "</td></tr>");
				}
			}
			the_html = the_html.concat("</table>");
			the_html = the_html.concat("<button id=\"open_testtable_dialog\">Open TestTable Dialog</button>");
			the_html = the_html.concat("<script>");
			the_html = the_html.concat("$(\"#open_testtable_dialog\").click(function() { console.log(\"Opening Dialog Box\"); theapp.open_dialog_box(\"<p>You have clicked a button</p>\"); });")
			the_html = the_html.concat("</script>");
			//open_dialog_box(); });
			$(htmlarea).html(the_html);

			console.log(`Loaded disk partition page: ${htmlarea}`);
		});
	}


	load_linechart(measure_name, description, measure_type, measurename_id, measurename_box, query_data)
	{
		const ctx = document.getElementById(measurename_id);
		const box = document.getElementById(measurename_box);
		let dash_labels = [];
		let dash_data = [];


		// Get the parent's actual dimensions
		const containerWidth = box.clientWidth;
		//const containerHeight = container.clientHeight;
		ctx.width = containerWidth;
		//canvas.height = containerHeight;

		for(let row of query_data)
		{
			dash_labels.push(row.reading_date);
			dash_data.push(row.average_value);
		} 

		new Chart(ctx, {
			type: 'line', // Specify the chart type
			data: {
				labels: dash_labels,
			datasets: [{
				label: `Chart: ${measure_type}`,
				data: dash_data,
			    fill: false,
			    borderColor: 'rgb(75, 192, 192)',
				tension: 0.1,
				borderWidth: 1
				}]
			},
			options: {
				plugins: {
					title: {
						display: true,
						text: description,
						padding: {
							top: 10,
							bottom: 30
						}
					}
				},
				scales: {
					y: {
						beginAtZero: false
					}
				}
			}
		});
	}

	generate_sensor_charts(measure_list)
	{
		let currentapp = this;
		let the_html = "<table style=\"width: 100%; border-collapse: separate; border-spacing: 0 10px;\">";
		for(const row of measure_list)
		{
			//the_html = the_html.concat("<tr><td>", measure_name, "</td></tr>");
			let measurename_id = `${row.measure_id}_chart`;
			let measurename_box = `${row.measure_name}_box`;
			the_html = the_html.concat("<tr style=\"width: 100%;\"><td id=\"",measurename_box,"\" style=\"width: 100%; background-color: white; border: 1px solid black;\">");
			the_html = the_html.concat("<canvas id=\"", measurename_id, "\" height=\"300px\"></canvas>");  
			the_html = the_html.concat("</td></tr>");
			$.getJSON(`/getmeasuredata/${row.measure_id}?days_since=20`, function(data, status)
			{	
				currentapp.load_linechart(row.measure_name, row.description, row.measure_type, measurename_id, measurename_box, data);
			});
		}		
		the_html = the_html.concat("</table>");
		$("#sensorgraphs_section").html(the_html);
	}

	request_current_sensors_data()
	{
		let currentapp = this;
		$.getJSON("/getcurrentstats", function(data, status)
		{	
			console.log("Displaying results");
			let the_html = "<table class=\"trans_list\">";
		
			the_html = the_html.concat("<tr><th>Sensor Name</th><th>Measure Name</th><th>Reading Value</th><th>Timestamp</th></tr>");
			for (const row of data)
			{
				the_html = the_html.concat("<tr><td>", row.sensor_name, "</td><td>", row.description, "</td><td>", row.reading_value, "</td><td>", row.reading_ts, "</td></tr>");
			}
			the_html = the_html.concat("</table>");
			$("#currentsensors_section").html(the_html);
			currentapp.generate_sensor_charts(data);
		});
	}


	home_dashboard()
	{
		let the_html = "<div>";
		the_html = the_html.concat(`<h3>Current Sensor Readings</h3>`);
		the_html = the_html.concat(`<p>These are the latest readings from all sensors</p>`);
		the_html = the_html.concat("<table class=\"button_bar\"><tr>");
		//the_html = the_html.concat("<td><button id=\"refresh_button\" onclick=\"request_current_sensors_data();\">Refresh</button></td></tr></table>");
		the_html = the_html.concat("<td><button id=\"refresh_button\">Refresh</button></td></tr></table>");
		the_html = the_html.concat("<div id=\"currentsensors_section\" class=\"panel_sub_section\"></div>");
		the_html = the_html.concat("<div id=\"sensorgraphs_section\" class=\"panel_sub_section\"></div>");
		the_html = the_html.concat("</div>");

		the_html = the_html.concat("<script>");
		the_html = the_html.concat("$(\"#refresh_button\").click(function() { theapp.request_current_sensors_data(); });");
		the_html = the_html.concat("<\/script>");

		console.log(the_html);

		console.log("Building the View Grid");
		$("#mainwindow").html(the_html);

		this.request_current_sensors_data();
	}

}


/*
let theapp = new MainApp();
let adminapp = new SqliteApp_AdminInterface("mainwindow");

$(document).ready(function() {

	globalThis.request_current_sensors_data = function()
	{
		$.getJSON("/getcurrentstats", function(data, status)
		{	
			console.log("Displaying results");
			let the_html = "<table class=\"trans_list\">";
			
			the_html = the_html.concat("<tr><th>Sensor Name</th><th>Sensor Name</th><th>Sensor Name</th><th>Sensor Name</th></tr>");
			for (const row of data)
			{
				the_html = the_html.concat("<tr><td>", row.sensor_name, "</td><td>", row.description, "</td><td>", row.reading_value, "</td><td>", row.reading_ts, "</td></tr>");
			}
			the_html = the_html.concat("</table>");
			$("#currentsensors_section").html(the_html);
		});
	}


	function home_dashboard()
	{
		let the_html = "<div>";
		the_html = the_html.concat(`<h3>Current Sensor Readings</h3>`);
		the_html = the_html.concat(`<p>These are the latest readings from all sensors</p>`);
		the_html = the_html.concat("<table class=\"button_bar\"><tr>");
		//the_html = the_html.concat("<td><button id=\"refresh_button\" onclick=\"request_current_sensors_data();\">Refresh</button></td></tr></table>");
		the_html = the_html.concat("<td><button id=\"refresh_button\">Refresh</button></td></tr></table>");
		the_html = the_html.concat("<div id=\"currentsensors_section\"></div>");
		the_html = the_html.concat("</div>");

		the_html = the_html.concat("<script>");
		the_html = the_html.concat("$(\"#refresh_button\").click(function() { request_current_sensors_data(); });");
		the_html = the_html.concat("<\/script>");

		console.log(the_html);

		console.log("Building the View Grid");
		$("#mainwindow").html(the_html);

		request_current_sensors_data();
	}

	theapp.load_navigation_menu();
    //theapp.load_diskinfo();
});
*/

