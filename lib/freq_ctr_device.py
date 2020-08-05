import coloredlogs
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
coloredlogs.install(level='DEBUG', logger=log)

__author__ = "Sheng Dong"
__email__ = "s.dong@mails.ccnu.edu.cn"


class FreqCtr:
    def __init__(self, hw):
        self.hw = hw
        self.reg_name_base = "freq_ctr_dev."
        log.debug("Frequency Counter Device")

    def enable_crap_mode(self, enable=False):
        reg_name = self.reg_name_base + "en_crap_mode"
        node = self.hw.getNode(reg_name)
        if enable:
            node.write(1)
        else:
            node.write(0)
        self.hw.dispatch()

    def sel_chn(self, chn):
        chn &= 0xf
        reg_name = self.reg_name_base + "chan_sel"
        node = self.hw.getNode(reg_name)
        node.write(chn)
        self.hw.dispatch()

    def get_sel_chn(self):
        reg_name = self.reg_name_base + "chan_sel"
        node = self.hw.getNode(reg_name)
        chn = node.read()
        self.hw.dispatch()
        return chn.value()

    def is_valid(self):
        reg_name = self.reg_name_base + "valid"
        node = self.hw.getNode(reg_name)
        valid_raw = node.read()
        self.hw.dispatch()
        valid = (valid_raw.value() == 1)
        return valid

    def get_freq(self):
        reg_name = self.reg_name_base + "count"
        node = self.hw.getNode(reg_name)
        freq_raw = node.read()
        reg_name = self.reg_name_base + "valid"
        node = self.hw.getNode(reg_name)
        valid_raw = node.read()
        self.hw.dispatch()
        if valid_raw.value() != 1:
            print("valid: {}".format(valid_raw.value()))
            return 0
        else:
            return freq_raw.value()

    def get_chn_freq(self, chn):
        self.sel_chn(chn)
        freq_counter = 0
        if self.is_valid():
            freq_counter = self.get_freq()
            log.debug("Frequency counter: {:d}".format(freq_counter))
        freq = 31.25E6 * freq_counter / (2**18 * 1E6)
        return freq
