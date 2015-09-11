# -*- coding: utf-8 -*-

"""
Created on Wed May 30 11:53:52 2012

@author: mmikofski
"""
import numpy as np
import scipy.constants

# Defaults
RS = 0.004267236774264931  # [ohm] series resistance
RSH = 10.01226369025448  # [ohm] shunt resistance
ISAT1_T0 = 2.286188161253440E-11  # [A] diode one saturation current
ISAT2 = 1.117455042372326E-6  # [A] diode two saturation current
APH = 1.000426348582935  # photovoltaic current coefficient
ISC0_T0 = 6.3056  # [A] reference short circuit current
TCELL = 298.15  # [K] cell temperature
VBYPASS = -0.5  # [V] trigger voltage of bypass diode
ARBD = 1.036748445065697E-4  # reverse breakdown coefficient
VRBD_ = -5.527260068445654  # [V] reverse breakdown voltage
NRBD = 3.284628553041425  # reverse breakdown exponent
CELLAREA = 153.33  # [cm^2] cell area
EG = 1.1  # [eV] band gap of cSi
ALPHA_ISC = 0.0003551  # [1/K] short circuit current temperature coefficient


class PVcell(object):
    """
    PVconstants - Class for PV constants
    """
    def __init__(self, Rs=RS, Rsh=RSH, Isat1_T0=ISAT1_T0, Isat2=ISAT2, Aph=APH,
                 Isc0_T0=ISC0_T0, Tcell=TCELL, cellArea=CELLAREA,
                 Vbypass=VBYPASS, aRBD=ARBD, VRBD=VRBD_, nRBD=NRBD, Eg=EG,
                 alpha_Isc=ALPHA_ISC):
        # hard constants
        self.k = scipy.constants.k  # [kJ/mole/K] Boltzmann constant
        self.q = scipy.constants.e  # [Coloumbs] elementary charge
        self.E0 = 1000.  # [W/m^2] irradiance of 1 sun
        self.T0 = 298.15  # [K] reference temperature
        # user inputs
        self.Eg = float(Eg)  # [eV] band gap of cSi
        self.alpha_Isc = float(alpha_Isc)  # [1/K] short circuit temp. coeff.
        self.Tcell = float(Tcell)  # [K] cell temperature
        self.Rs = float(Rs)  # [ohm] series resistance
        self.Rsh = float(Rsh)  # [ohm] shunt resistance
        self.Isat1_T0 = float(Isat1_T0)  # [A] diode one sat. current at T0
        self.Isat1 = self.calc_Isat1()  # [A] Isat1 at Tcell
        self.Isat2 = float(Isat2)  # [A] diode two saturation current
        self.Aph = float(Aph)  # photovoltaic current coefficient
        self.Isc0_T0 = float(Isc0_T0)  # [A] short circuit current at T0
        self.Isc0 = self.calc_Isc0()  # [A] Isc0 at Tcell
        self.cellArea = float(cellArea)  # [cm^2] cell area
        self.Vbypass = float(Vbypass)  # [V] trigger voltage of bypass diode
        self.aRBD = float(aRBD)  # reverse breakdown coefficient
        self.VRBD = float(VRBD)  # [V] reverse breakdown voltage
        self.nRBD = float(nRBD)  # reverse breakdown exponent
        # set number of points in IV curve(s)
        self.npts = npts  # number of points
        # point spacing from 0 to 1, used for Vcell, Vmod, Vsys and Istring
        # decrease point spacing as voltage approaches Voc by using logspace
        pts = (11. - np.logspace(np.log10(11.), 0., self.npts)) / 10.
        pts[0] = 0.  # first point must be exactly zero
        self.pts = pts.reshape(self.npts, 1)
        negpts = (11. - np.logspace(np.log10(11. - 1./float(self.npts)),
                                    0., self.npts)) / 10.
        negpts = negpts.reshape(self.npts, 1)
        self.Imod_negpts = 1 + 1./float(self.npts)/10. - negpts
        self.negpts = np.flipud(negpts)  # reverse the order
        # shift and concatenate pvconst.negpts and pvconst.pts
        # so that tight spacing is around MPP and RBD
        self.Imod_pts = 1 - np.flipud(self.pts)
        # multiprocessing
        self.parallel = parallel  # use multiprocessing if True
        self.procs = procs  # number of processes in pool
        self.maxtasksperchild = maxtasksperchild  # number of tasks per worker
        self.chunksize = chunksize  # size of tasks

    def update(self, *args, **kwargs):
        """
        Update user-defined constants.
        """
        kw = ['Rs', 'Rsh', 'Isat1_T0', 'Isat2', 'Aph', 'Isc0_T0', 'Tcell',
              'cellArea', 'Vbypass', 'aRBD', 'VRBD', 'nRBD', 'npts', 'Eg',
              'alpha_Isc']
        key = 0
        keys = []
        # set positional arguements (*args)
        for val in args:
            self.__setattr__(kw[key], float(val))
            key += 1
            keys.append(kw[key])
        # set optional arguments (*kwargs)
        for key in kwargs:
            if key in kw:
                self.__setattr__(key, float(kwargs[key]))
        # Check & update Isat1
        calc_Isat1 = 'Isat1_T0' in keys or 'Isat1_T0' in kwargs.keys()
        calc_Isat1 = calc_Isat1 or 'Tcell' in keys or 'Tcell' in kwargs.keys()
        calc_Isat1 = calc_Isat1 or 'Eg' in keys or 'Eg' in kwargs.keys()
        if calc_Isat1:
            self.Isat1 = self.calc_Isat1()  # [A] Isat1
        # Check & update Isc0
        calc_Isc0 = 'Isc0_T0' in keys or 'Isc0_T0' in kwargs.keys()
        calc_Isc0 = calc_Isc0 or 'Tcell' in keys or 'Tcell' in kwargs.keys()
        calc_Isc0 = (calc_Isc0 or
                       'alpha_Isc' in keys or 'alpha_Isc' in kwargs.keys())
        if calc_Isc0:
            self.Isc0 = self.calc_Isc0()  # [A] Isc0

    # TODO: try to override self.__setattr__  # IGNORE:W0511
    def calc_Isat1(self):
        """
        Diode one saturation current at Tcell.
        """
        _Tstar = self.Tcell ** 3 / self.T0 ** 3  # scaled temperature
        _inv_delta_T = 1 / self.T0 - 1 / self.Tcell  # [1/K]
        _expTstar = np.exp(self.Eg * self.q / self.k * _inv_delta_T)
        return self.Isat1_T0 * _Tstar * _expTstar  # [A] Isat1(Tcell)

    def calc_Isc0(self):
        """
        Short circuit current at Tcell
        """
        _delta_T = self.Tcell - self.T0  # [K] temperature difference
        return self.Isc0_T0 * (1 + self.alpha_Isc * _delta_T)  # [A] Isc0