import prometheus_client
from prometheus_client import Gauge, start_http_server, Counter
import pycurl
import time
import threading
from io import BytesIO

if __name__ == "__main__":
    start_http_server(":9900")