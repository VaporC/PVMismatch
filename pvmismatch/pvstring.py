# -*- coding: utf-8 -*-
"""
Created on Mon Jun 11 14:07:12 2012

@author: mmikofski
"""

from copy import deepcopy
from matplotlib import pyplot as plt
from pvmismatch.pvconstants import PVconstants, npinterpx
from pvmismatch.pvmodule import PVmodule, PTS, NPTS
import numpy as np

_numberMods = 10  # default number of modules


class PVstring(object):
    """
    PVstring - A class for PV strings.
    """

    def __init__(self, pvconst=PVconstants(), numberMods=_numberMods,
                 pvmods=None):
        """
        Constructor
        """
        self.pvconst = pvconst
        self.numberMods = numberMods
        if pvmods is None:
            # use deep copy instead of making each object in a for-loop
            self.pvmods = [PVmodule(pvconst=self.pvconst)] * self.numberMods
            self.pvmods[1:] = [deepcopy(pvmod) for pvmod in self.pvmods[1:]]
        elif ((type(pvmods) is list) and
              all([(type(pvmod) is PVmodule) for pvmod in pvmods])):
            self.numberMods = len(pvmods)
            self.pvmods = pvmods
        elif (type(pvmods) is list) and (len(pvmods) == self.numberMods):
            self.pvmods = pvmods
        else:
            raise Exception("Invalid modules list!")
        (self.Istring, self.Vstring, self.Pstring) = self.calcString()

    def calcString(self):
        """
        Calculate string I-V curves.
        Returns (Istring, Vstring, Pstring) : tuple of numpy.ndarray of float
        """
        # scale with max irradiance, so that Ee > 1 is not a problem
        maxEe = np.max([np.max(pvmod.Ee) for pvmod in self.pvmods])
        Istring = np.max(maxEe) * self.pvconst.Isc0 * PTS
        # pylint: disable = E1103
        Ineg = np.linspace(-np.max(Istring),
                           -1 / float(NPTS), NPTS).reshape(NPTS, 1)
        # pylint: disable = E1103
        Istring = np.concatenate((Ineg, Istring), axis=0)
        Vstring = np.zeros((2 * NPTS, 1))
        for mod in self.pvmods:
            xp = mod.Imod.squeeze()  # IGNORE:E1103
            fp = mod.Vmod.squeeze()  # IGNORE:E1103
            Vstring += npinterpx(Istring, xp, fp)
        Pstring = Istring * Vstring
        return (Istring, Vstring, Pstring)

    def plotStr(self):
        """
        Plot string I-V curves.
        Returns strPlot : matplotlib.pyplot figure
        """
        strPlot = plt.figure()
        plt.subplot(2, 1, 1)
        plt.plot(self.Vstring, self.Istring)
        plt.title('String I-V Characteristics')
        plt.ylabel('String Current, I [A]')
        plt.ylim(ymax=self.pvconst.Isc0 + 1)
        plt.grid()
        plt.subplot(2, 1, 2)
        plt.plot(self.Vstring, self.Pstring)
        plt.title('String P-V Characteristics')
        plt.xlabel('String Voltage, V [V]')
        plt.ylabel('String Power, P [W]')
        plt.grid()
        return strPlot
