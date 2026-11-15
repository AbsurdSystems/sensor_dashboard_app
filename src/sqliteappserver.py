import asyncio
import io
import sys
import os
import base64
import json
import sqlite3
from cryptography import fernet
from aiohttp import web
from aiohttp_session import setup, get_session, session_middleware
from aiohttp_session.cookie_storage import EncryptedCookieStorage

#headers={"Authorization": "Basic bG9naW46cGFzcw=="}
#async with aiohttp.ClientSession(headers=headers) as session:
#    async with session.get("http://httpbin.org/headers") as r:
#        json_body = await r.json()
#        assert json_body['headers']['Authorization'] == \
#            'Basic bG9naW46cGFzcw=='
#
#auth = BasicAuth(login="...", password="...")
#async with ClientSession(auth=auth) as session:

# For creating a long running 
#async def long_running_task():
#    print("Starting long-running task...")
#    await asyncio.sleep(5)  # Simulate some work
#    print("Long-running task finished.")
#
#async def handler(request):
#    asyncio.create_task(long_running_task())
#    return web.Response(text="Task initiated in background.")



### BACKGROUND TASKS ############################################################

#async def long_running_task(task_count):
#	print(f"Starting long-running task... {task_count}")
#	await asyncio.sleep(60)  # Simulate some work
#	print(f"Long-running task finished. {task_count}")

async def background_worker():
	counter = 0
	while True:
		#asyncio.create_task(long_running_task(counter))
		print(f"Background task is running... {counter}")
		counter += 1
		await asyncio.sleep(10)  # Simulate some work

async def bgtasks_startup(app):
	app['background_task'] = asyncio.create_task(background_worker())

async def bgtasks_cleanup(app):
	app['background_task'].cancel()
	await app['background_task'] # Await cancellation to ensure cleanup

### HELPER FUNCTIONS ############################################################


