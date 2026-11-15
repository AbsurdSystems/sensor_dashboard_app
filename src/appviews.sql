

DROP VIEW IF EXISTS SensorReadingsView;
CREATE VIEW SensorReadingsView AS
select c3.sensor_name, b2.measure_id, b2.measure_name, ifnull(b2.description, b2.measure_name) description, b2.measure_type, a1.reading_value, b2.min_val, b2.max_val,
       CAST(julianday('now') - julianday(a1.reading_ts) AS INTEGER) AS days_since,
       a1.reading_ts
from SensorReadings a1
join MeasureInfo b2 on (a1.measure_id = b2.measure_id)
join SensorInfo c3 on (b2.sensor_id = c3.sensor_id);

DROP VIEW IF EXISTS CurrentSensorsView;
CREATE VIEW CurrentSensorsView AS
select c3.sensor_name, b2.measure_id, b2.measure_name, ifnull(b2.description, b2.measure_name) description, b2.measure_type, a1.reading_value, b2.min_val, b2.max_val, a1.reading_ts
from SensorReadings a1
join MeasureInfo b2 on  (a1.measure_id = b2.measure_id)
join SensorInfo c3 on (b2.sensor_id = c3.sensor_id)
where a1.reading_ts = (select max(t1.reading_ts) from SensorReadings t1 where t1.measure_id = a1.measure_id);


