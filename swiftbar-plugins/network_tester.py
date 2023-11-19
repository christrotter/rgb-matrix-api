"""
    This will check the following:
    - local to gateway
    - local to first hop
    - local to google DNS

    These metrics are captured:
    - latency
    - timeouts/failures

    It's presented this way:
    - an indicator bar, red/yellow/green
    - which is split in thirds...

    To actuate it we'll use swiftbar cuz hammers.
    or maybe not.  docker container that runs on startup?...

    It will need great error handling on the network timeout front.
"""
from tcp_latency import measure_latency

#measure_latency(host='google.com')
#measure_latency(host='52.26.14.11', port=80, runs=10, timeout=2.5)
