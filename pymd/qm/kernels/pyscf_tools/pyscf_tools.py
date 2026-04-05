import importlib
import importlib.util

import numpy

from pymd.tools import io
from pymd.tools.structure import Atom, Molecule


# import pyscf.dispersion #TODO add importlib to this. 
from pyscf.hessian import thermo
from pyscf.tools import finite_diff
import pyscf
from pyscf import grad as pygrad, qmmm, dft, scf, cc, lib, gto, df
from pyscf.dft import RKS, UKS
# from pyscf.geomopt.berny_solver import optimize as optimize_berny #TODO implement
# from pyscf.geomopt.geometric_solver import optimize as optimize_geometric
from pyscf.geomopt import as_pyscf_method


if importlib.util.find_spec("gpu4pyscf") is not None:
    try:
        gpu_dft = importlib.import_module("gpu4pyscf.dft")
        gpu_scf = importlib.import_module("gpu4pyscf.scf")
        gpu_cc = importlib.import_module("gpu4pyscf.cc")
    except:
        gpu_dft = None
        gpu_scf = None
        gpu_cc = None
else:
    gpu_dft = None
    gpu_scf = None
    gpu_cc = None

if importlib.util.find_spec("skala") is not None:
    SkalaUKS = importlib.import_module("skala.pyscf.SkalaUKS")
    SkalaUKSGradient = importlib.import_module("skala.pyscf.gradients.SkalaUKSGradient")
    # from skala.pyscf import SkalaUKS
    # from skala.pyscf.gradients import SkalaUKSGradient
else:
    SkalaUKS = None
    SkalaUKSGradient = None

from pprint import pprint
# from pyscf.qsdopt.qsd_optimizer import QSD #TODO add importlib to this. 

def gen_mol(atoms: Molecule|list,
            basis: str = "sto-3g",
            charge: int = 0,
            spin: int = 0,
            memory: int = 15000,
            name: str = "mol.out") -> pyscf.gto.Mole:
    if isinstance(atoms, Molecule): 
        text = ""
        for at in atoms.atoms:
            text += f"{at.element} {at.x} {at.y} {at.z} ;"
        charge = atoms.charge
        spin = atoms.spin
    elif isinstance(atoms, list) and isinstance(atoms[0], Atom):
        text = ""
        for at in atoms:
            text += f"{at.element} {at.x} {at.y} {at.z} ;"
    elif type(atoms) == list and type(atoms[0]) == str:
        text = ""
        for at in atoms:
            text += f"{at} ;"
    elif type(atoms) == str:
        text = atoms
    else:
        raise TypeError("atoms must be of type moleculeClass, list of atom, list of str, or str")
    
    mol = pyscf.gto.Mole(atom=text, unit="Ang")
    mol.output=name
    mol.basis = basis
    mol.charge = charge
    mol.spin = spin
    mol.symmetry = False
    mol.verbose = 4
    mol.cart=False
    mol.max_memory=memory
    mol.build()
    return mol

    
def HF(
    mol: pyscf.gto.Mole, 
    restricted: bool = True,
    GPU: bool = False,
    charges: list = [],
    charge_locs: list = []
    ) -> pyscf.scf.hf.SCF:
    """Runs a Hartree-Fock calculation on a given molecule.

    Args:
        mol (pyscf.gto.Mole): Molecule object from pyscf.
        restricted (bool): Bool dictating whether to run a restricted or unrestricted HF calculation.
        GPU (bool): Whether to run on GPU
        charges (list[float]): QMMM point charge values
        charge_locs (list[tuple]): QMMMM point charge locations
    Returns:
        pyscf.scf.hf.SCF: Mean-field object from pyscf.
    """
    if gpu_scf is None:
        GPU = False
    if restricted:
        if GPU:
            mf = gpu_scf.RHF(mol)
        else:
            mf = scf.rhf.RHF(mol)
    else:
        if GPU:
            mf = gpu_scf.UHF(mol)
        else:
            mf = scf.uhf.UHF(mol)
    mf.max_cycle = 200
    mf.level_shift = 1.2
    if len(charges) > 0:
        assert len(charges) == len(charge_locs), "Different number of charges and charge locations."
        mf = qmmm.mm_charge(mf, charge_locs, charges)
    mf = mf.newton().run()
    grad = mf.nuc_grad_method()
    return mf, grad


def HF_scanner(
        restricted: bool = True,
        GPU: bool = False):

    if gpu_scf is None:
        GPU = False
    if restricted and GPU:
        scanner = gto.M().apply(gpu_scf.RHF).as_scanner()
    elif restricted and GPU == False:
        scanner = gto.M().apply(scf.rhf.RHF).as_scanner()
    elif restricted == False and GPU:
        scanner = gto.M().apply(gpu_scf.UHF).as_scanner()
    elif restricted == False and GPU == False:
        scanner = gto.M().apply(scf.rhf.UHF).as_scanner()
    grad_scanner = scanner.nuc_grad_method().as_scanner()
    return scanner, grad_scanner


