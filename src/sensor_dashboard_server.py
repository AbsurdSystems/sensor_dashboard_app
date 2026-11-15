import asyncio
import io
import sys
import os
import base64
import json
import sqlite3
import optparse
from cryptography import fernet
from aiohttp import web
from aiohttp_session import setup, get_session, session_middleware
from aiohttp_session.cookie_storage import EncryptedCookieStorage

from sqliteappserver import SqliteApp_Request_Handler, render_template


class CustomApp_Request_Handler(SqliteApp_Request_Handler):

	async def check_session(self,request):
		session = await get_session(request)
		user_id = session.get('user_id')
		if not user_id:
			return None
		else:
			return {"user_id": user_id, "username": session.get('username')}

	async def rootpage(self,request):
		session = await self.check_session(request)
		if session is None:
			file_path = os.path.join(self.static_dirpath, 'public.html')
			print("Getting public html file: ", file_path)
			response = web.FileResponse(file_path)
			response.headers['Cache-Control'] = 'max-age=0'
			return response
		else:
			file_path = os.path.join(self.static_dirpath, 'index.html')
			with open(file_path, 'r') as template_file:
				template_string=template_file.read()
				expanded_template=render_template(template_string, {'username': session["username"]})
			response = web.Response(text=expanded_template, content_type='text/html')
			response.headers['Cache-Control'] = 'max-age=0'
			return response


	def build_setup_scripts(self):
		self.build_sql_script("appsetup.sql")
		self.build_sql_script("appviews.sql")
		pass


	def get_app_routes(self):
		return [web.get('/getcurrentstats', self.get_current_stats),
				web.get('/getmeasuredata/{measureid}', self.get_measure_data),
				web.post('/sensorreading', self.save_sensor_reading)]


	async def get_current_stats(self,request):
		self.connect_db() 	

		c=self.dbconn.cursor()
		c.execute("select sensor_name, measure_id, measure_name, description, measure_type, reading_value, reading_ts from CurrentSensorsView")
		stats_data = c.fetchall()
		c.close()
		self.close_db() 

		result_array = [dict(row) for row in stats_data]
		response = web.json_response(result_array)
		response.headers['Cache-Control'] = 'max-age=0'
		return response


	async def get_measure_data(self,request):
		measure_id = request.match_info['measureid']
		self.connect_db() 	
		view_refname = "SensorReadingsView"
		view_columns = self.get_refname_columns(view_refname)
		filter_list = ["measure_id = ?"]
		value_list = [measure_id]
		uniquekey_count = 0
		for column_name in view_columns:
			if column_name in request.rel_url.query:
				if column_name == 'days_since':
					filter_list.append("%s <= ?" % (column_name,))
					value_list.append(request.rel_url.query[column_name])
				else:
					filter_list.append("%s = ?" % (column_name,))
					value_list.append(request.rel_url.query[column_name])
		if(len(filter_list) > 0):
			filter_statement = " where "+" and ".join(filter_list)
		else:
			filter_statement = ""

		sql_statement = "select date(a1.reading_ts) reading_date, avg(a1.reading_value) average_value from %s a1%s group by date(a1.reading_ts);" % (view_refname, filter_statement,)
		c=self.dbconn.cursor()
		c.execute(sql_statement, value_list)
		view_data = c.fetchall()
		c.close()
		self.close_db() 

		result_array = [dict(row) for row in view_data]
		response = web.json_response(result_array)
		response.headers['Cache-Control'] = 'max-age=0'
		return response


	async def save_sensor_reading(self,request):
		entry_data = await request.post()
		#session = await self.fetch_session(request)
		self.connect_db() 
		
		#print("Entry_data: ", entry_data)

		if('identifier' in entry_data):
			c = self.dbconn.cursor()
			c.execute("select sensor_id from SensorInfo where identifier = ?;",(entry_data['identifier'],))
			fetched_row = c.fetchone()
			c.close()
			if fetched_row is None:
				self.close_db() 
				return web.Response(text="Sensor Identifier does not exist")
			else:
				sensor_id = fetched_row["sensor_id"]				

			for entry_name in entry_data:
				if entry_name != "identifier":
					c = self.dbconn.cursor()
					c.execute("select measure_id from MeasureInfo where sensor_id = ? and measure_name = ?;",(sensor_id, entry_name,))
					fetched_row = c.fetchone()
					c.close()
					if not fetched_row is None:
						c = self.dbconn.cursor()
						c.execute("INSERT INTO SensorReadings (reading_id, measure_id, reading_value, reading_ts) values (NULL,?,?,datetime('now','localtime'));",(fetched_row["measure_id"],entry_data[entry_name]))
						c.close()
	
			self.dbconn.commit()
			self.close_db() 
			return web.Response(text="Sensor readings saved")
		else:
			self.close_db() 
			return web.Response(text="Identifier not found in sensor posting")


	

#async def prepare_app():
#	app = web.Application()
#	# secret_key must be 32 url-safe base64-encoded bytes
#	fernet_key = fernet.Fernet.generate_key()
#	secret_key = base64.urlsafe_b64decode(fernet_key)
#	setup(app, EncryptedCookieStorage(secret_key))
#
#	main = CustomApp_Request_Handler('apprepo.db')
#	app.add_routes(main.get_static_routes())
#	app.add_routes(main.get_sqlite_routes())
#	app.add_routes(main.get_app_routes())
#	
#	#app.on_startup.append(bgtasks_startup)
#	#app.on_cleanup.append(bgtasks_cleanup)
#	return app


def main_program():
	argparse = optparse.OptionParser(description="Sensor Dashboard Server | Copyright 2026 by Michael Burns ",
												usage="usage: sensor_dashboard_server.py [options]",
												version="version 1.0")
	argparse.add_option("-s","--static",dest="static_dir",default="./static",help="Mode: (verify,change)")
	argparse.add_option("-d","--dbfile",dest="dbfilename",default="apprepo.db",help="Location of SQLite DB file")
	(options, args) = argparse.parse_args()

	#configfilename = os.path.abspath(options.configfilename)
	static_directory = os.path.abspath(options.static_dir)
	db_filename = os.path.abspath(options.dbfilename)
	
	app = web.Application()
	# secret_key must be 32 url-safe base64-encoded bytes
	fernet_key = fernet.Fernet.generate_key()
	secret_key = base64.urlsafe_b64decode(fernet_key)
	setup(app, EncryptedCookieStorage(secret_key))

	main = CustomApp_Request_Handler(static_directory, db_filename)
	command = args[0]
	if command == "execsql":
		main.connect_db() 	
		main.build_sql_script(args[1])
		main.close_db() 	
	elif command == "run":
		app.add_routes(main.get_static_routes())
		app.add_routes(main.get_sqlite_routes())
		app.add_routes(main.get_app_routes())
		#app.on_startup.append(bgtasks_startup)
		#app.on_cleanup.append(bgtasks_cleanup)
		web.run_app(app, host='0.0.0.0', port=8080)
	else:
		print("*** Invalid command used for server program")


if __name__ == '__main__':
	main_program()
#	script_filepath = os.path.realpath(sys.argv[0])
#	script_dir = os.path.dirname(script_filepath) 
#	print("Script Filepath: ", script_filepath)
#	print("Script Directory: ", script_dir)


