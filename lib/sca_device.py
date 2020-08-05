import math
import sys 

import coloredlogs
import logging
from lib.mmcm import Mmcm

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
coloredlogs.install(level='INFO', logger=log)

__author__ = "Sheng Dong"
__email__ = "s.dong@mails.ccnu.edu.cn"


class ScaDevice:
    def __init__(self, hw):
        self.hw = hw
        self.sca_base = "sca_dev."
        self.refclk_base = self.sca_base + "ref_clk_drp."
        self.dffclk_base = self.sca_base + "dff_clk_drp."
        self.clkout0_shared_reg = 0x0000
        self.clkout0_reg1 = 0x0000
        self.clkout0_reg2 = 0x0000
        self.clkfbout_shared_reg = 0x0000
        self.clkfbout_reg1 = 0x0000
        self.clkfbout_reg2 = 0x0000
        self.div_reg = 0x0000
        self.lock_reg1 = 0x0000
        self.lock_reg2 = 0x0000
        self.lock_reg3 = 0x0000
        self.power_reg = 0xFFFF
        self.filter_reg1 = 0x0000
        self.filter_reg2 = 0x0000

        log.debug("SCA Device")


    def start(self, enable):
        reg_name = self.io_reg_base + "start_pad"
        node = self.hw.getNode(reg_name)
        if enable:
            node.write(1)
        else:
            node.write(0)
        self.hw.dispatch()

    def trigger(self, enable):
        reg_name = self.io_reg_base + "trigger_pad"
        node = self.hw.getNode(reg_name)
        if enable:
            node.write(1)
        else:
            node.write(0)
        self.hw.dispatch()

    def dff_enable(self, enable):
        reg_name = self.io_reg_base + "enable_r_dff"
        node = self.hw.getNode(reg_name)
        if enable:
            node.write(1)
        else:
            node.write(0)
        self.hw.dispatch()

    def set_bit0(self, enable):
        reg_name = self.io_reg_base + "bit_0_cp"
        node = self.hw.getNode(reg_name)
        if enable:
            node.write(1)
        else:
            node.write(0)
        self.hw.dispatch()

    def set_bit1(self, enable):
        reg_name = self.io_reg_base + "bit_1_cp"
        node = self.hw.getNode(reg_name)
        if enable:
            node.write(1)
        else:
            node.write(0)
        self.hw.dispatch()

	 def drp_clkout_frac(self, divide, phase):
			log.debug("Calculate clkout frac, divide: {:} phase: {:}".format(divide, phase))
			divide_frac = math.fmod(divide, 1)
			divide_frac_8ths = int(divide_frac * 8)
			divide_int = int(math.floor(divide))

			even_part_high = int(math.floor(divide_int / 2))
			even_part_low = even_part_high

			odd = divide_int - even_part_high - even_part_low
			odd_and_frac = int(8 * odd + divide_frac_8ths)

			if odd_and_frac <= 9:
				lt_frac = even_part_high - 1
			else:
				lt_frac = even_part_high
			if odd_and_frac <= 8:
				ht_frac = even_part_low - 1
			else:
				ht_frac = even_part_low

			pmfall = int(odd * 4 + math.floor(divide_frac_8ths / 2))
			pmrise = 0
			dt = int(math.floor(phase * divide / 360.0))
			pmrise = int(math.floor(8 * ((phase * divide / 360.0) - dt) + 0.5))
			pmfall = int(pmfall + pmrise)

			if (odd_and_frac <= 9) and (odd_and_frac >= 2) or (divide == 2.125):
				wf_fall = 1
			else:
				wf_fall = 0
			if (odd_and_frac <= 8) and (odd_and_frac >= 1):
				wf_rise = 1
			else:
				wf_rise = 0

			dt = int(dt + math.floor(pmrise / 8))  # delay time
			pmrise = int(math.fmod(pmrise, 8))
			pmfall = int(math.fmod(pmfall, 8))

			reg1 = ((pmrise & 0x7) << 13) + (1 << 12) + ((ht_frac & 0x3f) << 6) + (lt_frac & 0x3f)
			reg2 = ((divide_frac_8ths & 0x7) << 12) + (1 << 11) + ((wf_rise & 0b1) << 10) + (dt & 0x3f)
			regshared = ((pmfall & 0x7) << 1) + (wf_fall & 0b1)
			return reg1, reg2, regshared

		def drp_calc_m(self, divide, phase):
			log.debug("Calculate Multi Regs (clkfbout)")
			phasecycles = int((divide * phase) / 360.0)
			pmphase = phase - (phasecycles * 360.0) / divide
			## TODO: should check here
			pmphasecycles = int((pmphase * divide) / 45)

			ht = int(divide / 2)
			lt = int(divide - ht)
			odd = lt - ht
			daddr_reg1 = 0x14
			daddr_reg2 = 0x15
			daddr_regshared = 0x13
			if divide >= 64:
				log.error("daddr_14: error: m must be 2 to 64\t-clkfbout register 2-")
				log.error(
					"daddr_15: error: m must be 2 to 64\t-clkfbout register 2-\tnote: the calculations are only for the non-fractional settings. CLKFBOUT must use an integer divide value for these DRP settings to work")
				sys.exit(-1)
			elif divide == 1:
				drp_reg1 = (pmphasecycles & 0x8) << 14 + 0b1000001000001
				drp_reg2 = ((odd & 0b1) << 7) + (1 << 6) + (phasecycles & 0x3f)
				log.debug("daddr_{:#2x}: {:#4x}\t-clkfbout register 1- ".format(daddr_reg1, drp_reg1))
				log.debug("daddr_{:#2x}: {:#4x}\t-clkfbout register 2- ".format(daddr_reg2, drp_reg2))
				return drp_reg1, drp_reg2
			elif math.fmod(divide, 1) > 0:
				drp_frac_registers = self.drp_clkout_frac(divide, phase)
				drp_reg1 = drp_frac_registers[0]
				drp_reg2 = drp_frac_registers[1]
				drp_regshared = drp_frac_registers[2] << 10

				log.debug("DADDR_{:#2x}: {:#4x}\t-CLKFBOUT Register 1- ".format(daddr_reg1, drp_reg1))
				log.debug("DADDR_{:#2x}: {:#4x}\t-CLKFBOUT Register 2- ".format(daddr_reg2, drp_reg2))
				log.debug(
					"DADDR_{:#2x}: {:#4x}\t-CLKFBOUT Register Shared with CLKOUT6- ".format(daddr_regshared, drp_regshared))
				return drp_reg1, drp_reg2, drp_regshared
			else:
				drp_reg1 = ((pmphasecycles & 0x7) << 13) + (1 << 12) + ((ht & 0x3f) << 6) + (lt & 0x3f)
				drp_reg2 = ((odd & 0b1) << 7) + (phasecycles & 0x3f)
				log.debug("DADDR_{:#2x}: {:#4x}\t-CLKFBOUT Register 1- ".format(daddr_reg1, drp_reg1))
				log.debug("DADDR_{:#2x}: {:#4x}\t-CLKFBOUT Register 2- ".format(daddr_reg2, drp_reg2))
				return drp_reg1, drp_reg2

		def drp_calc_d(self, divide):
			log.debug("Calculate divide reg")
			ht = int(divide / 2)
			lt = int(divide - ht)
			if divide > 128:
				log.error("ERROR: DADDR_16: ERROR D must be 1 to 128")
				log.error("ERROR: 16 ERROR")
				sys.exit(-1)
			elif divide == 1:
				div_reg = int("0b0001000001000001", base=2)
				log.debug("DADDR_0x16: {:#4x}\t-DIVCLK Register $divide-".format(div_reg))
				return div_reg
			else:
				div_reg = ((ht & 0x3f) << 6) + (lt & 0x3f)
				log.debug("DADDR_16: {:#04x}\t-DIVCLK Register {}-".format(div_reg, divide))
				return div_reg

		def drp_cpres(self, div, bw):
			log.debug("Calculate filter regs")
			div = int(div)
			bw_lower = bw.lower()
			dict_low = {
				#  CP, RES, LFHF
				1: ("0010", "1111", "00"), 2: ("0010", "1111", "00"), 3: ("0010", "1111", "00"), 4: ("0010", "1111", "00"),
				5: ("0010", "0111", "00"), 6: ("0010", "1011", "00"), 7: ("0010", "1101", "00"), 8: ("0010", "0011", "00"),
				9: ("0010", "0101", "00"), 10: ("0010", "0101", "00"), 11: ("0010", "1001", "00"),
				12: ("0010", "1110", "00"),
				13: ("0010", "1110", "00"), 14: ("0010", "1110", "00"), 15: ("0010", "1110", "00"),
				16: ("0010", "0001", "00"),
				17: ("0010", "0001", "00"), 18: ("0010", "0001", "00"), 19: ("0010", "0110", "00"),
				20: ("0010", "0110", "00"),
				21: ("0010", "0110", "00"), 22: ("0010", "0110", "00"), 23: ("0010", "0110", "00"),
				24: ("0010", "0110", "00"),
				25: ("0010", "0110", "00"), 26: ("0010", "1010", "00"), 27: ("0010", "1010", "00"),
				28: ("0010", "1010", "00"),
				29: ("0010", "1010", "00"), 30: ("0010", "1010", "00"), 31: ("0010", "1100", "00"),
				32: ("0010", "1100", "00"),
				33: ("0010", "1100", "00"), 34: ("0010", "1100", "00"), 35: ("0010", "1100", "00"),
				36: ("0010", "1100", "00"),
				37: ("0010", "1100", "00"), 38: ("0010", "1100", "00"), 39: ("0010", "1100", "00"),
				40: ("0010", "1100", "00"),
				41: ("0010", "1100", "00"), 42: ("0010", "1100", "00"), 43: ("0010", "1100", "00"),
				44: ("0010", "1100", "00"),
				45: ("0010", "1100", "00"), 46: ("0010", "1100", "00"), 47: ("0010", "1100", "00"),
				48: ("0010", "0010", "00"),
				49: ("0010", "0010", "00"), 50: ("0010", "0010", "00"), 51: ("0010", "0010", "00"),
				52: ("0010", "0010", "00"),
				53: ("0010", "0010", "00"), 54: ("0010", "0010", "00"), 55: ("0010", "0010", "00"),
				56: ("0010", "0010", "00"),
				57: ("0010", "0010", "00"), 58: ("0010", "0010", "00"), 59: ("0010", "0010", "00"),
				60: ("0010", "0010", "00"),
				61: ("0010", "0010", "00"), 62: ("0010", "0010", "00"), 63: ("0010", "0010", "00"),
				64: ("0010", "0010", "00")
			}
			dict_low_ss = {
				1: ("0010", "1111", "11"), 2: ("0010", "1111", "11"), 3: ("0010", "1111", "11"), 4: ("0010", "1111", "11"),
				5: ("0010", "0111", "11"), 6: ("0010", "1011", "11"), 7: ("0010", "1101", "11"), 8: ("0010", "0011", "11"),
				9: ("0010", "0101", "11"), 10: ("0010", "0101", "11"), 11: ("0010", "1001", "11"),
				12: ("0010", "1110", "11"),
				13: ("0010", "1110", "11"), 14: ("0010", "1110", "11"), 15: ("0010", "1110", "11"),
				16: ("0010", "0001", "11"),
				17: ("0010", "0001", "11"), 18: ("0010", "0001", "11"), 19: ("0010", "0110", "11"),
				20: ("0010", "0110", "11"),
				21: ("0010", "0110", "11"), 22: ("0010", "0110", "11"), 23: ("0010", "0110", "11"),
				24: ("0010", "0110", "11"),
				25: ("0010", "0110", "11"), 26: ("0010", "1010", "11"), 27: ("0010", "1010", "11"),
				28: ("0010", "1010", "11"),
				29: ("0010", "1010", "11"), 30: ("0010", "1010", "11"), 31: ("0010", "1100", "11"),
				32: ("0010", "1100", "11"),
				33: ("0010", "1100", "11"), 34: ("0010", "1100", "11"), 35: ("0010", "1100", "11"),
				36: ("0010", "1100", "11"),
				37: ("0010", "1100", "11"), 38: ("0010", "1100", "11"), 39: ("0010", "1100", "11"),
				40: ("0010", "1100", "11"),
				41: ("0010", "1100", "11"), 42: ("0010", "1100", "11"), 43: ("0010", "1100", "11"),
				44: ("0010", "1100", "11"),
				45: ("0010", "1100", "11"), 46: ("0010", "1100", "11"), 47: ("0010", "1100", "11"),
				48: ("0010", "0010", "11"),
				49: ("0010", "0010", "11"), 50: ("0010", "0010", "11"), 51: ("0010", "0010", "11"),
				52: ("0010", "0010", "11"),
				53: ("0010", "0010", "11"), 54: ("0010", "0010", "11"), 55: ("0010", "0010", "11"),
				56: ("0010", "0010", "11"),
				57: ("0010", "0010", "11"), 58: ("0010", "0010", "11"), 59: ("0010", "0010", "11"),
				60: ("0010", "0010", "11"),
				61: ("0010", "0010", "11"), 62: ("0010", "0010", "11"), 63: ("0010", "0010", "11"),
				64: ("0010", "0010", "11")
			}
			dict_high = {
				1: ("0010", "1111", "00"), 2: ("0100", "1111", "00"), 3: ("0101", "1011", "00"), 4: ("0111", "0111", "00"),
				5: ("1101", "0111", "00"), 6: ("1110", "1011", "00"), 7: ("1110", "1101", "00"), 8: ("1111", "0011", "00"),
				9: ("1110", "0101", "00"), 10: ("1111", "0101", "00"), 11: ("1111", "1001", "00"),
				12: ("1101", "0001", "00"),
				13: ("1111", "1001", "00"), 14: ("1111", "1001", "00"), 15: ("1111", "1001", "00"),
				16: ("1111", "1001", "00"),
				17: ("1111", "0101", "00"), 18: ("1111", "0101", "00"), 19: ("1100", "0001", "00"),
				20: ("1100", "0001", "00"),
				21: ("1100", "0001", "00"), 22: ("0101", "1100", "00"), 23: ("0101", "1100", "00"),
				24: ("0101", "1100", "00"),
				25: ("0101", "1100", "00"), 26: ("0011", "0100", "00"), 27: ("0011", "0100", "00"),
				28: ("0011", "0100", "00"),
				29: ("0011", "0100", "00"), 30: ("0011", "0100", "00"), 31: ("0011", "0100", "00"),
				32: ("0011", "0100", "00"),
				33: ("0011", "0100", "00"), 34: ("0011", "0100", "00"), 35: ("0011", "0100", "00"),
				36: ("0011", "0100", "00"),
				37: ("0011", "0100", "00"), 38: ("0011", "0100", "00"), 39: ("0011", "0100", "00"),
				40: ("0011", "0100", "00"),
				41: ("0011", "0100", "00"), 42: ("0010", "1000", "00"), 43: ("0010", "1000", "00"),
				44: ("0010", "1000", "00"),
				45: ("0010", "1000", "00"), 46: ("0010", "1000", "00"), 47: ("0111", "0001", "00"),
				48: ("0111", "0001", "00"),
				49: ("0100", "1100", "00"), 50: ("0100", "1100", "00"), 51: ("0100", "1100", "00"),
				52: ("0100", "1100", "00"),
				53: ("0110", "0001", "00"), 54: ("0110", "0001", "00"), 55: ("0101", "0110", "00"),
				56: ("0101", "0110", "00"),
				57: ("0101", "0110", "00"), 58: ("0010", "0100", "00"), 59: ("0010", "0100", "00"),
				60: ("0010", "0100", "00"),
				61: ("0010", "0100", "00"), 62: ("0100", "1010", "00"), 63: ("0011", "1100", "00"),
				64: ("0011", "1100", "00")
			}
			dict_opt = {
				1: ("0010", "1111", "00"), 2: ("0100", "1111", "00"), 3: ("0101", "1011", "00"), 4: ("0111", "0111", "00"),
				5: ("1101", "0111", "00"), 6: ("1110", "1011", "00"), 7: ("1110", "1101", "00"), 8: ("1111", "0011", "00"),
				9: ("1110", "0101", "00"), 10: ("1111", "0101", "00"), 11: ("1111", "1001", "00"),
				12: ("1101", "0001", "00"),
				13: ("1111", "1001", "00"), 14: ("1111", "1001", "00"), 15: ("1111", "1001", "00"),
				16: ("1111", "1001", "00"),
				17: ("1111", "0101", "00"), 18: ("1111", "0101", "00"), 19: ("1100", "0001", "00"),
				20: ("1100", "0001", "00"),
				21: ("1100", "0001", "00"), 22: ("0101", "1100", "00"), 23: ("0101", "1100", "00"),
				24: ("0101", "1100", "00"),
				25: ("0101", "1100", "00"), 26: ("0011", "0100", "00"), 27: ("0011", "0100", "00"),
				28: ("0011", "0100", "00"),
				29: ("0011", "0100", "00"), 30: ("0011", "0100", "00"), 31: ("0011", "0100", "00"),
				32: ("0011", "0100", "00"),
				33: ("0011", "0100", "00"), 34: ("0011", "0100", "00"), 35: ("0011", "0100", "00"),
				36: ("0011", "0100", "00"),
				37: ("0011", "0100", "00"), 38: ("0011", "0100", "00"), 39: ("0011", "0100", "00"),
				40: ("0011", "0100", "00"),
				41: ("0011", "0100", "00"), 42: ("0010", "1000", "00"), 43: ("0010", "1000", "00"),
				44: ("0010", "1000", "00"),
				45: ("0010", "1000", "00"), 46: ("0010", "1000", "00"), 47: ("0111", "0001", "00"),
				48: ("0111", "0001", "00"),
				49: ("0100", "1100", "00"), 50: ("0100", "1100", "00"), 51: ("0100", "1100", "00"),
				52: ("0100", "1100", "00"),
				53: ("0110", "0001", "00"), 54: ("0110", "0001", "00"), 55: ("0101", "0110", "00"),
				56: ("0101", "0110", "00"),
				57: ("0101", "0110", "00"), 58: ("0010", "0100", "00"), 59: ("0010", "0100", "00"),
				60: ("0010", "0100", "00"),
				61: ("0010", "0100", "00"), 62: ("0100", "1010", "00"), 63: ("0011", "1100", "00"),
				64: ("0011", "1100", "00")
			}
			if bw_lower == "low":
				CP, RES, LFHF = dict_low[div]
			elif bw_lower == "low_ss":
				CP, RES, LFHF = dict_low_ss[div]
			elif bw_lower == "high":
				CP, RES, LFHF = dict_high[div]
			else:
				CP, RES, LFHF = dict_opt[div]
			filt_reg1 = (int(CP[3], base=2) << 8) + (int(CP[1:3], base=2) << 11) + (int(CP[0], base=2) << 15)
			filt_reg2 = (int(LFHF[1], base=2) << 4) + (int(LFHF[0], base=2) << 7) + (int(RES[3], base=2) << 8) + (
					int(RES[1:3], base=2) << 11) + (int(RES[0], base=2) << 15)
			log.debug(
				"DADDR_4E: {:#04x}\t-Filter Register 1: M set to {} with {} bandwidth-".format(filt_reg1, div, bw))
			log.debug(
				"DADDR_4F: {:#04x}\t-Filter Register 2: M set to {} with {} bandwidth-".format(filt_reg2, div, bw))
			return filt_reg1, filt_reg2

		def drp_locking(self, div):
			log.debug("Calculate locking regs")
			div = int(div)
			lock_dict = {
				#  LockRefDly, LockFBDly, LockCnt, LockSatHigh, UnlockCnt
				1: ("00110", "00110", "0111101000", "0111101001", "0000000001"),
				2: ("00110", "00110", "0111101000", "0111101001", "0000000001"),
				3: ("01000", "01000", "0111101000", "0111101001", "0000000001"),
				4: ("01011", "01011", "0111101000", "0111101001", "0000000001"),
				5: ("01110", "01110", "0111101000", "0111101001", "0000000001"),
				6: ("10001", "10001", "0111101000", "0111101001", "0000000001"),
				7: ("10011", "10011", "0111101000", "0111101001", "0000000001"),
				8: ("10110", "10110", "0111101000", "0111101001", "0000000001"),
				9: ("11001", "11001", "0111101000", "0111101001", "0000000001"),
				10: ("11100", "11100", "0111101000", "0111101001", "0000000001"),
				11: ("11111", "11111", "0110000100", "0111101001", "0000000001"),
				12: ("11111", "11111", "0100111001", "0111101001", "0000000001"),
				13: ("11111", "11111", "0111101110", "0111101001", "0000000001"),
				14: ("11111", "11111", "0110111100", "0111101001", "0000000001"),
				15: ("11111", "11111", "0110001010", "0111101001", "0000000001"),
				16: ("11111", "11111", "0101110001", "0111101001", "0000000001"),
				17: ("11111", "11111", "0100111111", "0111101001", "0000000001"),
				18: ("11111", "11111", "0100100110", "0111101001", "0000000001"),
				19: ("11111", "11111", "0100001101", "0111101001", "0000000001"),
				20: ("11111", "11111", "0011110100", "0111101001", "0000000001"),
				21: ("11111", "11111", "0011011011", "0111101001", "0000000001"),
				22: ("11111", "11111", "0011000010", "0111101001", "0000000001"),
				23: ("11111", "11111", "0010101001", "0111101001", "0000000001"),
				24: ("11111", "11111", "0010010000", "0111101001", "0000000001"),
				25: ("11111", "11111", "0010010000", "0111101001", "0000000001"),
				26: ("11111", "11111", "0001110111", "0111101001", "0000000001"),
				27: ("11111", "11111", "0001011110", "0111101001", "0000000001"),
				28: ("11111", "11111", "0001011110", "0111101001", "0000000001"),
				29: ("11111", "11111", "0001000101", "0111101001", "0000000001"),
				30: ("11111", "11111", "0001000101", "0111101001", "0000000001"),
				31: ("11111", "11111", "0000101100", "0111101001", "0000000001"),
				32: ("11111", "11111", "0000101100", "0111101001", "0000000001"),
				33: ("11111", "11111", "0000101100", "0111101001", "0000000001"),
				34: ("11111", "11111", "0000010011", "0111101001", "0000000001"),
				35: ("11111", "11111", "0000010011", "0111101001", "0000000001"),
				36: ("11111", "11111", "0000010011", "0111101001", "0000000001"),
				37: ("11111", "11111", "0011111010", "0111101001", "0000000001"),
				38: ("11111", "11111", "0011111010", "0111101001", "0000000001"),
				39: ("11111", "11111", "0011111010", "0111101001", "0000000001"),
				40: ("11111", "11111", "0011111010", "0111101001", "0000000001"),
				41: ("11111", "11111", "0011111010", "0111101001", "0000000001"),
				42: ("11111", "11111", "0011111010", "0111101001", "0000000001"),
				43: ("11111", "11111", "0011111010", "0111101001", "0000000001"),
				44: ("11111", "11111", "0011111010", "0111101001", "0000000001"),
				45: ("11111", "11111", "0011111010", "0111101001", "0000000001"),
				46: ("11111", "11111", "0011111010", "0111101001", "0000000001"),
				47: ("11111", "11111", "0011111010", "0111101001", "0000000001"),
				48: ("11111", "11111", "0011111010", "0111101001", "0000000001"),
				49: ("11111", "11111", "0011111010", "0111101001", "0000000001"),
				50: ("11111", "11111", "0011111010", "0111101001", "0000000001"),
				51: ("11111", "11111", "0011111010", "0111101001", "0000000001"),
				52: ("11111", "11111", "0011111010", "0111101001", "0000000001"),
				53: ("11111", "11111", "0011111010", "0111101001", "0000000001"),
				54: ("11111", "11111", "0011111010", "0111101001", "0000000001"),
				55: ("11111", "11111", "0011111010", "0111101001", "0000000001"),
				56: ("11111", "11111", "0011111010", "0111101001", "0000000001"),
				57: ("11111", "11111", "0011111010", "0111101001", "0000000001"),
				58: ("11111", "11111", "0011111010", "0111101001", "0000000001"),
				59: ("11111", "11111", "0011111010", "0111101001", "0000000001"),
				60: ("11111", "11111", "0011111010", "0111101001", "0000000001"),
				61: ("11111", "11111", "0011111010", "0111101001", "0000000001"),
				62: ("11111", "11111", "0011111010", "0111101001", "0000000001"),
				63: ("11111", "11111", "0011111010", "0111101001", "0000000001"),
				64: ("11111", "11111", "0011111010", "0111101001", "0000000001")
			}

			lock_reg1 = int("000000" + lock_dict[div][2], base=2)
			lock_reg2 = int("0" + lock_dict[div][1] + lock_dict[div][4], base=2)
			lock_reg3 = int("0" + lock_dict[div][0] + lock_dict[div][3], base=2)

			log.debug("DADDR_28: 0xFFFF\t-Power register leaving all interpolators on - ")
			log.debug("DADDR_18: {:#04x}\t-Lock Register 1: for M set to {:d} -".format(lock_reg1, div))
			log.debug("DADDR_19: {:#04x}\t-Lock Register 2: for M set to {}".format(lock_reg2, div))
			log.debug("DADDR_1A: {:#04x}\t-Lock Register 3: for M set to {}".format(lock_reg3, div))
			return lock_reg1, lock_reg2, lock_reg3

		def drp_clkout(self, divide, dutycycle, phase, clkout=0):
			"""
			:param divide:
			:param dutycycle: e.g. 0.5
			:param phase: e.g.11.25
			:param clkout: CLKOUT0 to CLKOUT6
			:return: the ordered pairs of DRP addresses & Data
			"""
			clkout = int(clkout)
			log.debug("Calculate clkout: {:d} (default = 0) output divide(O): {:} regs".format(clkout, divide))
			daddr_reg1 = 0x08
			daddr_reg2 = 0x09
			if clkout == 1:
				daddr_reg1 = 0x0a
				daddr_reg2 = 0x0b
			elif clkout == 2:
				daddr_reg1 = 0x0c
				daddr_reg2 = 0x0d
			elif clkout == 3:
				daddr_reg1 = 0x0e
				daddr_reg2 = 0x0f
			elif clkout == 4:
				daddr_reg1 = 0x10
				daddr_reg2 = 0x11
			elif clkout == 5:
				daddr_reg1 = 0x06
				daddr_reg2 = 0x07
			elif clkout == 5:
				daddr_reg1 = 0x12
				daddr_reg2 = 0x13

			if phase < 0:
				phase += 360.0

			phase_in_cycles = (phase / 360.0) * divide
			phasecycles_dec = 8 * phase_in_cycles
			phasecycles_int = int(phasecycles_dec)
			phasecycles_rem = phasecycles_dec - phasecycles_int
			if phasecycles_rem >= 0.5:
				phasecycles_int += 1
			phasecycles = int(phasecycles_int / 8)

			pmphasecycles = phasecycles_int - (phasecycles * 8)
			if (divide < 64):
				min_dc = 1.0 / divide
				max_dc = (divide - 0.5) / divide
			else:
				min_dc = (divide - 64.0) / divide
				max_dc = (64 + 0.5) / divide
			if dutycycle < min_dc:
				log.debug(
					"\n\tWARNING: Min duty cycle violation {} < {}\n\tChanging dutycycle to {}".format(dutycycle,
																									   min_dc,
																									   min_dc))
				dutycycle = min_dc
			if dutycycle > max_dc:
				log.debug("\n\tWARNING: Max duty cycle is {} > {}\n\tChanging dutycycle to {}".format(dutycycle,
																									 max_dc,
																									 max_dc))
				dutycycle = max_dc

			log.debug(
				"Requested phase is: {}; Given divide={} then phase increments in {};  ".format(phase, divide,
																								45.0 / divide))
			log.debug(
				"Requested Phase is: {}; Actual: {};  ".format(phase, (phasecycles * 360.0 / divide) + (
						pmphasecycles * 45.0 / divide)))

			ht = int(dutycycle * divide)
			lt = int(divide - ht)
			even_high = int(divide / 2)
			odd = int(divide - even_high * 2)
			if divide == 1:
				drp_reg1 = ((pmphasecycles & 0x7) << 13) + 0b1000001000001
				self.clkout0_reg1 = drp_reg1
				drp_reg2 = (odd << 7) + (1 << 6) + (phasecycles & 0x3f)
				self.clkout0_reg2 = drp_reg2
				log.debug("daddr_{:#2x}: {:#04x}\t-clkout{} register 1- ".format(daddr_reg1, drp_reg1, clkout))
				log.debug("daddr_{:#2x}: {:#04x}\t-clkout{} register 2- ".format(daddr_reg2, drp_reg2, clkout))
				return daddr_reg1, drp_reg1, daddr_reg2, drp_reg2
			elif math.fmod(divide, 1) == 0:
				# Integer divide
				drp_reg1 = ((pmphasecycles & 0x7) << 13) + (1 << 12) + ((ht & 0x3f) << 6) + (lt & 0x3f)
				self.clkout0_reg1 = drp_reg1
				drp_reg2 = ((odd & 0x1) << 7) + (phasecycles & 0x3f)
				self.clkout0_reg2 = drp_reg2
				log.debug(
					"Integer divide: daddr_{:#2x}: {:#04x}\t-clkout{} register 1- ".format(daddr_reg1, drp_reg1, clkout))
				log.debug(
					"Integer divide: daddr_{:#2x}: {:#04x}\t-clkout{} register 2- ".format(daddr_reg2, drp_reg2, clkout))
				return daddr_reg1, drp_reg1, daddr_reg2, drp_reg2
			elif clkout == 0:
				drp_frac_registers = self.drp_clkout_frac(divide, phase)
				drp_reg1 = drp_frac_registers[0]
				self.clkout0_reg1 = drp_reg1
				drp_reg2 = drp_frac_registers[1]
				self.clkout0_reg2 = drp_reg2
				daddr_regshared = 0x07
				drp_regshared = drp_frac_registers[2] << 10
				self.clkout0_shared_reg = drp_regshared
				log.debug(
					'Fractional divide: DADDR_{:#2x}: {:#04x}\t-clkout{} Register 1- '.format(daddr_reg1, drp_reg1, clkout))
				log.debug(
					'Fractional divide: DADDR_{:#2x}: {:#04x}\t-clkout{} Register 2- '.format(daddr_reg2, drp_reg2, clkout))
				log.debug(
					"DADDR_{:#2x}: {:#04x}\t- Register Shared with CLKOUT5- ".format(daddr_regshared, drp_regshared))
				return daddr_reg1, drp_reg1, daddr_reg2, drp_reg2, daddr_regshared, drp_regshared
			else:
				log.error(
					"ERROR: Fractional divide setting only supported for CLKOUT0. Output clock set to {}".format(clkout))
				sys.exit(-1)

		def drp_settings(self, m, d, phase, bw):
			"""
			:param m: CLKFBOUT_MULT
			:param d: DIVCLK_DIVIDE
			:param phase: 
			:param bw: BANDWIDTH can be: LOW, LOW_SS, HIGH, OPTIMIZED (case insensitive).
			:return: The ordered pairs of DRP addresses & Data
			"""
			if phase < 0:
				phase += 360.0

			clkfb_regs = self.drp_calc_m(m, phase)
			self.clkfbout_reg1 = clkfb_regs[0]
			self.clkfbout_reg2 = clkfb_regs[1]
			if len(clkfb_regs) == 3:
				self.clkfbout_shared_reg = clkfb_regs[2]

			div_reg = self.drp_calc_d(d)
			self.div_reg = div_reg

			filter_regs = self.drp_cpres(m, bw)
			self.filter_reg1 = filter_regs[0]
			self.filter_reg2 = filter_regs[1]

			locking_regs = self.drp_locking(m)
			self.lock_reg1 = locking_regs[0]
			self.lock_reg2 = locking_regs[1]
			self.lock_reg3 = locking_regs[2]

			return clkfb_regs, div_reg, filter_regs, locking_regs

		def is_locked(self, clk_sel):
			reg_name = self.sca_base + "ref_locked"
			if int(clk_sel) == 1:
				reg_name = self.sca_base + "dff_locked"
			node = self.hw.getNode(reg_name)
			locked_raw = node.read()
			self.hw.dispatch()
			log.debug("locked chn = {:d} value={:d}".format(clk_sel, locked_raw.value()))
			if locked_raw.value() == 1:
				return True
			else:
				return False

		def rst_mmcm(self, clk_sel, enabled, go_dispatch=False):
			reg_name = self.sca_base + "rst_ref"
			if int(clk_sel) == 1:
				reg_name = self.sca_base + "rst_dff"
			log.debug("clk_sel: {:d} \t reg_name: {:}".format(clk_sel, reg_name))
			node = self.hw.getNode(reg_name)
			write_val = 0
			if enabled:
				write_val = 1
			node.write(write_val)
			if go_dispatch:
				self.hw.dispatch()

		def rst_drp(self, clk_sel, enabled, go_dispatch=False):
			reg_name = self.sca_base + "rst_ref_drp"
			if int(clk_sel) == 1:
				reg_name = self.sca_base + "rst_dff_drp"
			log.debug("clk_sel: {:d} \t reg_name: {:}".format(clk_sel, reg_name))
			node = self.hw.getNode(reg_name)
			write_val = 0
			if enabled:
				write_val = 1
			node.write(write_val)
			if go_dispatch:
				self.hw.dispatch()

		def w_reg(self, reg, val, reg_base, go_dispatch):
			reg_name = reg_base + reg
			node = self.hw.getNode(reg_name)
			node.write(val)
			if go_dispatch:
				self.hw.dispatch()

		def set_clock(self, divide_O, mult, divide, clk_sel):
			clk_sel = int(clk_sel)
			duty_cycle = 0.5
			phase_O = .0
			phase_fb = .0
			bw = "opt"
			mmcm_clk = 0
			divide_O_regs = self.drp_clkout(divide_O, duty_cycle, phase_O, mmcm_clk)
			regs_drp_settings = self.drp_settings(mult, divide, phase_fb, bw)
			## MMCM rst pin must be assert during DRP
			self.rst_drp(clk_sel, False, False)
			self.rst_mmcm(clk_sel, True, False)

			clk_reg_base = self.refclk_base
			if clk_sel == 1:
				clk_reg_base = self.dffclk_base

			write_seq = {"power_reg": self.power_reg, "clkout0_reg2": self.clkout0_reg2,
						 "clkout0_reg1": self.clkout0_reg1,
						 "clkout0_shared_reg": self.clkout0_shared_reg, "clkfbout_shared_reg": self.clkfbout_shared_reg,
						 "div_reg": self.div_reg, "clkfbout_reg1": self.clkfbout_reg1,
						 "clkfbout_reg2": self.clkfbout_reg2,
						 "lock_reg1": self.lock_reg1, "lock_reg2": self.lock_reg2, "lock_reg3": self.lock_reg3,
						 "filter_reg1": self.filter_reg1, "filter_reg2": self.filter_reg2}
			if len(divide_O_regs) != 3:
				del write_seq["clkout0_shared_reg"]
			if len(regs_drp_settings[0]) != 3:
				del write_seq["clkfbout_shared_reg"]

			## Write regs
			for reg in write_seq.keys():
				self.w_reg(reg, write_seq[reg], clk_reg_base, False)
			# Deassert after DRP
			self.rst_mmcm(clk_sel, False, False)
			## Set DRP Ports tp default
			self.rst_drp(clk_sel, True, True)
			## Clear dictionary
			del write_seq
			return True

		def set_frq(self, chn, frq, prec=0.1):
			mmcm_inst = Mmcm(frq)
			while True:
				## Set Sca Clocks, parameters: Do, M, D
				## Frq: (clkin * M)/(DO * D)
				DO, M, D = mmcm_inst.get_parameters()
				## Ch 0 = REF CLK; ch 1 = DFF CLK
				freq_calc = mmcm_inst.Fin * M / (DO * D)
				log.debug("Calculating clkout frequency is clk {} : {}".format(chn, freq_calc))
				diff = abs(100 * (freq_calc - frq) / frq)
				log.debug("Freq diff percent: {:}%".format(diff))
				if diff > prec:
					mmcm_inst.M -= 0.125
					continue
				else:
					log.info("Calculated clkout frequency is clk {} : {}".format(chn, freq_calc))
					log.info("Freq diff percent: {:}%".format(diff))
					self.set_clock(DO, M, D, chn)
					if self.is_locked(chn):
						log.info("Clock channel {:d} is locked!".format(chn))
						break
					self.rst_mmcm(chn, True, True)
					log.error("Clock channel {:d} is not locked!".format(chn))
