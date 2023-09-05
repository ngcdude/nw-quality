import argparse
import subprocess
import time
import numpy as np
import os
import urllib.request
import json
import signal
import datetime
import sys
from multiprocessing import Process

data_file = '.ping_data.txt'  # Hidden data file
pid_file = '.ping_monitor.pid'  # PID file
host = 'www.google.com'

### HELPER FUNCTIONS
def ping(host):
    try:
        output = subprocess.check_output(["ping", "-c", "1", host], stderr=subprocess.STDOUT, text=True)
        success = True
    except subprocess.CalledProcessError as e:
        output = e.output
        success = False
    return success, output

def get_isp():
    try:
        with urllib.request.urlopen('http://ipinfo.io/json') as response:
            data = json.load(response)
        return data.get('org', 'Unknown ISP')
    except Exception as e:
        return 'Failed to fetch ISP information'


def check_pid_running(pid):
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True

def collect_data():
    while True:
        success, output = ping(host)
        if success:
            try:
                latency = float(output.split('time=')[1].split()[0])
            except (IndexError, ValueError):
                latency = 0  # Record missing ping responses as 0
        else:
            latency = 0

        with open(data_file, 'a') as f:
            f.write(f'{time.time()} {latency}\n')

        time.sleep(5)  # Adjust the frequency as needed

### DATA CYCLE
def start_data_collection():
    if os.path.exists(pid_file):
        print("Data collection process is already running")
        sys.exit(1)

    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))

    if os.path.exists(data_file):
        print(f"Continue data collection process into (existing) {data_file}")
    else:
        print(f"Create data file: {data_file}")
        # Write the ISP name at the beginning of the data file
        isp_name = get_isp()
        with open(data_file, 'w') as f:
            f.write(f"# ISP: {isp_name}\n")
            print(f"ISP name: {isp_name}\n")

    collect_data() # Start daat collection initializing
    print("Data collection process started")

def stop_data_collection():
    if os.path.exists(pid_file):
        with open(pid_file, 'r') as f:
            pid = int(f.read())
            if check_pid_running(pid):
                os.kill(pid, signal.SIGTERM)
                print("Data collection process stopped.")
            else:
                print("Data collection process is not running.")
        os.remove(pid_file)
    else:
        print("Data collection process is not running.")


#### PROCESS DATA COLLECTED
def load_data():
    data = []
    # Exit if there is a data file to parse
    if not os.path.exists(data_file):
        print("Missing data file, please start the data collection first")
        sys.exit(1)

    with open(data_file, 'r') as f:
        lines = f.readlines()
        for line in lines[1:]:  # Skip the first line (ISP name)
            timestamp, latency = line.strip().split()
            data.append((float(timestamp), float(latency)))
    return data

def format_timestamp(timestamp):
    return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def analyze_latency_patterns(data):
    # Bin data into hourly intervals
    bins = {}
    for timestamp, latency in data:
        dt = datetime.datetime.fromtimestamp(timestamp)
        hour = dt.hour
        if hour not in bins:
            bins[hour] = {'latencies': [], 'lost_pings': 0}
        bins[hour]['latencies'].append(latency)
        if latency == 0:
            bins[hour]['lost_pings'] += 1

    # Analyze and print patterns
    print("Latency Patterns by Hour:")
    print("==========================")
    for hour, values in sorted(bins.items()):
        avg_latency = np.mean(values['latencies'])
        lost_pings = values['lost_pings']
        print(f"Hour: {hour:02}:00 - {hour:02}:59")
        print(f"Average Latency: {avg_latency:.2f} ms")
        print(f"Lost Pings: {lost_pings}")
        print("==========================")


def main():
    parser = argparse.ArgumentParser(description="Monitor internet connectivity and record latency.")
    parser.add_argument("--start", action="store_true", help="Start data collection")
    parser.add_argument("--stop", action="store_true", help="Stop data collection")
    parser.add_argument("--status", action="store_true", help="Query monitoring status")
    parser.add_argument("--reset", action="store_true", help="Reset stored data")
    args = parser.parse_args()

    if args.start:
       # Start data collection 
        start_data_collection()
    elif args.stop:
        stop_data_collection()
    elif args.status:
        data = load_data()
        with open(data_file, 'r') as f:
            isp_name = f.readline().strip().split(': ')[1]  # Extract ISP name from the first line

        if data:
            avg_latency = np.mean([latency for _, latency in data])
            min_latency = np.min([latency for _, latency in data])
            max_latency = np.max([latency for _, latency in data])
            std_dev = np.std([latency for _, latency in data])

            lost_pings = sum(1 for _, latency in data if latency == 0)

            first_timestamp = data[0][0]
            last_timestamp = data[-1][0]

            print("ISP:", isp_name)  # Print ISP name
            print("Statistics:")
            print("=============================================")
            print(f"{'Average Latency:':<20} {avg_latency:.2f} ms")
            print(f"{'Min Latency:':<20} {min_latency:.2f} ms")
            print(f"{'Max Latency:':<20} {max_latency:.2f} ms")
            print(f"{'Standard Deviation:':<20} {std_dev:.2f}")
            print(f"{'Total Pings:':<20} {len(data)}")
            print(f"{'Lost Pings:':<20} {lost_pings}")
          
            print()
            print("Time Range:")
            print("=============================================")
            print(f"{'Start Time:':<20} {format_timestamp(first_timestamp)}")
            print(f"{'End Time:':<20} {format_timestamp(last_timestamp)}")
        else:
            print("No data available.")
    elif args.reset:
        if os.path.exists(data_file):
            os.remove(data_file)
            print(f"Deleted {data_file}")
        else:
            print(f"No {data_file} found to delete")
    else:
        collect_data()  # Run data collection in the background

if __name__ == "__main__":
    main()
