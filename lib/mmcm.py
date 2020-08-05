# Kintex -2 MMCM Parameters, Ref: Xilinx DS182, UG472
import math
import logging
import coloredlogs

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
coloredlogs.install(level='INFO', logger=log)

__author__ = "Sheng Dong"
__email__ = "s.dong@mails.ccnu.edu.cn"


class Mmcm:
    def __init__(self, Fout):

        self.Fout = Fout
        self.Fin = 31.25  # MHz

        self.Fin_min = 933
        self.Fin_max = 10
        self.Fpfd_max = 500
        self.Fpfd_min = 10
        self.Fvco_max = 1440
        self.Fvco_min = 200
        self.Fout_max = 933
        self.Fout_min = 4.69

        self.Dmin = self.get_Dmin()
        self.Dmax = self.get_Dmax()
        self.Mmin = self.get_Mmin()
        self.Mmax = self.get_Mmax()
        self.Mideal = self.get_Mideal()
        self.DOmin = 2.0
        self.DOmax = 128.0

        # self.M = int(self.Mideal/0.125)*0.125
        self.M = int(self.Mmax / 0.125) * 0.125
        self.DO = self.DOmin
        self.D = math.ceil((self.Fin * self.M) / (self.DO * Fout))

    def get_Dmin(self):
        Dmin = math.ceil(self.Fin / self.Fpfd_max)
        if Dmin < 1:
            Dmin = 1.0
        log.debug("Dmin: {}".format(Dmin))
        return Dmin

    def get_Dmax(self):
        Dmax = math.floor(self.Fin / self.Fpfd_min)
        if Dmax > 128:
            Dmax = 128.0
        log.debug("Dmax: {}".format(Dmax))
        return Dmax

    def get_Mmin(self):
        Mmin = self.Dmin * self.Fvco_min / self.Fin
        if Mmin < 2:
            Mmin = 2.0
        log.debug("Mmin: {}".format(Mmin))
        return Mmin

    def get_Mmax(self):
        Mmax = self.Dmax * self.Fvco_max / self.Fin
        if Mmax > 64:
            Mmax = 64.0 - 0.125
        log.debug("Mmax: {}".format(Mmax))
        return Mmax

    def get_Mideal(self):
        Mideal = self.Dmin * self.Fvco_max / self.Fin
        log.debug("Mideal: {}".format(Mideal))
        return Mideal

    def check_parameters(self, divide_O, mult, divide):
        if not isinstance(divide, int):
            self.D = int(divide)
            log.debug("Divide must be integer only, convert to {:}".format(self.D))
        if divide < self.Dmin:
            self.D = self.Dmin
            log.debug("Divide must be bigger than {0:}, set Divide to {0:}".format(self.D))
            return False
        elif divide > self.Dmax:
            self.D = self.Dmax
            log.debug("Divide must be less than {0:}, set Divide to {0:}".format(self.D))
            return False

        if mult < self.Mmin:
            self.M = self.Mmin
            log.debug("Mult must be bigger than {0:}, set Mult to {0:}".format(self.M))
            return False
        elif mult > self.Mmax:
            self.M = self.Mmax
            log.debug("Mult must be less than {0:}, set Mult to {0:}".format(self.M))
            return False

        if divide_O < self.DOmin:
            self.DO = self.DOmin
            log.debug("Divide_O must be bigger than {0:}, set Divide_O to {0:}".format(self.DO))
            return False
        elif divide_O > self.DOmax:
            self.DO = self.DOmax
            log.debug("Divide_O must be less than {0:}, set Divide_O to {0:}".format(self.DO))
            return False

        return True

    def get_parameters(self):
        while True:
            if self.check_parameters(self.DO, self.M, self.D):
                break
            else:
                self.DO += 0.125
                if self.DO > self.DOmax:
                    self.DO = self.Dmin
                self.D = math.ceil((self.Fin * self.M) / (self.DO * self.Fout))

        log.debug("Get DO: {} \t M: {} \t D: {}".format(self.DO, self.M, self.D))
        return self.DO, self.M, self.D
