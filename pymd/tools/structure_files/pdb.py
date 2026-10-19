from pymd.tools.structure import Atom
from pymd.tools.io import TERM_SIZE

import datetime


class PDB:
    atoms: list[Atom]
    nat: int
    def __init__(self) -> None:
        pass

    def from_file(self, file: str) -> None:
        with open(file, "r") as f:
            lines = f.readlines()
        
        for line in reversed(lines):
            if line.startswith("ATOM") or line.startswith("HETATM"):
                self.nat = int(line[6:11])

                break
        tmp = [None]*(self.nat-1)
        index = 0
        print("".center(TERM_SIZE, "-"))
        print("Starting the parse of the PDB file".center(TERM_SIZE))
        print("".center(TERM_SIZE, "-"))
        print(f"Number of atoms: {self.nat}".center(TERM_SIZE))
        res_chain: dict = dict()
        for line in lines:
            if line.startswith("ATOM") or line.startswith("HETATM"):
                if line.startswith("HETATM"):
                    prefix = "HETATM"
                else:
                    prefix = "ATOM"
                
                elem = line[76:78].strip()
                x = float(line[30:38].strip())
                y = float(line[38:46].strip())
                z = float(line[46:54].strip())
                at = Atom(elem, x, y, z)
                at.change_prefix(prefix)
                at.add_index(int(line[6:11]))
                resn = line[17:20].strip()
                resi = int(line[22:26].strip())
                chain = line[21]
                at.add_atom_type(line[12:16].strip())
                if chain not in res_chain:
                    res_chain[chain] = dict()
                if resi not in res_chain[chain]:
                    res_chain[chain][resi] = resn
                if chain == " ":
                    chain = None
                at.add_residue_information(resname=resn, resid=resi, chain=chain)
                
                # at._print_pdb()
                tmp[index] = at
                index += 1
        total = 0
        for chain in res_chain.keys():
            total += len(res_chain[chain].keys())
        print(f"Total number of residues: {total}".center(TERM_SIZE))
        print(f"Chains in file: {list(res_chain.keys())}".center(TERM_SIZE))
        print("".center(TERM_SIZE, "-"))
        print("PDB file parsed".center(TERM_SIZE))
        print("".center(TERM_SIZE, "-"))
        self.atoms = tmp


    def update_coordinates(self, coordinates: list[Atom]) -> None:
        # assert len(coordinates) == self.nat # Check to make sure the coordinates are the same.
        for i, at in enumerate(coordinates):
            assert at.element == self.atoms[i].element # quick check to make sure you are updating the same atom
            self.atoms[i].update_coordinates(x=at.x, y=at.y, z=at.z)


    def to_file(self, file: str) -> None:
        with open(file, "w") as f:
            print("TITLE   {0:2} {1:79}".format(" ", # Continuation
                f"PDB file created by Ross Amory on {datetime.datetime.now().strftime('%x at %X')}",),
                file=f)
            print("REMARK {0:3} {1:68}".format("1".ljust(3),
                                                f"PDB file generated according to PDB v3.3"), file=f)
            print("REMARK {0:3} {1:68}".format("2".ljust(3),
                                                f"PDB file generated using a script made by Dr. Ross Amory"),
                                                file=f)
            print("REMARK {0:3} {1:68}".format("3".ljust(3),
                                                f"This script is in its BETA stage and so should be used with caution."),
                                                file=f)
            for at in self.atoms:
                print(at._pdb_lines(), file=f)
