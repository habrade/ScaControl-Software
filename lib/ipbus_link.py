import coloredlogs
import logging
import uhal

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
coloredlogs.install(level='DEBUG', logger=log)

__author__ = "Sheng Dong"
__email__ = "s.dong@mails.ccnu.edu.cn"


class IPbusLink:
    def __init__(self):
        self.device_ip = "192.168.3.17"
        self.device_uri = "chtcp-2.0://localhost:10203?target=" + self.device_ip + ":50001"
        self.address_table_name = "../etc/address.xml"
        self.address_table_uri = "file://" + self.address_table_name
        self.hw = None

    def get_hw(self):
        uhal.setLogLevelTo(uhal.LogLevel.INFO)
        self.hw = uhal.getDevice("HappyDaq.udp.0", self.device_uri, self.address_table_uri)
        return self.hw