def non_scf_DFT(mol: pyscf.gto.Mole, xc:str, disp:None, charges:list=[], charge_locs:list=[], dm0=None):
    mf = dft.UKS(mol, xc)
    if disp is not None:
        mf.disp = disp
    mf.max_cycle = -1
    if len(charges) > 0:
        mf = qmmm.mm_charge(mf, charge_locs, charges)
    dm = mf.get_init_guess()
    mf.kernel(dm0=dm)
    return mf


def DFT(mol:pyscf.gto.Mole,
        xc:str,
        disp=None,
        GPU:bool=False,
        implicit_solvent: bool = False,
        charges: list = [],
        charge_locs:list=[],
        dm0=None,
        no_grad=False):
    
    dispersion = disp
    if gpu_dft is None:
        GPU = False

    if GPU:
        mf = gpu_dft.UKS(mol, xc)
    else:
        mf = UKS(mol, xc)
    # mf.newton()
    # mf.init_guess = "huckel"
    mf.max_cycle = 300
    mf.level_shift = 1.2

    # mf.grids.level = 5
    mf.conv_tol = 1e-6
    mf.conv_tol_grad = 1E-3
    # mf.diis_space = 12
    # mf.conv_check = False
    if dispersion is not None:
        mf.disp = dispersion

    if implicit_solvent:
        mf.PCM()
        mf.with_solvent.method = "C-PCM"
        mf.with_solvent.eps = 80.1510
    elif len(charges) >0:
        mf = qmmm.mm_charge(mf, charge_locs, charges, unit="Ang" )
        # mf.newton()
    if dm0 is not None:

        mf.kernel(dm0=dm0)
    else:
        # mf.kernel()
        mf = mf.newton().run()
    if no_grad == False:
        grad = mf.nuc_grad_method()
    else:
        grad = None
    return mf, grad


def DFT_scanner(
        xc: str,
        disp: str|None = None,
        GPU: bool = False,
        implicit_solvent: bool = False):
    dispersion = disp
    if gpu_dft is None:
        GPU = False
    elif "skala" in xc:
        if SkalaUKS is None:
            raise ModuleNotFoundError("Skala does not exist in this environment.")
        if "d3" in xc:
            disp = True
        else:
            disp = False
        mf_dft = SkalaUKS(pyscf.M(), xc="skala", with_dftd3=disp ).as_scanner()
        mf_dft.conv_tol = 1e-7
        mf_dft.max_cycle = 300
        grad = SkalaUKSGradient(mf_dft).as_scanner()
        if implicit_solvent:
            mf_dft.PCM()
            mf_dft.with_solvent.method = "C-PCM"
            mf_dft.with_solvent.eps = 80.1510

            grad.PCM()
            grad.with_solvent.method = "C-PCM"
            grad.with_solvent.eps = 80.1510
        return mf_dft, grad
    else:
        if "_D3BJ" in xc:
            dispersion = "d3bj"
            xc = xc.replace("_D3BJ","")
        if GPU:
            scanner = gto.M().apply(gpu_dft.UKS).as_scanner()
        else:
            scanner = gto.M().apply(UKS).as_scanner()
        scanner.xc = xc
        scanner.damp
        scanner.max_cycle=300
        scanner.conv_tol = 1e-7    
        if dispersion is not None:
            scanner.disp = dispersion
    if implicit_solvent:
        scanner.PCM()
        scanner.with_solvent.method = "C-PCM"
        scanner.with_solvent.eps = 80.1510
    scanner.level_shift = (1.6,0.2)
    grad_scanner = scanner.nuc_grad_method().as_scanner()
    return scanner, grad_scanner


