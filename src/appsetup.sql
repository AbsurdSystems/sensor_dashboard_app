

--DROP TABLE SensorInfo;
CREATE TABLE SensorInfo (sensor_id INTEGER PRIMARY KEY, sensor_name TEXT, identifier TEXT, description TEXT);
--DROP TABLE MeasureInfo;
CREATE TABLE MeasureInfo (measure_id INTEGER PRIMARY KEY, sensor_id INTEGER, measure_name TEXT UNIQUE, measure_type TEXT, description TEXT, min_val REAL, max_val REAL);
--DROP TABLE SensorReadings;
CREATE TABLE SensorReadings (reading_id INTEGER PRIMARY KEY, measure_id INTEGER, reading_value REAL, reading_ts TEXT);


INSERT INTO UserList(user_id, username, password, full_name) values (NULL,'temp_admin','boombox','Temporary Administrator');
INSERT INTO GroupList(group_id, group_name, description) values (NULL,'Admin_Group','Administrators Group');
INSERT INTO GroupRoles (grole_id, group_id, provision_role) values (NULL, 1, 'administrator');
INSERT INTO GroupMembers(member_id, group_id, user_id) values (NULL, 1, 1);
INSERT INTO DB_Views(view_id, view_name, ref_name, menu_name, description) values (NULL,'adminmenuoptions','AdminMenuOptions','View Menu Options','List of menu options for administration');
INSERT INTO DB_Views(view_id, view_name, ref_name, menu_name, description) values (NULL,'userroleview','UserRoleView','View Users Roles','List of Users in database');
INSERT INTO DB_Views(view_id, view_name, ref_name, menu_name, description) values (NULL,'sensorreadings','SensorReadingsView','View Sensor Readings','List of Sensor readings');
INSERT INTO DB_Tables(table_id, table_name, ref_name, menu_name, description) values (NULL,'userlist','UserList','Edit User List','List of Users in database');
INSERT INTO DB_Tables(table_id, table_name, ref_name, menu_name, description) values (NULL,'grouplist','GroupList','Edit Group List','List of Groups in database');
INSERT INTO DB_Tables(table_id, table_name, ref_name, menu_name, description) values (NULL,'groupmembers','GroupMembers','Edit Group Members','Members of Groups');
INSERT INTO DB_Tables(table_id, table_name, ref_name, menu_name, description) values (NULL,'dbtables','DB_Tables','Edit Accessable Tables','List of Tables that can be accessed through interface');
INSERT INTO DB_Tables(table_id, table_name, ref_name, menu_name, description) values (NULL,'dbview','DB_Views','Edit Accessable Views','List of Views that can be accessed through interface');

INSERT INTO DB_Tables(table_id, table_name, ref_name, menu_name, description) values (NULL,'sensorinfo','SensorInfo','Edit Available Sensors','List of Sensors that can send readings to server');
INSERT INTO DB_Tables(table_id, table_name, ref_name, menu_name, description) values (NULL,'measureinfo','MeasureInfo','Edit Sensor Measures','List of Measures that can be saved from sensor readings');

