#!/usr/bin/env python3

import os
import sys
from datetime import datetime, timezone
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from Formulas import get_lim, get_absolute_humidity


POINTS_FILE = r"/home/taupunkt/points.txt"
EXPORT_FILE = r"/home/taupunkt/points-export.txt"


def x2float(x):
    try:
        x = float(x)
    except:
        x = float("NaN")
    return x


class Database():
    def __init__(self, url="http://localhost:8086", org="taupunkt_org", bucket="taupunkt_bucket", token_file=r"/home/taupunkt/influxdb.python.token"):
        self.url = url
        self.org = org
        self.bucket = bucket
        if os.path.isfile(token_file):
            with open(token_file) as f:
                self.token = f.read().strip()
        else:
            sys.exit("token file '{}' missing".format(token_file))

        self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.client.query_api()

    def write_DHT22(self, key, temperature, rH, dewpoint, aH, lim, error):
        point = (
            Point("DHT22")
            .tag("key", key)
            .field("temperature", x2float(temperature))
            .field("rH", x2float(rH))
            .field("dewpoint", x2float(dewpoint))
            .field("aH", x2float(aH))
            .field("lim", x2float(lim))
            .field("error", True if error else False)
            .time(datetime.now(timezone.utc).replace(microsecond=0))
        )
        self.write_point(point=point, time_precission="s")

    def export_DHT22(self):
        format = "%Y-%m-%dT%H:%M:%S.%fZ"
        start = datetime.fromtimestamp(0).strftime(format)
        query = f'from(bucket:"taupunkt_bucket")\
|> range(start: {start})\
|> filter(fn:(r) => r._measurement == "DHT22")\
|> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")\
'
        tables = self.query_api.query(query)
        with open(EXPORT_FILE, "a") as f:
            for table in tables:
                for record in table.records:
                    # old format
                    if "humidity" in record.values:
                        humidity = record.values["humidity"]
                    else:
                        humidity = None

                    # new format
                    if "rH" in record.values:
                        rH = record.values["rH"]
                    else:
                        rH = None

                    # select the right one
                    if (rH is None) and (humidity is not None):
                        rH = humidity

                    temperature = record.values["temperature"]
                    lim = None
                    aH = None
                    if temperature is not None:
                        lim = get_lim(temperature)
                        if rH is not None:
                            aH = get_absolute_humidity(temperature, rH)

                    point = '{},key={} '.format(
                        record.values["_measurement"],
                        record.values["key"]
                    )
                    if temperature is not None:
                        point += 'temperature={},'.format(temperature)
                    if rH is not None:
                        point += 'rH={},'.format(rH)
                    if record.values["dewpoint"] is not None:
                        point += 'dewpoint={},'.format(record.values["dewpoint"])
                    if aH is not None:
                        point += 'aH={},'.format(aH)
                    if lim is not None:
                        point += 'lim={},'.format(lim)
                    point += 'error={}'.format(True if record.values["error"] else False)
                    point += ' {}\n'.format(int(record.values["_time"].timestamp()))
                    f.write(point)

    def write_RD200(self, radon, error):
        point = (
            Point("RD200")
            .field("radon", x2float(radon))
            .field("error", True if error else False)
            .time(datetime.now(timezone.utc).replace(microsecond=0))
        )
        self.write_point(point=point, time_precission="m")

    def export_RD200(self):
        format = "%Y-%m-%dT%H:%M:%S.%fZ"
        start = datetime.fromtimestamp(0).strftime(format)
        query = f'from(bucket:"taupunkt_bucket")\
|> range(start: {start})\
|> filter(fn:(r) => r._measurement == "RD200")\
|> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")\
'
        tables = self.query_api.query(query)
        with open(EXPORT_FILE, "a") as f:
            for table in tables:
                for record in table.records:
                    point = '{} '.format(
                        record.values["_measurement"],
                    )
                    if record.values["radon"] is not None:
                        point += 'radon={},'.format(record.values["radon"])
                    point += 'error={}'.format(True if record.values["error"] else False)
                    point += ' {}\n'.format(int(record.values["_time"].timestamp()))
                    f.write(point)

    def write_ventilation(self, ventilation):
        point = (
            Point("ventilation")
            .field("radon_request", True if ventilation["radon_request"] else False)
            .field("humidity_request", True if ventilation["humidity_request"] else False)
            .field("dewpoint_granted", True if ventilation["dewpoint_granted"] else False)
            .field("internal_temp_granted", True if ventilation["internal_temp_granted"] else False)
            .field("external_temp_granted", True if ventilation["external_temp_granted"] else False)
            .time(datetime.now(timezone.utc).replace(microsecond=0))
        )
        self.write_point(point=point, time_precission="s")

    def export_ventilation(self):
        format = "%Y-%m-%dT%H:%M:%S.%fZ"
        start = datetime.fromtimestamp(0).strftime(format)
        query = f'from(bucket:"taupunkt_bucket")\
|> range(start: {start})\
|> filter(fn:(r) => r._measurement == "ventilation")\
|> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")\
'
        tables = self.query_api.query(query)
        with open(EXPORT_FILE, "a") as f:
            for table in tables:
                for record in table.records:
                    point = '{} '.format(
                        record.values["_measurement"],
                    )
                    point += 'radon_request={},'.format(True if record.values["radon_request"] else False)
                    point += 'humidity_request={},'.format(True if record.values["humidity_request"] else False)
                    point += 'dewpoint_granted={},'.format(True if record.values["dewpoint_granted"] else False)
                    point += 'internal_temp_granted={},'.format(True if record.values["internal_temp_granted"] else False)
                    point += 'external_temp_granted={}'.format(True if record.values["external_temp_granted"] else False)
                    point += ' {}\n'.format(int(record.values["_time"].timestamp()))
                    f.write(point)

    def write_switches(self, switches):
        point = (
            Point("switches")
            .field("out_fan_on", True if switches["out_fan_on"] else False)
            .field("in_fan_on", True if switches["in_fan_on"] else False)
            .time(datetime.now(timezone.utc).replace(microsecond=0))
        )
        self.write_point(point=point, time_precission="s")

    def export_switches(self):
        format = "%Y-%m-%dT%H:%M:%S.%fZ"
        start = datetime.fromtimestamp(0).strftime(format)
        query = f'from(bucket:"taupunkt_bucket")\
|> range(start: {start})\
|> filter(fn:(r) => r._measurement == "switches")\
|> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")\
'
        tables = self.query_api.query(query)
        with open(EXPORT_FILE, "a") as f:
            for table in tables:
                for record in table.records:
                    point = '{} '.format(
                        record.values["_measurement"],
                    )
                    point += 'out_fan_on={},'.format(True if record.values["out_fan_on"] else False)
                    point += 'in_fan_on={}'.format(True if record.values["in_fan_on"] else False)
                    point += ' {}\n'.format(int(record.values["_time"].timestamp()))
                    f.write(point)

    def backup_point(self, point):
        with open(POINTS_FILE, "a") as f:
            f.write("{}\n".format(point))

    def write_point(self, point, time_precission):
        print(point)
        try:
            self.write_api.write(bucket=self.bucket, org=self.org, record=point, write_precision=WritePrecision.S, time_precission=time_precission)
            self.rewrite_points() # it worked, check whether there is something to rewrite
        except Exception as e:
            print(e)
            self.backup_point(point)

    def rewrite_point(self, point):
        try:
            if point.startswith("RD200"):
                time_precission="m"
            else:
                time_precission="s"
            self.write_api.write(bucket=self.bucket, org=self.org, record=point, write_precision=WritePrecision.S, time_precission=time_precission)
            return True
        except Exception as e:
            print(e)
            return False

    def rewrite_points(self):
        if os.path.isfile(POINTS_FILE):
            points = []
            failed = []
            with open(POINTS_FILE, 'r') as f:
                data = f.read().split('\n')
                for line in data:
                    if line.strip():
                        points.append(line.strip())
            for point in points:
                if not self.rewrite_point(point):
                    failed.append(point)
            if failed:
                print("ERROR: These could not be written")
                with open(POINTS_FILE, "W") as f:
                    for point in failed:
                        print(point)
                        f.write("{}\n".format(point))
            else:
                try:
                    os.remove(POINTS_FILE)
                except Exception as e:
                    print(e)

    def import_all(self):
        if os.path.isfile(EXPORT_FILE):
            with open(POINTS_FILE, "a") as f_out:
                with open(EXPORT_FILE, 'r') as f_in:
                    lines = f_in.readlines(10)
                    while lines:
                        for line in lines:
                            point = line.strip()
                            if point:
                                if not self.rewrite_point(point):
                                    f_out.write("{}\n".format(point))
                        lines = f_in.readlines(10)