def CCSD(mol:pyscf.gto.Mole,
        restricted:bool=True,
        implicit_solvent:bool=False,
        direct:bool=False,
        density_fit:bool=False,
        memory:int=20000,
        charges: list = [],
        charge_locs: list = [],
        FrozenCore: bool = True,
        ccsdt: bool = False,
        ccsdtq: bool = False) -> cc.CCSD:
    """Runs a CCSD calculation on a given molecule. Defaults to frozen core CCSD

    """
    if gpu_cc is None:
        GPU = False
    if restricted and GPU == False:
        mf = scf.rhf.RHF(mol)
    elif restricted == False and GPU == False:
        mf = scf.uhf.UHF(mol)
    else:
        raise ValueError("Invalid combination of restricted and GPU flags.")
    
    if len(charges) > 0: 
        mf = qmmm.mm_charge(mf, charge_locs, charges, unit="Ang").run()
    else:
        mf.run()

    # muliken = mf.mulliken_pop(verbose=1)
    if ccsdt == False and ccsdtq == False:
        mycc = cc.CCSD(mf)
    elif ccsdt == True:
        mycc = cc.RCCSDT(mf, compact_tamps=True)
    elif ccsdtq == True:
        mycc = cc.RCCSDTQ(mf, compact_tamps=True)
    if direct:
        mycc.direct = True
    if FrozenCore:
        mycc.set_frozen()
    if density_fit:
        mycc.density_fit()
    mycc.max_memory=memory
    if implicit_solvent:
        mycc.PCM()
        mycc.with_solvent.method = "C-PCM"
        mycc.with_solvent.eps = 80.1510
    
    
    mycc.conv_tol = 1e-8
    mycc.kernel()
    grad = mycc.nuc_grad_method()   
    return mycc, grad, mf


def CCSD_scanner(restricted:bool=True,
                GPU:bool=False,
                implicit_solvent:bool=False,
                direct:bool=False,
                fast:bool=False,
                memory:int=15000):
    if gpu_cc is None:
        GPU = False
    if restricted and GPU == False:
        scanner = gto.M().apply(scf.rhf.RHF).apply(cc.CCSD).as_scanner()
    elif restricted == False and GPU == False:
        scanner = gto.M().apply(scf.rhf.UHF).apply(cc.CCSD).as_scanner()
    elif restricted and GPU:
        scanner = gto.M().apply(gpu_scf.UHF).apply(gpu_cc.ccsd_incore.CCSD).as_scanner()
    elif restricted == False and GPU:
        scanner = gto.M().apply(gpu_scf.RHF).apply(gpu_cc.ccsd_incore.CCSD).as_scanner()
    else:
        raise ValueError("Invalid combination of restricted and GPU flags.")
    if direct:
        scanner.direct = True
    if fast:
        scanner.set_frozen()
        scanner.density_fit()
    scanner.max_memory=memory
    if implicit_solvent:
        scanner.PCM()
        scanner.with_solvent.method = "C-PCM"
        scanner.with_solvent.eps = 80.1510
    grad = scanner.nuc_grad_method().as_scanner()
    return scanner, grad

def FCI(mol:pyscf.gto.Mole):
    mf = pyscf.scf.UHF(mol)
    mf.kernel()
    cisolver = pyscf.fci.FCI(mf)
    Energy, fcivec = cisolver.kernel()
    return Energy


def get_freq(
        mf,
        mol=None,
        method: str|None = None,
        grad_scanner = None)->list:
    """
    Returns the imaginary frequencies of a molecule.
    
    Args:
        mf: A pySCF mean-field object.
        mol: A pySCF molecule object.
        method: The method to use for frequency calculation.
        grad_scanner: A scanner object for gradient calculation.
    """
    if method != "CCSD" and "QEDFT" not in method and "skala" not in method:
        imag = []
        hess = mf.Hessian().kernel()
        freq = thermo.harmonic_analysis(mol, hess, imaginary_freq=False,)
        for f in freq["freq_wavenumber"]:
            if f < 0 : 
                imag.append(f)
        return imag
    elif "skala" in method:
        imag = []
        assert grad_scanner is not None
        # grad = grad_scanner(mol)
        hess = finite_diff.Hessian(grad_scanner).kernel()
        freq = thermo.harmonic_analysis(mol, hess, imaginary_freq=False,)
        for f in freq["freq_wavenumber"]:
            if f < 0 : 
                imag.append(f)
        return imag
   
    else:
        imag = []
        grad = mf.nuc_grad_method()
        hess = finite_diff.Hessian(grad).kernel()
        freq = thermo.harmonic_analysis(mol, hess, imaginary_freq=False,)
        for f in freq["freq_wavenumber"]:
            if f < 0 : 
                imag.append(f)
        return imag
   

