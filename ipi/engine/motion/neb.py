"""Holds the algorithms to perform nudged elastic band calculations.

Algorithms implemented by Michele Ceriotti and Bejamin Helfrecht, 2015
"""

# This file is part of i-PI.
# i-PI Copyright (C) 2014-2015 i-PI developers
# See the "licenses" directory for full license information.


import numpy as np
import time

from ipi.engine.motion import Motion
from ipi.utils.depend import *
from ipi.utils.softexit import softexit
from ipi.utils.mintools import L_BFGS, min_brent_neb
from ipi.utils.messages import verbosity, info


__all__ = ['NEBMover']


# TODO: Do not shout :-)
# NOTE: CURRENTLY, NEB ONLY WORKS FOR L-BFGS MINIMIZATION.
#       IF SD, CG, OR BFGS OPTIONS ARE NOT DESIRED, CONSIDER ELIMINATING
#       NEBLineMover AND THE RELEVANT BLOCKS IN NEBMover. IF THESE OPTIONS ARE DESIRED,
#       THE INFRASTRUCTURE IS PRESENT BUT MUST BE DEBUGGED AND MADE CONSISTENT WITH
#       THAT PRESENT IN NEBBFGSMover (TO REMOVE REMAINING ERRORS IN COMPUTATION).
#       CLIMBING IMAGE AND VARIABLE SPRING CONSTANTS HAVE NOT YET BEEN IMPLEMENTED, BUT
#       THE GENERIC INFRASTRUCTURE IS PRESENT (SEE COMMENTED BLOCKS IN NEBLineMover AND
#       NEBBFGSMover). REQUIRES REARRANGEMENT AND DEBUGGING.
#       THIS NEB IMPLEMENTATION USES THE 'IMPROVED TANGENTS' OF HENKELMAN AND JONSSON, 2000.
#       THE 'OLD IMPLEMENTATION' IS PRESERVED IN COMMENTS


class NEBLineMover(object):
    """Creation of the one-dimensional function that will be minimized

    Attributes:
        x0: initial position
        d: move direction
        kappa: spring constants
        first: flag indicating first iteration of simulation
    """

    def __init__(self):
        self.x0 = None
        self.d = None
        self.kappa = None
        self.first = True

    def bind(self, ens):
        self.dbeads = ens.beads.copy()
        self.dcell = ens.cell.copy()
        self.dforces = ens.forces.copy(self.dbeads, self.dcell)

    def set_dir(self, x0, mdir):
        self.x0 = x0.copy()
        self.d = mdir.copy() / np.sqrt(np.dot(mdir.flatten(), mdir.flatten()))
        if self.x0.shape != self.d.shape:
            raise ValueError("Incompatible shape of initial value and displacement direction")

    def __call__(self, x):
        if self.first is True:
            self.dbeads.q = x
        else:
            self.dbeads.q = self.x0 + self.d * x

        # List of atom/bead positions
        bq = depstrip(self.dbeads.q).copy()

        # List of forces
        bf = depstrip(self.dforces.f).copy()

        # List of bead energies
        be = depstrip(self.dforces.pots).copy()

        # Number of images
        nimg = self.dbeads.nbeads

        # Number of atoms
        nat = self.dbeads.natoms

        kappa = np.zeros(nimg)

        # Get tangents, end images are distinct, fixed, pre-relaxed configurations
        btau = np.zeros((nimg, 3 * nat), float)
        for ii in range(1, nimg - 1):
            d1 = bq[ii] - bq[ii - 1]   # tau mius
            d2 = bq[ii + 1] - bq[ii]   # tau plus

            # "Old" implementation of NEB
            btau[ii] = d1 / np.linalg.norm(d1) + d2 / np.linalg.norm(d2)
            btau[ii] *= 1.0 / np.linalg.norm(btau)

