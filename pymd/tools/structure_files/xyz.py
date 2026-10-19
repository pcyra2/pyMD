
from pymd.tools.structure import Atom
from pymd.tools.io import TERM_SIZE

from tqdm import tqdm

class XYZ:
    nat: int
    atoms: list[Atom]
    charge: float
    spin: int
    trajectory: list[list[Atom]]
    energies: list
    traj_length: int = 0

    def __init__(self) -> None:
        pass


    def from_file(self, file: str) -> None:
        with open(file, "r") as f:
            lines = f.readlines()

        print("".center(TERM_SIZE, "-"))
        print("Starting the parse of the XYZ file".center(TERM_SIZE))
        print("".center(TERM_SIZE, "-"))
        

        self.nat = int(lines[0])
        print(f"Number of atoms: {self.nat}".center(TERM_SIZE))
        atoms = [None]*self.nat
        for i, line in enumerate(lines[2:self.nat+2]):
            words = line.split()
            atoms[i] = Atom(str(words[0]), float(words[1]), float(words[2]), float(words[3]))

        self.atoms = atoms
        print("".center(TERM_SIZE, "-"))
        print("XYZ file parsed".center(TERM_SIZE))
        print("".center(TERM_SIZE, "-"))

    def from_atoms(self, atoms: list[Atom]) -> None:
        self.atoms = atoms


    def _get_charge(self) -> None:
        chg = 0
        for atom in self.atoms:
            chg += atom.charge
        self.charge = chg


    def from_trajectory(self, file: str, energies: bool = True) -> None:
        with open(file, "r") as f:
            lines = f.readlines()
        nat = int(lines[0])
        n_structures = 0
        index = -1000
        trajectories = []
        print("".center(TERM_SIZE, "-"))
        print("Starting the parse of the XYZ trajectory file".center(TERM_SIZE))
        print("".center(TERM_SIZE, "-"))
        print(f"Number of atoms: {nat}".center(TERM_SIZE))
        mol = [None] * nat
        if energies:
            en = []
        for line in tqdm(lines, "Reading file: "):
            
            if line.strip() == str(nat) and index < 0: # The gap between .xyz structures. 
                # Allows for structure delimiters rather than .xyz structures in rapid succsesison.
                index = -2 # Assuming nat definition is 2 lines before the start of the structure. 
            if index == -1 and energies == True:
                en.append(line)
            if index >= 0: # Where the atoms start
                words = line.split()
                # print(words, index)
                mol[index] = Atom(str(words[0]), float(words[1]), float(words[2]), float(words[3]))
            if index == nat-1:
                trajectories.append(mol) # Update the trajectory
                n_structures += 1
                index = -1000 # Reset the index counter
                # print(n_structures)
                # print(mol[0].echo())
                # print(mol[-1].echo())
                mol = [None] * nat

            index += 1 # Add to the index. 

        if energies:
            self.energies = en
        self.atoms = mol
        self.trajectory = trajectories
        self.traj_length = n_structures
        print(f"Number of structures in the trajectory: {n_structures}".center(TERM_SIZE))
        print("".center(TERM_SIZE, "-"))
        print("XYZ trajectory file parsed".center(TERM_SIZE))
        print("".center(TERM_SIZE, "-"))