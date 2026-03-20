class atom:
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

    def __init__(self, element: str, x: float, y: float, z: float):
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


    def echo(self):
        """Prints the coordinates of the atom in .xyz format."""
        return f"{self.element} {self.x} {self.y} {self.z}"
    

    def translate_x(self, distance: float):
        """Translates the atom in the x-direction by the given distance
        
        Args:
            distance (float): Distance to move in Angstrom
        """
        self.x += distance


    def translate_y(self, distance: float):
        """Translates the atom in the y-direction by the given distance
        
        Args:
            distance (float): Distance to move in Angstrom
        """
        self.y += distance


    def translate_z(self, distance: float):
        """Translates the atom in the z-direction by the given distance
        
        Args:
            distance (float): Distance to move in Angstrom
        """
        self.z += distance

    
    def add_atom_type(self, atom_type: str):
        """Allows for allocating atom types to an atom for use in a forcefield.
        
        Args:
            atom_type (str): Atom type to be allocated to this atom
        """
        self.atom_type = atom_type

class molecule:
    """molecule class. Contains information about a given molecule

    Attributes:
        charge (int): net charge of the molecule
        spin (int): number of unpaired electrons (2S not 2S + 1)
        atoms (list[atom]): List of atoms and their coordinates
        nat (int): number of atoms in the molecule
    """
    charge: int
    spin: int
    atoms: list[atom]
    nat: int

    def __init__(self, ):
        """Initialises the molecule class. """
        pass

    def from_atoms_list(self, atoms: list[atom], charge: int, spin: int):
        """Initialises a molecule object from an atom list
        
        Args:
            atoms (list[atom]): List of atoms
            charge (int): net charge of the molecule
            spin (int): number of unpaired electrons (2S not 2S+1)
        """
        self.nat = len(atoms)
        self.atoms = atoms
        self.charge = charge
        self.spin = spin

    def from_xyz(self, lines:list[str], charge:int, spin:int):
        """
        Initialises a molecule object from the text within a .xyz file

        Args:
            lines (list): The contents of the .xyz file
            charge (int): net charge of the system
            spin (int): Spin of the system (2S not 2S+1)
        """
        if type(lines) == str:
            lines = lines.split("\n")
        self.nat = int(lines[0])
        atoms = []*self.nat
        for i in range(self.nat):
            items = lines[i+2].split()
            atoms[i] = atom(items[0], float(items[1]), float(items[2]), float(items[3]))
        self.atoms = atoms
        self.charge = charge
        self.spin = spin

    def print_coords(self)->str:
        """Prints the coordinates of a molecule object in a format similar to the .xyz format, however without the top 2 lines containing the NAT or the name."""
        text = ""
        for at in self.atoms:
            text += at.echo()+"\n"
        return text