#            # Energy of images: (ii+1) < (ii) < (ii-1)
#            if (be[ii + 1] < be[ii]) and (be[ii] < be[ii - 1]):
#                btau[ii] = d2
#
#            # Energy of images (ii-1) < (ii) < (ii+1)
#            elif (be[ii - 1] < be[ii]) and (be[ii] < be[ii + 1]):
#                btau[ii] = d1
#
#            # Energy of image (ii) is a minimum or maximum
#            else:
#                maxpot = max(be[ii + 1] - be[ii], be[ii - 1], be[ii])
#                minpot = min(be[ii + 1] - be[ii], be[ii - 1], be[ii])
#
#                if be[ii + 1] < be[ii - 1]:
#                    btau[ii] = d1 * minpot + d2 * maxpot
#
#                elif be[ii - 1] < be[ii + 1]:
#                    btau[ii] = d1 * maxpot + d2 * minpot
#
#                else:
#                    print "Error in NEB tangents: Energy of images are equal"
#
#            btau[ii] *= 1.0 / np.linalg.norm(btau)


        #if mode == "variablesprings": #TODO: input option for variable spring mode


#        if mode == "ci":
#
#        # Climbing NEB term. Choose highest energy bead after 5 (arbitrary) iterations
#            if step >= 5:
#                imax = np.argmax(be)
#                bf[imax] = bf[imax] - 2 * np.dot(bf[imax], btau[imax]) * btau[imax]
#
#                # Determine variable spring constants
#                #kappa = np.zeros(nimg)
#                #ei = np.zeros(nimg)
#                #emax = np.amax(be)
#                #eref = max(be[0], be[nimg])
#                #kappamax = self.kappa_max
#                #kappamin = self.kappa_min #TODO: input options for max and min spring constant
#                #deltakappa = kappamax - kappamin
#                #for ii in range(1, nimg - 1):
#                #    ei[ii] = max(be[ii], be[ii - 1])
#                #    if ei[j] > eref:
#                #        kappa[ii] = kappamax - deltakappa * ((emax - ei[ii]) / (emax - eref))
#                #    else:
#                #        kappa[ii] = kappamin
#
#        else:
#            kappa.fill(self.kappa)
#
#
#            # get perpendicular forces
#            for ii in range(1, nimg - 1):
#                bf[ii] = bf[ii] - np.dot(bf[ii], btau[ii]) * btau[ii]
#
#            # adds the spring forces
#            for ii in range(1, nimg - 1):
#                bf[ii] += kappa[ii] * btau[ii] * np.dot(btau[ii], (bq[ii + 1] + bq[ii - 1] - 2 * bq[ii]))

        kappa.fill(self.kappa)

        # get perpendicular forces
        for ii in range(1, nimg - 1):
            bf[ii] = bf[ii] - np.dot(bf[ii], btau[ii]) * btau[ii]

        # adds the spring forces
        for ii in range(1, nimg - 1):
            bf[ii] += kappa[ii] * btau[ii] * np.dot(btau[ii], (bq[ii + 1] + bq[ii - 1] - 2 * bq[ii]))

        # For first iteration, move in direction of the force
        if self.first is True:
            self.d = bf
            self.first = False

        force = bf
        g = -np.dot(bf.flatten(), self.d.flatten())
        g = abs(g)

        # Return NEB forces and gradient modulus
        linefunc = (force, g)
        return linefunc


class NEBBFGSMover(object):
    """Creation of the multi-dimensional function that will be minimized

    Attributes:
        x0: initial position
        d: move direction
        xold: position from previous step
        kappa: spring constants"""

    def __init__(self):
        self.x0 = None
        self.d = None
        self.xold = None
        self.kappa = None

    def bind(self, ens):
        self.dbeads = ens.beads.copy()
        self.dcell = ens.cell.copy()
        self.dforces = ens.forces.copy(self.dbeads, self.dcell)

    def __call__(self, x):

        # Bead positions
        self.dbeads.q = x
        bq = depstrip(self.dbeads.q).copy()

        # Forces
        bf = depstrip(self.dforces.f).copy()

        # Bead energies
        be = depstrip(self.dforces.pots).copy()

        # Number of beads
        nimg = self.dbeads.nbeads

        # Number of atoms
        nat = self.dbeads.natoms

        # Array for sping constants
        kappa = np.zeros(nimg)

        # get tangents, end images are distinct, fixed, pre-relaxed configurations
        btau = np.zeros((nimg, 3 * nat), float)
        for ii in range(1, nimg - 1):
            d1 = bq[ii] - bq[ii - 1]   # tau minus
            d2 = bq[ii + 1] - bq[ii]   # tau plus

            # Old implementation of NEB tangents
            #btau[ii] = d1 / np.linalg.norm(d1) + d2 / np.linalg.norm(d2)
            #btau[ii] *= 1.0 / np.linalg.norm(btau)

            # Energy of images: (ii+1) < (ii) < (ii-1)
            if (be[ii + 1] < be[ii]) and (be[ii] < be[ii - 1]):
                btau[ii] = d1

            # Energy of images (ii-1) < (ii) < (ii+1)
            elif (be[ii - 1] < be[ii]) and (be[ii] < be[ii + 1]):
                btau[ii] = d2

            # Energy of image (ii) is a minimum or maximum
            else:
                maxpot = max(abs(be[ii + 1] - be[ii]), abs(be[ii - 1] - be[ii]))
                minpot = min(abs(be[ii + 1] - be[ii]), abs(be[ii - 1] - be[ii]))

                if be[ii + 1] < be[ii - 1]:
                    btau[ii] = d2 * minpot + d1 * maxpot

                elif be[ii - 1] < be[ii + 1]:
                    btau[ii] = d2 * maxpot + d1 * minpot

                else:
                    print "Error in NEB tangents: Energy of images are equal"

            btau[ii] *= 1.0 / np.linalg.norm(btau)


        #if mode == "variablesprings":


