#!/usr/bin/env python3

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
log.setLevel(logging.INFO)
coloredlogs.install(level='INFO', logger=log)

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
    Fout_ref = 1000 / 180  ## Unit: MHz
    Fout_dff = 1000 / 120  ## Unit: MHz
    Precision = 0.1  ## Unit: Hundred percent, %

    log.debug("MMCM initial Status:")
    for chn in [0, 1]:
        log.debug("clock {:} is locked: {:}!".format(chn, sca_dev.is_locked(chn)))

    for chn in [0, 1]:
        if chn == 0:
            clock_name = "Ref"
            sca_dev.set_frq(chn, Fout_ref, Precision)
        else:
            clock_name = "Dff"
            sca_dev.set_frq(chn, Fout_dff, Precision)
        time.sleep(1)
        freq_ref = freq_ctr_dev.get_chn_freq(chn)
        log.info("Tested {:s} Clock frequency is : {}".format(clock_name, freq_ref))

    # Set Sca IO
    sca_dev.set_bit0(True)
    sca_dev.set_bit1(True)
    sca_dev.start(True)

    sca_dev.dff_enable(True)

    sca_dev.set_din(True, False)
    sca_dev.set_din(True, False)
    sca_dev.trigger(True, False)
    sca_dev.trigger(False, True)
