# nw-quality
Tool created to monitor latency and packet drops from terminal

## command

Monitor internet connectivity and record latency

```
monitor_service.py [-h] [--start] [--stop] [--status] [--reset]

options:
  -h, --help  show this help message and exit
  --start     Start data collection
  --stop      Stop data collection
  --status    Query monitoring status
  --reset     Reset stored data
```

## example use

```
python3 monitor_service.py --start
[data collection starts through pings]
...
...
python3 monitor_service.py --status 
[provides a summary of the current collection] 
...
...
python3 monitor_service.py --stop 
[stops data collection, perhaps the user disconnect the terminal for other reasons and wants to pause] 
python3 monitor_service.py --start 
[continues data collection] 
...
python3 monitor_service.py --stop 
[user stops data collection because wants to use another method: wifi vs. ethernet]
python3 monitor_service.py --status 
[outputs summary of data collected]

python3 monitor_service.py --reset
[user wants a new data set, the old one is deleted]
python3 monitor_service.py --start
[user starts the new data collection]