async def run_command(command, args):
	try:
		process = await asyncio.create_subprocess_exec(command,*args,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
		stdout, stderr = await process.communicate()
		output = stdout.decode().strip()
		error = stderr.decode().strip()
		if process.returncode == 0:
			return {"returncode": process.returncode, "error": "", "output": output} 
		else:
			return {"returncode": process.returncode, "error": "error", "output": output}
	except Exception as e:
		return {"returncode": 500, "error": f"Error running subprocess: {e}", "output": ""}

def run_template_code(template_code, template_globals = None):
	# Create a StringIO object to capture output
	captured_output = io.StringIO()
	# Save the original stdout
	original_stdout = sys.stdout
	try:
		sys.stdout = captured_output
		exec(template_code.strip(), template_globals)
	finally:
		sys.stdout = original_stdout
	return captured_output.getvalue()

def render_template(template_string, template_globals = None):
	new_html = ""
	curr_string = template_string
	string_parts = template_string.partition("{{")
	new_html += string_parts[0]
	while string_parts[1] == "{{":
		curr_string = string_parts[2]
		string_parts = curr_string.partition("}}")
		if(string_parts[1] != "}}"):
			raise Exception
		thecode = string_parts[0]
		curr_string = string_parts[2]
		#### Run the code
		new_html += run_template_code(thecode, template_globals)
		string_parts = curr_string.partition("{{")
		new_html += string_parts[0]
	return new_html


class Site_Request_Handler:

	def __init__(self, static_dir):
		print("Serving static files at: ", static_dir)
		self.static_dirpath = static_dir
		pass

	async def fetch_session(self,request):
		return {"user_id": 1, "username": "nobody"}


	async def static_file(self,request):
		#session = await self.fetch_session(request)
		#file_path = os.path.join(os.getcwd(), 'static', request.match_info['subfolder'], request.match_info['filename'])
		file_path = os.path.join(self.static_dirpath, request.match_info['subfolder'], request.match_info['filename'])
		response = web.FileResponse(file_path)
		response.headers['Cache-Control'] = 'max-age=0'
		#response.headers['Content-Disposition'] = 'attachment; filename="report.csv"'
		return response


	async def rootpage(self,request):
		session = await self.fetch_session(request)
		return web.Response(text="Test Page, nothing defined yet")

#	async def rootpage(self,request):
#		session = await self.fetch_session(request)
#		file_path = os.path.join(os.getcwd(), 'static', 'index.html')
#		with open(file_path, 'r') as template_file:
#			template_string=template_file.read()
#			expanded_template=render_template(template_string, {'username': session["username"]})
#		response = web.Response(text=expanded_template, content_type='text/html')
#		response.headers['Cache-Control'] = 'max-age=0'
#		##response.headers['Content-Disposition'] = 'attachment; filename="report.csv"'
#		return response

	async def run_lsblk(self,request):
		#result = await run_command("ls",["-lh","./"])
		result = await run_command("lsblk",["--json","-o","NAME,KNAME,PATH,TYPE,FSTYPE,LABEL,PARTLABEL,MOUNTPOINT,FSSIZE"])
		if(result['returncode'] == 0):
			return web.Response(text=f'{result["output"]}', content_type='text/json')
		else:
			return web.Response(text=f'Process output:\n{result["returncode"]}\n{result["error"]}')


	def get_static_routes(self):
		return [web.get('/', self.rootpage),
				web.get('/lsblk', self.run_lsblk),
				web.get('/static/{subfolder}/{filename}', self.static_file)]



### REQUEST HANDLER FUNCTIONS ###################################################

class SqliteApp_Request_Handler(Site_Request_Handler):

	def __init__(self, static_dir, dbfilename):
		super().__init__(static_dir)
		self.db_filename = dbfilename
		self.setup()

	async def fetch_session(self,request):
		session = await get_session(request)
		user_id = session.get('user_id')
		if not user_id:
			raise web.HTTPFound("/login")
		return {"user_id": user_id, "username": session.get('username')}

	def connect_db(self):
		self.dbconn = sqlite3.connect(self.db_filename)
		self.dbconn.row_factory = sqlite3.Row

	def close_db(self):
		self.dbconn.close()

	def setup(self):
		self.connect_db() 
		c = self.dbconn.cursor()
		try:
			c.execute("select user_id, username, full_name from UserList;")
			user_info= c.fetchone()
			c.close()
			self.close_db() 
		except:
			c.close()
			print("Resetting the schemas")
			self.build_system_tables()
			self.build_setup_scripts()
			self.close_db() 

	def build_system_tables(self):
		c=self.dbconn.cursor()
		result = True
		try:
			c.execute("DROP TABLE UserList;")
			c.execute("DROP TABLE GroupList;")
			c.execute("DROP TABLE GroupMembers;")
			c.execute("DROP TABLE GroupRoles;")
			c.execute("DROP TABLE TableGroupGrants;")
			c.execute("DROP TABLE ViewGroupGrants;")
			#c.execute("DROP TABLE UserRoles;")
			c.execute("DROP TABLE DB_Views;")
			c.execute("DROP TABLE DB_Tables;")
			c.execute("DROP VIEW AdminMenuOptions;")
			c.execute("DROP VIEW UserRoleView;")
			c.execute("DROP VIEW UserTableGrantView;")
			c.execute("DROP VIEW UserViewGrantView;")
		except:
			pass

		c.execute("CREATE TABLE UserList (user_id INTEGER PRIMARY KEY, username  TEXT, password  TEXT, full_name TEXT);")
		c.execute("CREATE TABLE GroupList (group_id INTEGER PRIMARY KEY, group_name TEXT, description TEXT);")
		c.execute("CREATE TABLE GroupMembers (member_id INTEGER PRIMARY KEY, group_id INTEGER, user_id INTEGER);")
		c.execute("CREATE TABLE GroupRoles (grole_id INTEGER PRIMARY KEY, group_id INTEGER, provision_role TEXT);")
		c.execute("CREATE TABLE TableGroupGrants (tgrant_id INTEGER PRIMARY KEY, group_id INTEGER, table_id INTEGER, grant_role TEXT);")
		c.execute("CREATE TABLE ViewGroupGrants (vgrant_id INTEGER PRIMARY KEY, group_id INTEGER, view_id INTEGER);")
		#c.execute("CREATE TABLE UserRoles (urole_id INTEGER PRIMARY KEY, user_id INTEGER, provision_role TEXT);")
		c.execute("CREATE TABLE DB_Views (view_id INTEGER PRIMARY KEY, view_name TEXT, ref_name TEXT, menu_name TEXT, description TEXT);")
		c.execute("CREATE TABLE DB_Tables (table_id INTEGER PRIMARY KEY, table_name TEXT, ref_name TEXT, menu_name TEXT, description TEXT);")

		c.execute("CREATE VIEW AdminMenuOptions as select 'View' type, view_name url_name, menu_name, description from DB_Views where menu_name is not NULL union select 'Table' type, table_name url_name, menu_name, description from DB_Tables where menu_name is not NULL order by 1 desc, 2 asc;")
		c.execute("CREATE VIEW UserRoleView as select a1.user_id, c3.provision_role from GroupMembers a1 join UserList b2 on (a1.user_id = b2.user_id) join GroupRoles c3 on (a1.group_id = c3.group_id);")
		c.execute("CREATE VIEW UserTableGrantView as select a1.user_id, c3.table_id, d4.provision_role, c3.grant_role from GroupMembers a1 join UserList b2 on (a1.user_id = b2.user_id) join TableGroupGrants c3 on (a1.group_id = c3.group_id) join GroupRoles d4 on (a1.group_id = d4.group_id);")
		c.execute("CREATE VIEW UserViewGrantView as select a1.user_id, c3.view_id, d4.provision_role, 'select' grant_role from GroupMembers a1 join UserList b2 on (a1.user_id = b2.user_id) join ViewGroupGrants c3 on (a1.group_id = c3.group_id) join GroupRoles d4 on (a1.group_id = d4.group_id);")

		#c.execute("INSERT INTO UserList(user_id, username, password, full_name) values (NULL,'temp_admin','boombox','Temporary Administrator');")
		#c.execute("INSERT INTO GroupList(group_id, group_name, description) values (NULL,'Admin_Group','Administrators Group');")
		#c.execute("INSERT INTO GroupRoles (grole_id, group_id, provision_role) values (NULL, 1, 'administrator');")
		#c.execute("INSERT INTO GroupMembers(member_id, group_id, user_id) values (NULL, 1, 1);")
		#c.execute("INSERT INTO DB_Views(view_id, view_name, ref_name, menu_name, description) values (NULL,'adminmenuoptions','AdminMenuOptions','View Menu Options','List of menu options for administration');")
		#c.execute("INSERT INTO DB_Views(view_id, view_name, ref_name, menu_name, description) values (NULL,'userroleview','UserRoleView','View Users Roles','List of Users in database');")
		#c.execute("INSERT INTO DB_Tables(table_id, table_name, ref_name, menu_name, description) values (NULL,'userlist','UserList','Edit User List','List of Users in database');")
		#c.execute("INSERT INTO DB_Tables(table_id, table_name, ref_name, menu_name, description) values (NULL,'grouplist','GroupList','Edit Group List','List of Groups in database');")
		#c.execute("INSERT INTO DB_Tables(table_id, table_name, ref_name, menu_name, description) values (NULL,'groupmembers','GroupMembers','Edit Group Members','Members of Groups');")
		c.close()
		self.dbconn.commit()

	def build_setup_scripts(self):
		self.build_sql_script("appsetup.sql")
		pass

	def build_sql_script(self, script_name):
		script_filepath = os.path.realpath(sys.argv[0])
		script_dir = os.path.dirname(script_filepath) 
		sql_scriptpath = os.path.join(script_dir, script_name)
		with open(sql_scriptpath,'r') as sql_file:	
			c=self.dbconn.cursor()
			sql_script = sql_file.read()
			try:
				c.executescript(sql_script)
			except:
				print("Failure to run custom SQL install script %s" % (script_name,))
				raise Exception
			c.close()
		self.dbconn.commit()
		pass


	def get_sqlite_routes(self):
		return [web.get('/login', self.login_page),
				web.post('/login', self.process_login),
				web.get('/logout', self.logout_page),
				web.get('/getroles', self.get_roles),
				web.get('/view/select/{viewname}', self.view_select),
				web.get('/view/describe/{viewname}', self.view_describe),
				web.get('/table/fetch/{tablename}', self.table_fetchrow),
				web.get('/table/delete/{tablename}', self.table_delete),
				web.post('/table/add/{tablename}', self.table_addrow),
				web.post('/table/update/{tablename}', self.table_update)]


	async def process_login(self,request):
		entry_data = await request.post()
		session = await get_session(request)
		username = entry_data['username']
		password = entry_data['password']
		self.connect_db() 	
		c=self.dbconn.cursor()
		c.execute("select user_id, username from UserList where username = ? and password = ?;", (username, password))
		row_data = c.fetchone()
		c.close()
		self.close_db() 
		if row_data is None:
			return web.Response(text="Invalid login")
		else:
			session['user_id'] = row_data['user_id']
			session['username'] = row_data['username']
			raise web.HTTPFound("/")	


	async def rootpage(self,request):
		session = await self.fetch_session(request)
		file_path = os.path.join(self.static_dirpath, 'index.html')
		with open(file_path, 'r') as template_file:
			template_string=template_file.read()
			expanded_template=render_template(template_string, {'username': session["username"]})
		response = web.Response(text=expanded_template, content_type='text/html')
		response.headers['Cache-Control'] = 'max-age=0'
		##response.headers['Content-Disposition'] = 'attachment; filename="report.csv"'
		return response


	async def logout_page(self,request):
		session = await get_session(request)
		session.clear()
		raise web.HTTPFound("/")
	
	async def login_page(self,request):
		file_path = os.path.join(self.static_dirpath, 'login.html')
		response = web.FileResponse(file_path)
		response.headers['Cache-Control'] = 'max-age=0'
		#response.headers['Content-Disposition'] = 'attachment; filename="report.csv"'
		return response		


	async def get_roles(self,request):
		session = await self.fetch_session(request)
		self.connect_db() 	
		c=self.dbconn.cursor()
		c.execute("select provision_role from UserRoleView where user_id = ?;",(session['user_id'],))
		user_roles = c.fetchall()
		c.close()
		self.close_db() 

		result_array = [row['provision_role'] for row in user_roles]
		response = web.json_response(result_array)
		response.headers['Cache-Control'] = 'max-age=0'
		return response


	def has_role(self, user_id, provision_role):	
		c = self.dbconn.cursor()
		c.execute("select user_id from UserRoleView where user_id = ? and provision_role = ?;",(user_id,provision_role))
		found_role = c.fetchone()
		c.close()
		if found_role is None:
			return False
		else:
			return True


	def get_view_reference(self, view_name, user_id):
		c = self.dbconn.cursor()
		c.execute("select view_id, ref_name from DB_Views where view_name = ?;",( view_name,))
		db_info= c.fetchone()
		c.close()
		if db_info is None:
			return self.get_table_reference(view_name, user_id, 'select')

		if not self.has_role(user_id, 'administrator'):
			c = self.dbconn.cursor()
			c.execute("select user_id from UserViewGrantView where user_id = ? and view_id = ? and provision_role in ('viewaccess','tableaccess');",(user_id, db_info['view_id']))
			grant_role = c.fetchone()
			c.close()
			if grant_role is None:
				self.close_db()
				raise web.HTTPUnauthorized(headers=None, reason=None, body=None, text=None, content_type=None)
		return db_info['ref_name']


	def get_table_reference(self, table_name, user_id, allowed_role):
		c = self.dbconn.cursor()
		c.execute("select table_id, ref_name from DB_Tables where table_name = ?;",( table_name,))
		db_info= c.fetchone()
		c.close()
		if db_info is None:
			self.close_db()
			raise web.HTTPNotFound(headers=None, reason=None, body=None, text=None, content_type=None)

		if not self.has_role(user_id, 'administrator'):
			c = self.dbconn.cursor()
			c.execute("select user_id from UserTableGrantView where user_id = ? and table_id = ? and grant_role = ? and provision_role = 'tableaccess';",(user_id, db_info['table_id'], allowed_role))
			grant_role = c.fetchone()
			c.close()
			if grant_role is None:
				self.close_db()
				raise web.HTTPUnauthorized(headers=None, reason=None, body=None, text=None, content_type=None)
		return db_info['ref_name']

	def get_refname_columns(self, ref_name):		
		#pragma table_info('UserList');
		c=self.dbconn.cursor()
		c.execute("pragma table_info("+ref_name+")")
		column_data = c.fetchall()
		c.close()
		column_dict = {}
		for row in column_data:
			# row.keys()
			if row['pk'] == 1:
				column_dict[row['name']] = 'PRIMARY_KEY'
			else:
				column_dict[row['name']] = row['type']
		return column_dict


	async def view_select(self,request):
		session = await self.fetch_session(request)
		view_name = request.match_info['viewname']
		self.connect_db() 	
		view_refname = self.get_view_reference(view_name,session['user_id'])
		view_columns = self.get_refname_columns(view_refname)
		filter_list = []
		value_list = []
		uniquekey_count = 0
		for column_name in view_columns:
			if column_name in request.rel_url.query:				
				filter_list.append("%s = ?" % (column_name,))
				value_list.append(request.rel_url.query[column_name])
		if(len(filter_list) > 0):
			filter_statement = " where "+" and ".join(filter_list)
		else:
			filter_statement = ""

		c=self.dbconn.cursor()
		c.execute("select * from %s%s" % (view_refname, filter_statement), value_list)
		view_data = c.fetchall()
		c.close()
		self.close_db() 

		result_array = [dict(row) for row in view_data]
		response = web.json_response(result_array)
		response.headers['Cache-Control'] = 'max-age=0'
		return response

	async def view_describe(self,request):
		session = await self.fetch_session(request)
		view_name = request.match_info['viewname']
		self.connect_db() 	
		view_refname = self.get_view_reference(view_name,session['user_id'])

		c=self.dbconn.cursor()
		c.execute("pragma table_info('%s')" % (view_refname,))
		view_data = c.fetchall()
		c.close()
		self.close_db() 

		result_array = [dict(row) for row in view_data]
		response = web.json_response(result_array)
		response.headers['Cache-Control'] = 'max-age=0'
		return response


	async def table_fetchrow(self,request):
		session = await self.fetch_session(request)
		table_name = request.match_info['tablename']
		self.connect_db() 	
		#if(len(request.rel_url.query) != 1):
		#	raise web.HTTPNotFound(headers=None, reason=None, body=None, text=None, content_type=None)
		table_refname = self.get_table_reference(table_name,session['user_id'],'select')
		table_columns = self.get_refname_columns(table_refname)
		filter_list = []
		value_list = []
		uniquekey_count = 0
		for column_name in table_columns:
			if column_name in request.rel_url.query and table_columns[column_name] == 'PRIMARY_KEY':				
				filter_list.append("%s = ?" % (column_name,))
				value_list.append(request.rel_url.query[column_name])
				uniquekey_count += 1
		if(uniquekey_count != 1):
			raise web.HTTPNotAcceptable(headers=None, reason="Unique key not found", body=None, text="Unique key not found", content_type=None)	
		filter_statement = " and ".join(filter_list)
		#print("Filter statement: (%s)" % (view_refname,))

		c=self.dbconn.cursor()
		c.execute("select * from %s where %s" % (table_refname, filter_statement), value_list)
		row_data = c.fetchone()
		c.close()
		self.close_db() 
		
		if row_data is None:	
			raise web.HTTPNoContent(headers=None, reason=None, body=None, text="No row found in table", content_type=None)
		response = web.json_response(dict(row_data))
		response.headers['Cache-Control'] = 'max-age=0'
		return response

	async def table_delete(self,request):
		session = await self.fetch_session(request)
		table_name = request.match_info['tablename']
		self.connect_db() 	
		table_refname = self.get_table_reference(table_name,session['user_id'],'delete')
		table_columns = self.get_refname_columns(table_refname)
		filter_list = []
		value_list = []
		uniquekey_count = 0
		for column_name in table_columns:
			if column_name in request.rel_url.query and table_columns[column_name] == 'PRIMARY_KEY':				
				filter_list.append("%s = ?" % (column_name,))
				value_list.append(request.rel_url.query[column_name])
				uniquekey_count += 1
		if(uniquekey_count != 1):
			raise web.HTTPNotAcceptable(headers=None, reason="Unique key not found", body=None, text="Unique key not found", content_type=None)	
		filter_statement = " and ".join(filter_list)

		c = self.dbconn.cursor()
		try:
			c.execute("delete from %s where %s;" % (table_refname,filter_statement), value_list)
			self.dbconn.commit()
		except:
			self.dbconn.rollback()
		c.close()
		self.close_db() 
		response = web.Response(text=f'Record Deleted')
		response.headers['Cache-Control'] = 'max-age=0'
		return response

	async def table_addrow(self,request):
		entry_data = await request.post()
		session = await self.fetch_session(request)
		table_name = request.match_info['tablename']
		self.connect_db() 

		#Build the column names and values from post data
		named_list = []
		param_list = []
		value_list = []
		table_refname = self.get_table_reference(table_name,session['user_id'],'addrow')
		table_columns = self.get_refname_columns(table_refname)
		for column_name in table_columns:
			if table_columns[column_name] == 'PRIMARY_KEY':
				named_list.append(column_name)
				param_list.append('NULL')
			elif column_name in entry_data:
				named_list.append(column_name)
				if(len(entry_data[column_name]) == 0):
					param_list.append('NULL')	
				else:	
					param_list.append('?')
					value_list.append(entry_data[column_name])
		named_list = ','.join(named_list)
		param_list = ','.join(param_list)

		c = self.dbconn.cursor()
		try:
			c.execute("INSERT INTO %s(%s) values (%s);" % (table_refname,named_list,param_list), value_list)
			self.dbconn.commit()
			c.close()
			self.close_db() 
			return web.Response(text="Row added")
		except:
			self.dbconn.rollback()
			c.close()
			self.close_db() 
			return web.Response(text="Failure to add row")


	async def table_update(self,request):
		entry_data = await request.post()
		session = await self.fetch_session(request)
		table_name = request.match_info['tablename']
		self.connect_db() 
		table_refname = self.get_table_reference(table_name,session['user_id'],'update')
		table_columns = self.get_refname_columns(table_refname)
		filter_list = []
		filter_value_list = []
		update_column_list = []
		update_value_list = []
		uniquekey_count = 0
		for column_name in table_columns:
			if column_name in request.rel_url.query and table_columns[column_name] == 'PRIMARY_KEY':				
				filter_list.append("%s = ?" % (column_name,))
				filter_value_list.append(request.rel_url.query[column_name])
				uniquekey_count += 1
			if column_name in entry_data:
				if(len(entry_data[column_name]) == 0):
					update_column_list.append("%s = NULL" % (column_name,))
				else:
					update_column_list.append("%s = ?" % (column_name,))
					update_value_list.append(entry_data[column_name])
		if(uniquekey_count != 1):
			raise web.HTTPNotAcceptable(headers=None, reason="Unique key not found", body=None, text="Unique key not found", content_type=None)	
		filter_statement = " and ".join(filter_list)
		update_set_statement = ", ".join(update_column_list)
		update_value_list.extend(filter_value_list)
		c = self.dbconn.cursor()
		try:
			c.execute("update %s set %s where %s;" % (table_refname,update_set_statement,filter_statement), update_value_list)
			self.dbconn.commit()
			c.close()
			self.close_db() 
			return web.Response(text="Row updated")
		except:
			self.dbconn.rollback()
			c.close()
			self.close_db() 
			return web.Response(text="Failure to update row")




async def prepare_app():
	app = web.Application()
	# secret_key must be 32 url-safe base64-encoded bytes
	fernet_key = fernet.Fernet.generate_key()
	secret_key = base64.urlsafe_b64decode(fernet_key)
	setup(app, EncryptedCookieStorage(secret_key))

	#main = SqliteApp_Request_Handler('test.db')
	main = CustomApp_Request_Handler('test.db')
	app.add_routes(main.get_static_routes())
	app.add_routes(main.get_sqlite_routes())
	#app.add_routes(main.get_app_routes())
	
	#app.on_startup.append(bgtasks_startup)
	#app.on_cleanup.append(bgtasks_cleanup)
	return app



##app = web.Application()

#if __name__ == '__main__':
#	app = prepare_app()
#	web.run_app(app, host='0.0.0.0', port=8080)


