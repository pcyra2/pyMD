import dis

import pyscf
import pyscf.dft

from pymd.qm.qm import Molecule

class PySCFConfig:
    grid: int = 5
    level_shift: float = 1.2
    dispersion: str|None = None
    method: str = "PBE"
    basis: str = "def2-SVP"
    verbosity: int = 4
    max_memory: int = 1000
    symmetry: bool = False
    restricted: bool = False
    conv_tol: float = 1e-6
    scf_solver: str = "newton"
    max_cycles: int = 300
    gpu: bool = False
    output_file: str = "pyscf.out"
    charge: int = 0
    spin: int = 0

    ## Do not edit beyond this point. 
    mol: pyscf.gto.Mole|None
    charges: list[float]|None = None
    charge_locs: list[tuple[float,float,float]]|None = None
    hf: bool = False
    dft: bool = False
    ccsd: bool = False
    mp2: bool = False
    fci: bool = False
    _mf_kernel: pyscf.dft.rks.RKS|pyscf.dft.uks.UKS|pyscf.scf.rhf.RHF|pyscf.scf.uhf.UHF|None = None
    
    def __init__(self, method: str,
            basis: str,
            dispersion: str|None,
            job_name: str
            ) -> None:
        self.set_method(method)
        self.set_basis(basis=basis)
        if dispersion is not None:
            self.add_dispersion(dispersion=dispersion)
        self.output_file = job_name

    def set_verbosity(self, verbosity: int) -> None:
        self.verbosity = verbosity

    def build_molecule(self, molecule: Molecule) -> None:
        text = ""
        for at in molecule.atoms:
            text += f"{at.element} {at.x} {at.y} {at.z} ;"

        self.mol = pyscf.gto.Mole(atom = text, unit = "Ang")
        self.mol.charge = molecule.charge
        self.mol.spin = molecule.spin
        self.mol.basis = self.basis
        self.mol.verbose = self.verbosity
        self.mol.symmetry = self.symmetry
        self.mol.max_memory = self.max_memory
        self.mol.build()

        self.charge = molecule.charge
        self.spin = molecule.spin

    def use_symm(self) -> None:
        self.symmetry = True

    def set_method(self, method: str) -> None:
        self.method = method
        if "hf" in method.casefold():
            self.hf = True
            if method.casefold() == "uhf":
                self.restricted = False

        elif "ccsd" in method.casefold():
            self.hf = True
            self.ccsd = True
            
        elif "mp2" in method.casefold():
            self.hf = True
            self.mp2 = True
        elif "fci" in method.casefold():
            self.hf = True
            self.fci = True
        else:
            self.dft = True
            if "uks" in method.casefold():
                self.restricted = True
                self.method = method.casefold().replace("uks","")

    def set_basis(self, basis: str) -> None:
        self.basis = basis
        if self.mol is not None:
            self.mol.basis = basis
            self.mol.build()

    def hf_kernel(self,
            scanner: bool = False) -> None:

        if scanner is False:
            assert self.mol is not None
            mol = self.mol
        else:
            mol = pyscf.M()
        if self.restricted:
            mf = pyscf.scf.rhf.RHF(mol=mol)
        else:
            mf = pyscf.scf.uhf.UHF(mol=mol)
        mf.level_shift = self.level_shift
        mf.max_cycle = self.max_cycles
        mf.conv_tol = self.conv_tol
        if scanner:
            mf.as_scanner()
        self._mf_kernel = mf

    def dft_kernel(self,
            scanner: bool = False) -> None:
        pass

    def add_dispersion(self, dispersion: str) -> None:
        self.dispersion = dispersion
    
    def to_gpu(self) -> None:
        if self.dft:
            self.gpu = True
        else:
            print("WARNING: Do not use pySCF4GPU for non-DFT calculataions.")

    def add_charges(self, charges: list[float], charge_locs: list[tuple[float,float,float]]) -> None:
        """Adds charges to the molecule to run a QM/MM calculation"""
        self.charges = charges
        self.charge_locs = charge_locs


    def build(self, molecule: Molecule):
        self.build_molecule(molecule=molecule)

        if self.hf:
            self.hf_kernel()
        else:
            self.dft_kernel()
        
