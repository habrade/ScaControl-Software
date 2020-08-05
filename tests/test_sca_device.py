import pytest

from lib.ipbus_link import IPbusLink
from lib.sca_device import ScaDevice


@pytest.fixture
def foo_sca_dev():
    hw = IPbusLink().get_hw()
    sca_dev = ScaDevice(hw)
    return sca_dev


@pytest.mark.parametrize('DO, dutycycle, phase, clk_sel, expected', [(2, 0.5, 0, 0, (0x08, 0x1041, 0x09, 0x0)),
                                                                     (1, 0.5, 60, 0, (0x08, 0x3041, 0x09, 0x00c0)),
                                                                     (2.2, 0.5, 60, 0,
                                                                      (0x08, 0x7000, 0x09, 0x1c00, 0x07, 0x1800))
                                                                     ])
def test_drp_clkout(DO, dutycycle, phase, clk_sel, expected, foo_sca_dev):
    assert foo_sca_dev.drp_clkout(DO, dutycycle, phase, clk_sel) == expected


@pytest.mark.parametrize('m, d, phase, bw, expected', [(2, 3, 0, "high", ((0x1041, 0x0000), 0x0042,
                                                                          (0x1000, 0x9900), (0x01e8, 0x1801, 0x19e9))),
                                                       (2.2, 3.2, 0, "low",
                                                        ((0x1000, 0x1c00, 0x0000), 0x0042, (0x0800, 0x9900),
                                                         (0x01e8, 0x1801, 0x19e9)))])
def test_xapp888_drp_settings(m, d, phase, bw, expected, foo_sca_dev):
    assert foo_sca_dev.drp_settings(m, d, phase, bw) == expected
