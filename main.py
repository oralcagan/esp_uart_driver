
from EspAtDriver import ESPDriver
import time

esp = ESPDriver(0,115200)
esp.set_multi(1)
esp.open_server(8080)
print("here")
time.sleep(5)
esp.tcp_write(0,b"hello")
print(bytes(esp.nw_msgs[0]).decode("UTF-8"))