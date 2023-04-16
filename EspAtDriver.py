from machine import UART
import time

line_end = "\r\n"

max_buf_size: int = 64
link_n = 5

def sleep_ms(ms: int):
    time.sleep_ms(ms)


def _read_until_n(c):
    if c == b"\n":
        return True
    return False


class ESPDriver:
    nw_msgs = [[] * link_n]
    ports_open = [False] * link_n
    def __init__(self, id: int, baud: int):
        self.uart = UART(id, baud)
        sleep_ms(1000)
        if not self.test():
            raise Exception("'AT' command not OK")

    def _handle_nw_cmd(self, buf: bytes):
        if len(buf) == 9 and buf.endswith(b"CONNECT"):
            id = int(buf[0:1].decode("UTF-8"))
            self.ports_open[id] = True
            return (True,bytes())
        if (len(buf) == 8 and buf.endswith(b"CLOSED")) or (len(buf) == 14 and buf.endswith(b"CONNECT FAIL")):
            id = int(buf[0:1].decode("UTF-8"))
            self.ports_open[id] = False
            self.nw_msgs[id] = []
        if buf.startswith(b"+IPD"):
            id = int(buf[5:6].decode("UTF-8"))
            self.ports_open[id] = True
            end_i = buf.find(b":")
            data_len = int(buf[7:end_i].decode("UTF-8"))
            data = buf[end_i+1:end_i+1+data_len]
            self.nw_msgs[id].extend(data)
            extra = buf[end_i+1+data_len:]
            (is_nw,_) = self._handle_nw_cmd(extra)
            if not is_nw:
                return (True,extra)
            return (True,bytes())
        return (False,bytes())

    def _read_char(self):
        while True:
            if self.uart.any() > 0:
                return self.uart.read(1)

    def _read_until(self, verify):
        while True:
            c = self._read_char()
            if verify(c):
                return

    def _readline(self):
        buf = bytearray()
        while True:
            c = self._read_char()
            if c == b"\r":
                self._read_until(_read_until_n)
                res = bytes(buf)
                (is_nw,data) = self._handle_nw_cmd(res)
                if is_nw:
                    (is_nw,_) = self._handle_nw_cmd(data)
                    if not is_nw:
                        return data
                    buf = bytes()
                    continue
                return res
            buf += c

    def _read_n_lines(self, n: int):
        l = []
        while n > 0:
            line = self._readline()
            if line is None:
                n += 1
            else:
                l.append(line.decode("UTF-8","replace"))
            n -= 1
        return l

    def _read_until_line(self, msg: str):
        while True:
            line = self._readline()
            if line is not None:
                line = line.decode("UTF-8","replace")
                if line == msg:
                    return

    def test(self) -> bool:
        msg = "AT"
        msg_buf = msg + line_end
        msg_buf = msg_buf.encode()
        self.uart.write(msg_buf)
        self._read_until_line(msg)
        if self._read_n_lines(2)[1] == "OK":
            return True
        return False

    def set_ap_mode(self, mode: int) -> bool:
        msg = "AT+CWMODE_CUR=" + str(mode)
        msg_buf = msg + line_end
        msg_buf = msg_buf.encode()
        self.uart.write(msg_buf)
        self._read_until_line(msg)
        if self._read_n_lines(2)[1] == "OK":
            return True
        return False

    def set_ap_config(self, ssid: str, pw: str, chl: int, enc: int) -> bool:
        msg = "AT+CWSAP_CUR=\"" + ssid + "\",\"" + \
            pw + "\"," + str(chl) + "," + str(enc)
        msg_buf = msg + line_end
        msg_buf = msg_buf.encode()
        self.uart.write(msg_buf)
        self._read_until_line(msg)
        if self._read_n_lines(2)[1] == "OK":
            return True
        return False

    def conn_stat(self) -> int:
        # STATUS:<stat>
        msg = "AT+CIPSTATUS"
        msg_buf = msg + line_end
        msg_buf = msg_buf.encode()
        self.uart.write(msg_buf)
        self._read_until_line(msg)
        return int(self._read_n_lines(1)[0][7])

    def open_server(self, port: int) -> bool:
        msg = "AT+CIPSERVER=1," + str(port)
        msg_buf = msg + line_end
        msg_buf = msg_buf.encode()
        self.uart.write(msg_buf)
        self._read_until_line(msg)
        res = self._read_n_lines(2)
        if res[0] == "no change":
            self._read_n_lines(1)
            return True
        if res[1] == "OK":
            return True
        return False

    def tcp_write(self, id: int, data: bytes):
        msg = "AT+CIPSEND=" + str(id) + "," + str(len(data))
        msg_buf = msg + line_end
        msg_buf = msg_buf.encode()
        self.uart.write(msg_buf)
        self._read_until_line(msg)
        self.uart.write(data)
        self._read_n_lines(7)

    def set_multi(self, mode: int):
        msg = "AT+CIPMUX=" + str(mode)
        msg_buf = msg + line_end
        msg_buf = msg_buf.encode()
        self.uart.write(msg_buf)
        self._read_until_line(msg)
        if self._read_n_lines(2)[1] == "OK":
            return True
        return False