def create_test_data():
    import time
    db = Database()
    toggle = True
    for i in range(10):
        if 3 == i:
            error = True
        else:
            error = False
        offset = 0
        for key in ["ext", "NO", "SO", "SW", "NW"]:
            if error:
                db.write_DHT22(key=key, temperature=None, rH=None, dewpoint=None, aH=None, lim=None, error=error)
            else:
                db.write_DHT22(key=key, temperature=20+i+offset, rH=50+i+offset, dewpoint=10+i+offset, aH=10+i+offset, lim=30+i+offset, error=error)
        if 0 == i % 3:
            if error:
                db.write_RD200(radon=200+i, error=error)
            else:
                db.write_RD200(radon=200+i, error=error)

        db.write_ventilation({
            "radon_request": toggle,
            "humidity_request": toggle,
            "dewpoint_granted": toggle,
            "internal_temp_granted": toggle,
            "external_temp_granted": toggle,
        })

        db.write_switches({
            "out_fan_on": toggle,
            "in_fan_on": toggle,
        })
        toggle = not toggle
        time.sleep(20)


def delete_test_data():
    import subprocess
    from datetime import datetime, timezone
    token_file=r"/home/taupunkt/influxdb.python.token"
    if os.path.isfile(token_file):
        with open(token_file) as f:
            token = f.read().strip()
    else:
        sys.exit("token file '{}' missing".format(token_file))

    format = "%Y-%m-%dT%H:%M:%S.%fZ"
    start = "1900-01-01T00:00:00.000Z"
    stop = datetime.now(timezone.utc).strftime(format)
    command = f"influx delete --bucket taupunkt_bucket --start {start} --stop {stop} --org taupunkt_org --token {token}".split()
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.stdout:
        print(result.stdout.decode(sys.stdout.encoding))
    if result.stderr:
        print(result.stderr.decode(sys.stderr.encoding))


def export_bucket():
    if os.path.isfile(EXPORT_FILE):
        os.remove(EXPORT_FILE)
    db = Database()
    db.export_DHT22()
    db.export_RD200()
    db.export_ventilation()
    db.export_switches()


def import_bucket():
    db = Database()
    db.import_all()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="InfluxDB Test")
    parser.add_argument('--create-test-data', action='store_true', help="Creates test data. Caution, do not execute when your system is in real use!")
    parser.add_argument('--delete-test-data', action='store_true', help="Delete test data. Caution, do not execute when your system is in real use!")
    parser.add_argument('--export-bucket', action='store_true', help="export bucket (old format and enhance with aH and lim).")
    parser.add_argument('--import-bucket', action='store_true', help="import bucket (delete and re-create taupunkt_bucket before execution)")
    args = parser.parse_args()
    if (args.create_test_data == False) and (args.delete_test_data == False) and (args.export_bucket == False) and (args.import_bucket == False):
        parser.print_help()
    if args.create_test_data:
        create_test_data()
    if args.delete_test_data:
        delete_test_data()
    if args.export_bucket:
        export_bucket()
    if args.import_bucket:
        import_bucket()


if __name__ == '__main__':
    main()
