from pymd.tools.structure import Atom, Molecule

CALCULATION_TYPES = ["SP", "Opt", "OptTS", "Freq"]

class OrcaConfig:
    method: str = "PBE"
    basis: str = "def2-SVP"
    dispersion: str = "D3BJ"
    grid: str = "DEFGRID3"
    print_level: str = "MINIPRINT"
    scf_level: str = "TightSCF"
    rij: str = "RIJCOSX"
    convergence_level: str = "EasyConv"
    implicit_solvent: str
    _cores:int = 12
    _mem_per_cpu: int = 1000
    _charge: int = 0
    _spin: int = 1
    _molecule: Molecule
    _scan_atoms: list[int]
    _scan_start: float
    _scan_stop: float
    _scan_steps: int

    ##### Do not edit beyond this point #####
    _structure_line: str


    def __init__(self) -> None:
        pass

    def to_dict(self)->dict:
        """Returns a dictionary of the class attributes"""
        return {key:value for key, value in vars(self).items() if not key.startswith('_')}


    def add_input_structure(self, 
            structure:str|list[str]|list[Atom]|Molecule,
            structure_type: str = "xyzfile") -> None:
        STRUCTURE_TYPES = ["xyzfile", "xyz"]

        assert structure_type in STRUCTURE_TYPES
        
        if structure_type == "xyzfile":
            self._structure_line = f"* xyzfile {self._charge} {self._spin} {structure}"
        elif structure_type == "raw":
            line = f"* xyz {structure.charge} {structure.spin + 1}\n"
            
            if isinstance(structure, Molecule):
                self._molecule = Molecule
                line += structure.print_coords()
            
            elif isinstance(structure, list[Atom]):
                self._molecule = Molecule().from_atoms_list(atoms=structure,
                                                            charge=self._charge,
                                                            spin=self._spin-1)
                line += self._molecule.print_coords()
            
            elif isinstance(structure, list[str]):
                atoms = [Atom]*len(structure)
                for i, l in enumerate(structure):
                    inf = l.split()
                    atoms[i] = Atom(element=inf[0], x=inf[1], y=inf[2], z=inf[3])
                self._molecule = Molecule().from_atoms_list(atoms=atoms, 
                                                            charge=self._charge,
                                                            spin=self._spin)
                line += self._molecule.print_coords()
            
            elif isinstance(structure, str):
                line += structure
            
            else:
                raise NotImplementedError(f"ERROR: Structure type {type(structure)} not implemented for this function")
            
            line += "\n*"
            self._structure_line = line


    def gen_input_file(self) -> list[str]:
        """#TODO

        Returns:
            list[str]: _description_
        """
        contents = self.to_dict()
        
        input_file = []
        top_line = f"! {contents.pop("method")} {contents.pop("method")} {contents.pop("method")}"
        remainder = list(contents.keys())
        for key in remainder:
            top_line += f" {contents[key]}"
        input_file.append(top_line)    
        input_file.append(f"%PAL NPROCS {self._cores} END")
        input_file.append(f"%maxcore {self._mem_per_cpu}")
        input_file.append(self._structure_line)

        return input_file


