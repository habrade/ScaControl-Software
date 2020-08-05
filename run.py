#!/usr/bin/env python

######################################################################
import time

import coloredlogs
import logging
from lib.freq_ctr_device import FreqCtr
from lib.global_device import GlobalDevice
from lib.ipbus_link import IPbusLink
from lib.sca_device import ScaDevice

######################################################################

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
coloredlogs.install(level='DEBUG')
coloredlogs.install(level='DEBUG', logger=log)

__author__ = "Sheng Dong"
__email__ = "s.dong@mails.ccnu.edu.cn"

if __name__ == '__main__':
    hw = IPbusLink().get_hw()
    global_dev = GlobalDevice(hw)
    sca_dev = ScaDevice(hw)
    freq_ctr_dev = FreqCtr(hw)

    ## Soft reset
    # global_dev.set_nuke()
    global_dev.set_soft_rst()


	## Set SCA clocks
    Fout_ref = 6.2
    Fout_dff = 10.5
    Precision = 0.1  ## Unit: Hundred percent

    chn = 0
    sca_dev.set_frq(chn, Fout_ref, Precision)
    time.sleep(1)
    freq_ref = freq_ctr_dev.get_chn_freq(chn)
    log.info("Tested Ref Clock frequency is : {}".format(freq_ref))

    time.sleep(5)

    chn = 1
    sca_dev.set_frq(chn, Fout_dff, Precision)
    time.sleep(1)
    freq_dff = freq_ctr_dev.get_chn_freq(chn)
    log.info("Tested Dff Clock frequency is : {}".format(freq_dff))

    ## Set Sca IO
    sca_dev.set_bit0(True)
    sca_dev.set_bit1(True)
    sca_dev.start(True)
    sca_dev.dff_enable(True)
    sca_dev.trigger(True)
    time.sleep(0.001)
    sca_dev.trigger(False)
