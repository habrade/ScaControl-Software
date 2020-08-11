#!/usr/bin/env python3

import time
import coloredlogs
import logging
from lib.freq_ctr_device import FreqCtr
from lib.global_device import GlobalDevice
from lib.ipbus_link import IPbusLink
from lib.sca_device import ScaDevice
from lib.sca_defines import Delay_Conters

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
coloredlogs.install(level='INFO', logger=log)

__author__ = "Sheng Dong"
__email__ = "s.dong@mails.ccnu.edu.cn"


def set_sca(sca_dev, Fout_ref, Fout_dff, Precision):
    log.debug("MMCM initial Status:")
    for chn in [0, 1]:
        log.debug("clock {:} is locked: {:}!".format(chn, sca_dev.is_locked(chn)))

    for chn in [0, 1]:
        if chn == 0:
            sca_dev.set_frq(chn, Fout_ref, Precision)
        else:
            sca_dev.set_frq(chn, Fout_dff, Precision)
        time.sleep(1)

    # Set Sca IO
    sca_dev.set_bit0(True)
    sca_dev.set_bit1(True)
    sca_dev.start(True)

    sca_dev.dff_enable(True)

    sca_dev.set_din(True, False)
    sca_dev.set_din(True, False)
    sca_dev.trigger(True, False)
    sca_dev.trigger(False, True)


def fre_counter(freq_ctr_dev):
    for chn in [0, 1]:
        if chn == 0:
            clock_name = "Ref"
        else:
            clock_name = "Dff"
    freq_ref = freq_ctr_dev.get_chn_freq(chn)
    log.info("Tested {:s} Clock frequency is : {}".format(clock_name, freq_ref))


def main(Fout_ref, Fout_dff, Precision):
    ## Get ipbus connection
    hw = IPbusLink().get_hw()
    global_dev = GlobalDevice(hw)
    sca_dev = ScaDevice(hw)
    freq_ctr_dev = FreqCtr(hw)
    ## Soft reset
    # global_dev.set_nuke()
    global_dev.set_soft_rst()
    ## Set SCA
    set_sca(sca_dev, Fout_ref, Fout_dff, Precision)
    ## Test clock frq
    fre_counter(freq_ctr_dev)


if __name__ == '__main__':
    ## Set SCA sampling frequnce
    Sample_Frq = 2000  ## Unit: MHz
    ## Set SCA clocks
    Fout_ref = Sample_Frq / Delay_Conters  ## Unit: MHz
    Fout_dff = 1000 / 120  ## Unit: MHz
    Precision = 0.1  ## Unit: Hundred percent, %
    main(Fout_ref, Fout_dff, Precision)
