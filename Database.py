#!/usr/bin/env python3

import os
import sys
from datetime import datetime, timezone
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS


POINTS_FILE = r"/home/taupunkt/points.txt"


def backup_point(point):
    with open(POINTS_FILE, "a") as f:
        f.write("{} {}\n".format(point, int(datetime.now(timezone.utc).timestamp())))


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

    def write_DHT22(self, key, temperature, humidity, dewpoint, error):
        point = (
            Point("DHT22")
            .tag("key", key)
            .field("temperature", x2float(temperature))
            .field("humidity", x2float(humidity))
            .field("dewpoint", x2float(dewpoint))
            .field("error", True if error else False)
        )
        try:
            self.write_api.write(bucket=self.bucket, org=self.org, record=point, write_precision=WritePrecision.S, time_precission="s")
        except Exception as e:
            print(e)
            backup_point(point)

    def write_RD200(self, radon, error):
        point = (
            Point("RD200")
            .field("radon", x2float(radon))
            .field("error", True if error else False)
        )
        try:
            self.write_api.write(bucket=self.bucket, org=self.org, record=point, write_precision=WritePrecision.S, time_precission="m")
        except Exception as e:
            print(e)
            backup_point(point)

    def write_ventilation(self, ventilation):
        point = (
            Point("ventilation")
            .field("radon_request", True if ventilation["radon_request"] else False)
            .field("humidity_request", True if ventilation["humidity_request"] else False)
            .field("dewpoint_granted", True if ventilation["dewpoint_granted"] else False)
            .field("internal_temp_granted", True if ventilation["internal_temp_granted"] else False)
            .field("external_temp_granted", True if ventilation["external_temp_granted"] else False)
        )
        try:
            self.write_api.write(bucket=self.bucket, org=self.org, record=point, write_precision=WritePrecision.S, time_precission="s")
        except Exception as e:
            print(e)
            backup_point(point)

    def write_switches(self, switches):
        point = (
            Point("switches")
            .field("out_fan_on", True if switches["out_fan_on"] else False)
            .field("in_fan_on", True if switches["in_fan_on"] else False)
        )
        try:
            self.write_api.write(bucket=self.bucket, org=self.org, record=point, write_precision=WritePrecision.S, time_precission="s")
        except Exception as e:
            print(e)
            backup_point(point)

    def write_point(self, point):
        try:
            self.write_api.write(bucket=self.bucket, org=self.org, record=point, write_precision=WritePrecision.S, time_precission="s")
            return True
        except Exception as e:
            print(e)
            return False


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
            print(int(time.time()), end=": ")
            if error:
                db.write_DHT22(key=key, temperature=None, humidity=None, dewpoint=None, error=error)
            else:
                db.write_DHT22(key=key, temperature=20+i+offset, humidity=50+i+offset, dewpoint=10+i+offset, error=error)
        if 0 == i % 3:
            print(int(time.time()), end=": ")
            if error:
                db.write_RD200(radon=200+i, error=error)
            else:
                db.write_RD200(radon=200+i, error=error)

        print(int(time.time()), end=": ")
        db.write_ventilation({
            "radon_request": toggle,
            "humidity_request": toggle,
            "dewpoint_granted": toggle,
            "internal_temp_granted": toggle,
            "external_temp_granted": toggle,
        })

        print(int(time.time()), end=": ")
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
    command = f"influx delete --bucket taupunkt_bucket --start {start} --stop {stop} --org taupunkt_org --token {token}".split()
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.stdout:
        print(result.stdout.decode(sys.stdout.encoding))
    if result.stderr:
        print(result.stderr.decode(sys.stderr.encoding))


def write_points():
    points = []
    failed = []
    with open(POINTS_FILE, 'r') as f:
        data = f.read().split('\n')
        for line in data:
            if line.strip():
                points.append(line.strip())
    db = Database()
    for point in points:
        if not db.write_point(point):
            failed.append(points)
    if failed:
        print("ERROR: These could not be written")
        for point in failed:
            f.write("{}\n".format(point))


def main():
    import argparse
    parser = argparse.ArgumentParser(description="InfluxDB Test")
    parser.add_argument('--create-test-data', action='store_true', help="Creates test data. Caution, do not execute when your system is in real use!")
    parser.add_argument('--delete-test-data', action='store_true', help="Delete test data. Caution, do not execute when your system is in real use!")
    parser.add_argument('--write-points', action='store_true', help="points that could not be written at startup are writen with ths command.")
    args = parser.parse_args()
    if (args.create_test_data == False) and (args.delete_test_data == False) and (args.write_points == False):
        parser.print_help()
    if args.create_test_data:
        create_test_data()
    if args.delete_test_data:
        delete_test_data()
    if args.write_points:
        write_points()

if __name__ == '__main__':
    main()
