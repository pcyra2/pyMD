"""#TODO
"""
class Atom:
    """Class containing atom information
    
    Attributes:
        element (str): element symbol from the periodic table
        x (float): X-coordinate of the atom in Angstrom
        y (float): Y-coordinate of the atom in Angstrom
        Z (float): Z-coordinate of the atom in Angstrom
        atom_type (str): Atom type for the respective forcefield
    """
    element: str
    x: float
    y: float
    z: float
    atom_type: str

    def __init__(self, element: str, x: float, y: float, z: float) -> None:
        """Initialises the atom object
        
        Args:
            element (str): element key
            x (float): X coordinate of the atom in Angstrom
            y (float): Y coordinate of the atom in Angstrom
            z (float): Z coordinate of the atom in Angstrom
        """
        self.element = element
        self.x = x
        self.y = y
        self.z = z


    def echo(self) -> str:
        """Prints the coordinates of the atom in .xyz format."""
        return f"{self.element} {self.x} {self.y} {self.z}"


    def translate_x(self, distance: float) -> None:
        """Translates the atom in the x-direction by the given distance
        
        Args:
            distance (float): Distance to move in Angstrom
        """
        self.x += distance


    def translate_y(self, distance: float) -> None:
        """Translates the atom in the y-direction by the given distance
        
        Args:
            distance (float): Distance to move in Angstrom
        """
        self.y += distance


    def translate_z(self, distance: float) -> None:
        """Translates the atom in the z-direction by the given distance
        
        Args:
            distance (float): Distance to move in Angstrom
        """
        self.z += distance


    def add_atom_type(self, atom_type: str) -> None:
        """Allows for allocating atom types to an atom for use in a forcefield.
        
        Args:
            atom_type (str): Atom type to be allocated to this atom
        """
        self.atom_type = atom_type

class Bond:
    atom1: int
    atom2: int
    length: float

    def __init__(self, at1: int, at2: int) -> None:
        self.atom1 = at1
        self.atom2 = at2

    def set_length(self, length: float) -> None:
        self.length = length

class Molecule:
    """molecule class. Contains information about a given molecule

    Attributes:
        charge (int): net charge of the molecule
        spin (int): number of unpaired electrons (2S not 2S + 1)
        atoms (list[Atom]): List of atoms and their coordinates
        bonds (list[Bond]): List of Bonds
        nat (int): number of atoms in the molecule
    """
    charge: int
    spin: int
    atoms: list[Atom]
    bonds: list[Bond]
    nat: int

    def __init__(self, ) -> None:
        """Initialises the molecule class. """

    def from_atoms_list(self, atoms: list[Atom], charge: int, spin: int) -> None:
        """Initialises a molecule object from an atom list
        
        Args:
            atoms (list[Atom]): List of atoms
            charge (int): net charge of the molecule
            spin (int): number of unpaired electrons (2S not 2S+1)
        """
        self.nat = len(atoms)
        self.atoms = atoms
        self.charge = charge
        self.spin = spin


    def from_xyz(self, lines: list[str]|str, charge: int, spin: int) -> None:
        """
        Initialises a molecule object from the text within a .xyz file

        Args:
            lines (list): The contents of the .xyz file
            charge (int): net charge of the system
            spin (int): Spin of the system (2S not 2S+1)
        """
        if isinstance(lines, str):
            lines = lines.split(sep="\n")
        self.nat = int(lines[0])
        atoms = [Atom]*self.nat
        for i in range(self.nat):
            items = lines[i+2].split()
            atoms[i] = Atom(element=items[0], x=float(items[1]), y=float(items[2]), z=float(items[3]))
        self.atoms = atoms
        self.charge = charge
        self.spin = spin


    def from_mol2(self, lines: list[str], charge: int, spin: int):
        tmp = lines[2].split()
        self.nat = int(tmp[0])
        nbonds = int(tmp[1])
        atoms = [] * self.nat
        bonds = [] * nbonds
        ATOM_LINES = False
        BOND_LINES = False
        for line in lines:
            if line.startswith("@<TRIPOS>ATOM"):
                assert BOND_LINES is False
                i = -1
                ATOM_LINES=True
                continue
            if line.startswith("@<TRIPOS>BOND"):
                assert ATOM_LINES is False
                i = -1
                BOND_LINES=True
            if ATOM_LINES is True:
                i += 1
                tmp = line.split()
                atoms[i] = Atom(element=tmp[1].replace(tmp[0],""), x=tmp[2], y=tmp[3], z=tmp[4])
                if i == self.nat:
                    ATOM_LINES = False
            if BOND_LINES is True:
                i += 1
                tmp = line.split()
                bonds[i] = Bond(at1=int(tmp[0]), at2=int(tmp[1]))
                if i == nbonds:
                    BOND_LINES = False
        self.atoms = atoms
        self.bonds = bonds


    def print_coords(self) -> str:
        """Prints the coordinates of a molecule object in a format similar to the .xyz format, 
        however without the top 2 lines containing the NAT or the name.
        """
        text = ""
        for at in self.atoms:
            text += at.echo()+"\n"
        return text