def optimize_mol(mf:as_pyscf_method, method: Optional[str] = "Berny", maxsteps: Optional[int] = 100, TS: bool = False)->pyscf.gto.Mole:
    """Optimizes the geometry of a molecule using the specified optimization method.

    Args:
        mf (cc.CCSD): Mean-field object from pyscf.
        method (str, optional): Optimization method to use. Defaults to "Berny".
        maxsteps (int, optional): Maximum number of optimization steps. Defaults to 50.
        TS (bool): Whether to do a TS search
    Returns:
        pyscf.gto.Mole: Optimized molecule object.
    """
    if TS:
        try:
            if method == "QSD":
                optimizer = QSD(mf, stationary_point="TS")
                optimizer.kernel(step=0.05, numhess_method="forward", max_iter=maxsteps)
                # optimizer.kernel()
                return optimizer.mol
            elif method == "Geometric":
                params = {'transition': True, 'trust': 0.01, 'tmax': 0.03,}
                print(type(mf))
                mol_eq = mf.optimizer(solver="geomeTRIC", max_iter=300).kernel(params)
                # mol_eq = optimize_geometric(mf, maxsteps=500).kernel(params)

                # except:
                    # mol_eq = mf.Gradients().optimizer(solver="geomeTRIC").kernel(params)
                    
                    # mol_eq = optimize_geometric(mf, maxsteps=maxsteps).kernel(params)
                # mol_eq = optimize_geometric(mf, maxsteps=maxsteps).kernel(params)
                return mol_eq
            else:
                raise NotImplementedError(f"Optimization method {method} not implemented. for TS search")
        except RuntimeError:
            return None
    else:
        try:
            if method == "Berny":
                mol_eq = optimize_berny(mf, maxsteps=maxsteps, assert_convergence=False).kernel({  # These are the default settings
            'gradientmax': 0.45e-3,  # Eh/[Bohr|rad]
            'gradientrms': 0.15e-3,  # Eh/[Bohr|rad]
            'stepmax': 3e-3,       # [Bohr|rad]
            'steprms': 1.2e-3,       # [Bohr|rad]
        })
            elif method == "Geometric":
                mol_eq = optimize_geometric(mf, maxsteps=maxsteps).kernel()
                # mol_eq = mf.optimizer(solver="geomeTRIC").kernel()
            else:
                raise NotImplementedError(f"Optimization method {method} not implemented for standard optimisation.")
            return mol_eq
        except RuntimeError:
            return None
    

def mol_to_xyz(mol:pyscf.gto.Mole, unit:str="Ang"):
    """Converts a pyscf molecule object to an XYZ format string.

    Args:
        mol (pyscf.gto.Mole): Molecule to convert.
        unit (str, optional): Unit for the positions. Defaults to "Ang".

    Returns:
        str: Text in XYZ format.
    """
    elements = [at[0] for at in mol._atom]
    positions = mol.atom_coords(unit=unit)
    text = f"{len(elements)}\n"
    for i, el in enumerate(elements):
        pos = positions[i]
        text += f"\n{el} {round(pos[0],8):.8f} {round(pos[1],8):.8f} {round(pos[2],8):.8f}"
    return text

def grad_hcore_mm(qmmm, qm_mol, dm):# Credit to pySCF. This is pulled from v.2.8.0 © Copyright 2025, The PySCF Developers. Pulled purely for compatibility between DM21 and qmmm
    mol = qm_mol
    mm_mol = qmmm.mm_mol

    coords = mm_mol.atom_coords()
    charges = mm_mol.atom_charges()

    intor = 'int3c2e_ip2'
    nao = mol.nao
    max_memory = qmmm.max_memory - lib.current_memory()[0]
    blksize = int(min(max_memory*1e6/8/nao**2/3, 200))
    blksize = max(blksize, 1)
    cintopt = gto.moleintor.make_cintopt(mol._atm, mol._bas,
                                            mol._env, intor)
    g = numpy.empty_like(coords)
    for i0, i1 in lib.prange(0, charges.size, blksize):
        fakemol = gto.fakemol_for_charges(coords[i0:i1])
        j3c = df.incore.aux_e2(mol, fakemol, intor, aosym='s1',
                                comp=3, cintopt=cintopt)
        g[i0:i1] = numpy.einsum('ipqk,qp->ik', j3c * charges[i0:i1], dm).T
    return g

def grad_nuc_mm(qmmm, mol,dm): # Credit to pySCF. This is pulled from v.2.8.0 © Copyright 2025, The PySCF Developers. Pulled purely for compatibility between DM21 and qmmm
        '''Nuclear gradients of the QM-MM nuclear energy
        (in the form of point charge Coulomb interactions)
        with respect to MM atoms.
        '''
        mm_mol = qmmm.mm_mol
        coords = mm_mol.atom_coords()
        charges = mm_mol.atom_charges()
        # g_mm = numpy.zeros_like(coords)
        g_mm = grad_hcore_mm(qmmm, mol, dm)
        for i in range(mol.natm):
            # q1 = qm_charges[i]
            q1 = mol.atom_charge(i)
            r1 = mol.atom_coord(i)
            r = lib.norm(coords -r1, axis=1)
            g_mm -= q1 * numpy.einsum('i,ix,i->ix', charges, coords-r1, 1/r**3)
        return g_mm