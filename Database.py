#!/usr/bin/env python3

import os
import sys
from datetime import datetime, timezone
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from Formulas import get_lim, get_absolute_humidity


POINTS_FILE = r"/home/taupunkt/points.txt"


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

    def write_DHT22(self, key, temperature, humidity, dewpoint, error):
        point = (
            Point("DHT22")
            .tag("key", key)
            .field("temperature", x2float(temperature))
            .field("humidity", x2float(humidity))
            .field("dewpoint", x2float(dewpoint))
            .field("error", True if error else False)
        )
        self.write_point(point=point, time_precission="s")

    def write_RD200(self, radon, error):
        point = (
            Point("RD200")
            .field("radon", x2float(radon))
            .field("error", True if error else False)
        )
        self.write_point(point=point, time_precission="m")

    def write_ventilation(self, ventilation):
        point = (
            Point("ventilation")
            .field("radon_request", True if ventilation["radon_request"] else False)
            .field("humidity_request", True if ventilation["humidity_request"] else False)
            .field("dewpoint_granted", True if ventilation["dewpoint_granted"] else False)
            .field("internal_temp_granted", True if ventilation["internal_temp_granted"] else False)
            .field("external_temp_granted", True if ventilation["external_temp_granted"] else False)
        )
        self.write_point(point=point, time_precission="s")

    def write_switches(self, switches):
        point = (
            Point("switches")
            .field("out_fan_on", True if switches["out_fan_on"] else False)
            .field("in_fan_on", True if switches["in_fan_on"] else False)
        )
        self.write_point(point=point, time_precission="s")

    def backup_point(self, point):
        with open(POINTS_FILE, "a") as f:
            f.write("{} {}\n".format(point, int(datetime.now(timezone.utc).timestamp())))

    def write_point(self, point, time_precission):
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
                    failed.append(points)
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

    def test(self):
        query = 'from(bucket:"taupunkt_bucket")\
|> range(start: -1m)\
|> filter(fn:(r) => r._measurement == "DHT22")\
|> filter(fn:(r) => r.key == "NO")\
|> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")\
'
        tables = self.query_api.query(query)
        return tables


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
                db.write_DHT22(key=key, temperature=None, humidity=None, dewpoint=None, error=error)
            else:
                db.write_DHT22(key=key, temperature=20+i+offset, humidity=50+i+offset, dewpoint=10+i+offset, error=error)
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

    format = "%Y-%m-%dT%H:%M:%S.%dZ"
    start = datetime.fromtimestamp(0).strftime(format)
    stop = datetime.now(timezone.utc).strftime(format)
    stop = "2025-01-17T14:42:00Z"
    command = f"influx delete --bucket taupunkt_bucket --start {start} --stop {stop} --org taupunkt_org --token {token}".split()
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.stdout:
        print(result.stdout.decode(sys.stdout.encoding))
    if result.stderr:
        print(result.stderr.decode(sys.stderr.encoding))


def test():
    db = Database()
    tables = db.test()
    for table in tables:
        for record in table.records:
            print(type(record.values))
            for (k, v) in record.values.items():
                print(" ", k, v)
            if record.values["error"] == False:
                temperature = record.values["temperature"]
                humidity = record.values["humidity"]
                if "lim" not in record.values:
                    lim = get_lim(temperature)
                    print("  lim", lim)
                if "aH" not in record.values:
                    aH = get_absolute_humidity(temperature, humidity)
                    print("  aH", aH)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="InfluxDB Test")
    parser.add_argument('--create-test-data', action='store_true', help="Creates test data. Caution, do not execute when your system is in real use!")
    parser.add_argument('--delete-test-data', action='store_true', help="Delete test data. Caution, do not execute when your system is in real use!")
    parser.add_argument('--test', action='store_true', help="Temporary test function.")
    args = parser.parse_args()
    if (args.create_test_data == False) and (args.delete_test_data == False) and (args.test == False):
        parser.print_help()
    if args.create_test_data:
        create_test_data()
    if args.delete_test_data:
        delete_test_data()
    if args.test:
        test()


if __name__ == '__main__':
    main()