#        if mode == "ci":
#
#        # Climbing NEB term. Choose highest energy bead after 5 (arbitrary) iterations
#            if step >= 5:
#                imax = np.argmax(be)
#                bf[imax] = bf[imax] - 2 * np.dot(bf[imax], btau[imax]) * btau[imax]
#
#                # Determine variable spring constants
#                #kappa = np.zeros(nimg)
#                #ei = np.zeros(nimg)
#                #emax = np.amax(be)
#                #eref = max(be[0], be[nimg])
#                #kappamax = self.spring["kappa_max"]
#                #kappamin = self.spring["kappa_min"]
#                #deltakappa = kappamax - kappamin
#                #for ii in range(1, nimg - 1):
#                #    ei[ii] = max(be[ii], be[ii - 1])
#                #    if ei[j] > eref:
#                #        kappa[ii] = kappamax - deltakappa * ((emax - ei[ii]) / (emax - eref))
#                #    else:
#                #        kappa[ii] = kappamin
#
#        else:
#            kappa.fill(self.kappa)
#
        # Array of spring constants; all are equal
        kappa.fill(self.kappa)

        # Get perpendicular forces
        for ii in range(1, nimg - 1):
            bf[ii] = bf[ii] - np.dot(bf[ii], btau[ii]) * btau[ii]

        # Adds the spring forces
        for ii in range(1, nimg - 1):

            # Old implementation
            #bf[ii] += kappa[ii] * btau[ii] * np.dot(btau[ii], (bq[ii + 1] + bq[ii - 1] - 2 * bq[ii]))
            bf[ii] += kappa[ii] * (np.linalg.norm(bq[ii + 1] - bq[ii]) - np.linalg.norm(bq[ii] - bq[ii - 1])) * btau[ii]

        # Return forces and modulus of gradient
        g = -bf
        e = np.linalg.norm(g)   # self.dforces.pot # 0.0
        return e, g


class NEBMover(Motion):
    """Nudged elastic band routine.

    Attributes:
        mode: minimizer to use for NEB
        maximum_step: maximum step size for BFGS/L-BFGS
        cg_old_force: force from previous iteration
        cg_old_direction: direction from previous iteration
        invhessian: inverse Hessian for BFGS/L-BFGS
        ls_options:
            tolerance: tolerance for exit of line search
            iter: maximum iterations for line search per MD step
            step: initial step size for SD/CG
            adaptive: flag for adaptive step size
        tolerances:
            energy: tolerance on change in energy for exiting minimization
            force: tolerance on force/change in force for exiting minimization
            position: tolerance and change in position for exiting minimization
        corrections: number of corrections to store for L-BFGS
        qlist: list of previous positions (x_n+1 - x_n) for L-BFGS
        glist: list of previous gradients (g_n+1 - g_n) for L-BFGS
        endpoints: flag for minimizing end images in NEB *** NOT YET IMPLEMENTED ***
        spring:
            varsprings: T/F for variable spring constants
            kappa: single spring constant if varsprings is F
            kappamax: max spring constant if varsprings is T *** NOT YET IMPLEMENTED ***
            kappamin: min spring constant if varsprings is T *** NOT YET IMPLEMENTED ***
        climb: flag for climbing image NEB *** NOT YET IMPLEMENTED ***
    """

    def __init__(self, fixcom=False, fixatoms=None,
                 mode="sd",
                 maximum_step=100.0,
                 cg_old_force=np.zeros(0, float),
                 cg_old_direction=np.zeros(0, float),
                 invhessian=np.eye(0),
                 ls_options={"tolerance": 1e-5, "iter": 100.0, "step": 1e-3, "adaptive": 1.0},
                 tolerances={"energy": 1e-5, "force": 1e-5, "position": 1e-5},
                 corrections=5,
                 qlist=np.zeros(0, float),
                 glist=np.zeros(0, float),
                 endpoints=True,
                 spring={"varsprings": False, "kappa": 1.0, "kappamax": 1.5, "kappamin": 0.5},
                 climb=False):
        """Initialises NEBMover.

        Args:
           fixcom: An optional boolean which decides whether the centre of mass
              motion will be constrained or not. Defaults to False.
        """

        super(NEBMover, self).__init__(fixcom=fixcom, fixatoms=fixatoms)

        # Optimization options
        self.ls_options = ls_options
        self.tolerances = tolerances
        self.mode = mode
        self.max_step = maximum_step
        self.cg_old_f = cg_old_force
        self.cg_old_d = cg_old_direction
        self.invhessian = invhessian
        self.corrections = corrections
        self.qlist = qlist
        self.glist = glist
        self.endpoints = endpoints
        self.spring = spring
        self.climb = climb

        self.neblm = NEBLineMover()
        self.nebbfgsm = NEBBFGSMover()

    def bind(self, ens, beads, nm, cell, bforce, prng):

        super(NEBMover,self).bind(ens, beads, nm, cell, bforce, prng)
        if self.cg_old_f.shape != beads.q.shape:
            if self.cg_old_f.shape == (0,):
                self.cg_old_f = np.zeros(beads.q.shape, float)
            else:
                raise ValueError("Conjugate gradient force size does not match system size")
        if self.cg_old_d.shape != beads.q.shape:
            if self.cg_old_d.shape == (0,):
                self.cg_old_d = np.zeros(beads.q.shape, float)
            else:
                raise ValueError("Conjugate gradient direction size does not match system size")
        if self.invhessian.size != (beads.q.size * beads.q.size):
            if self.invhessian.size == 0:
                self.invhessian = np.eye(beads.q.flatten().size, beads.q.flatten().size, 0, float)
            else:
                raise ValueError("Inverse Hessian size does not match system size")

        self.neblm.bind(self)
        self.nebbfgsm.bind(self)

    def step(self, step=None):
        """Does one simulation time step."""

        info("\nMD STEP %d" % step, verbosity.debug)

        # Fetch spring constants
        self.nebbfgsm.kappa = self.spring["kappa"]
        self.neblm.kappa = self.spring["kappa"]

        self.ptime = self.ttime = 0
        self.qtime = -time.time()

        if self.mode == "lbfgs":

            # L-BFGS Minimization
            # Initialize direction to the steepest descent direction
            if step == 0:   # or np.sqrt(np.dot(self.bfgsm.d, self.bfgsm.d)) == 0.0: <-- this part for restarting at claimed minimum
                info(" @GEOP: Initializing L-BFGS", verbosity.debug)
                fx, nebgrad = self.nebbfgsm(self.beads.q)

                # Set direction to direction of NEB forces
                self.nebbfgsm.d = -nebgrad
                self.nebbfgsm.xold = self.beads.q.copy()

                # Initialize lists of previous positions and gradients
                self.qlist = np.zeros((self.corrections, len(self.beads.q.flatten())))
                self.glist = np.zeros((self.corrections, len(self.beads.q.flatten())))

            else:
                fx, nebgrad = self.nebbfgsm(self.beads.q)

            # Intial gradient and gradient modulus
            u0, du0 = (fx, nebgrad)

            # Store old force
            self.cg_old_f[:] = -nebgrad

            # Do one iteration of L-BFGS and return positions, gradient modulus,
            # direction, list of positions, list of gradients
            self.beads.q, fx, self.nebbfgsm.d, self.qlist, self.glist = L_BFGS(self.beads.q,
                  self.nebbfgsm.d, self.nebbfgsm, self.qlist, self.glist,
                  fdf0=(u0, du0), max_step=self.max_step, tol=self.ls_options["tolerance"],
                  itmax=self.ls_options["iter"],
                  m=self.corrections, k=step)

            info(" @GEOP: Updated position list", verbosity.debug)
            info(" @GEOP: Updated gradient list", verbosity.debug)

            # x = current position - previous position. Use to determine converged minimization
            x = np.amax(np.absolute(np.subtract(self.beads.q, self.nebbfgsm.xold)))

            # Store old positions
            self.nebbfgsm.xold[:] = self.beads.q

            info(" @GEOP: Updated bead positions", verbosity.debug)

        # Routine for steepest descent and conjugate gradient
        # TODO: CURRENTLY DOES NOT WORK. MUST BE ELIMINATED OR DEBUGGED
        else:
            if (self.mode == "sd" or step == 0):

                # Steepest descent minimization
                # gradf1 = force at current atom position
                # dq1 = direction of steepest descent
                # dq1_unit = unit vector of dq1
                nebgrad = self.neblm(self.beads.q)[0]
                gradf1 = dq1 = -nebgrad

                # Move direction for steepest descent and 1st conjugate gradient step
                dq1_unit = dq1 / np.sqrt(np.dot(gradf1.flatten(), gradf1.flatten()))
                info(" @GEOP: Determined SD direction", verbosity.debug)

            else:

                # Conjugate gradient, Polak-Ribiere
                # gradf1: force at current atom position
                # gradf0: force at previous atom position
                # dq1 = direction to move
                # dq0 = previous direction
                # dq1_unit = unit vector of dq1
                gradf0 = self.cg_old_f
                dq0 = self.cg_old_d
                nebgrad = self.neblm(self.beads.q)[0]
                gradf1 = -nebgrad
                beta = np.dot((gradf1.flatten() - gradf0.flatten()), gradf1.flatten()) / (np.dot(gradf0.flatten(), gradf0.flatten()))
                dq1 = gradf1 + max(0.0, beta) * dq0
                dq1_unit = dq1 / np.sqrt(np.dot(dq1.flatten(), dq1.flatten()))
                info(" @GEOP: Determined CG direction", verbosity.debug)

            # Store force and direction for next CG step
            self.cg_old_d[:] = dq1
            self.cg_old_f[:] = gradf1

            if len(self.fixatoms) > 0:
                for dqb in dq1_unit:
                    dqb[self.fixatoms*3] = 0.0
                    dqb[self.fixatoms*3+1] = 0.0
                    dqb[self.fixatoms*3+2] = 0.0

            self.neblm.set_dir(depstrip(self.beads.q), dq1_unit)

            # Reuse initial value since we have energy and forces already
            u0 = np.dot(-nebgrad.flatten(), dq1_unit.flatten())
            u0 = np.sqrt(np.dot(u0, u0))

            (x, fx) = min_brent_neb(self.neblm, fdf0=u0, x0=0.0,
                    tol=self.ls_options["tolerance"],
                    itmax=self.ls_options["iter"], init_step=self.ls_options["step"])

            # Automatically adapt the search step for the next iteration.
            # Relaxes better with very small step --> multiply by factor of 0.1 or 0.01
            self.ls_options["step"] = 0.1 * x * self.ls_options["adaptive"] + (1 - self.ls_options["adaptive"]) * self.ls_options["step"]

            self.beads.q += dq1_unit * x
            info(" @GEOP: Updated bead positions", verbosity.debug)

        self.qtime += time.time()

        # Determine conditions for converged relaxation
        if ((fx - u0) / self.beads.natoms <= self.tolerances["energy"])\
            and ((np.amax(np.absolute(self.forces.f)) <= self.tolerances["force"])\
                or (np.sqrt(np.dot(self.forces.f.flatten() - self.cg_old_f.flatten(),\
                    self.forces.f.flatten() - self.cg_old_f.flatten())) == 0.0))\
            and (x <= self.tolerances["position"]):
            softexit.trigger("Geometry optimization converged. Exiting simulation")
