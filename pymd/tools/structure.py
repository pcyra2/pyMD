"""#TODO
"""
import numpy

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


class Angle:
    atom1: int
    atom2: int
    atom3: int
    angle: float

    def __init__(self, index1:int, index2:int, index3:int) -> None:
        self.atom1=index1
        self.atom2=index2
        self.atom3=index3

    def set_angle(self, value:float) -> None:
        self.angle = value


class Molecule:
    """molecule class. Contains information about a given molecule

    Attributes:
        charge (int): net charge of the molecule
        spin (int): number of unpaired electrons (2S not 2S + 1)
        atoms (list[Atom]): List of atoms and their coordinates
        bonds (list[Bond]): List of Bonds
        angles (list[Angle]): List of Angles
        nat (int): number of atoms in the molecule
    """
    charge: int
    spin: int
    atoms: list[Atom]
    bonds: list[Bond]
    angles: list[Angle]
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


    def from_mol2(self, lines: list[str], charge: int, spin: int) -> None:
        tmp = lines[2].split()
        self.nat = int(tmp[0])
        nbonds = int(tmp[1])
        atoms = [] * self.nat
        bonds = [] * nbonds
        ATOM_LINES = False
        BOND_LINES = False
        i: int = 0
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
                atoms[i] = Atom(element=tmp[1].replace(tmp[0],""),
                                x=float(tmp[2]),
                                y=float(tmp[3]),
                                z=float(tmp[4]))
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
        self.charge = charge
        self.spin = spin
        for bond in self.bonds:
            bond.set_length(length=calc_distance(a=self.atoms[bond.atom1], b=self.atoms[bond.atom2]))
        self.find_angles()


    def find_angles(self) -> None:
        """Detects all unique bond angles from the list of bonds.
        
        A bond angle is formed by three atoms where two bonds share a common central atom.
        For each pair of bonds that share an atom, an Angle object is created with the
        shared atom as the central atom.
        """
        angles = []
        seen_angles = set()  # Track angles to avoid duplicates (as tuples of sorted atom indices)
        
        # Iterate through all pairs of bonds
        for i, bond_i in enumerate(iterable=self.bonds):
            for _, bond_j in enumerate(iterable=self.bonds, start=i+1):


                
                # Check all possible combinations where the two bonds share an atom
                # Case 1: bond_i.atom1 == bond_j.atom1 (both bonds start at same atom)
                if bond_i.atom1 == bond_j.atom1:
                    central_atom = bond_i.atom1
                    atom1 = bond_i.atom2
                    atom3 = bond_j.atom2
                    angle_key = tuple(sorted([atom1, central_atom, atom3]))
                    
                    if angle_key not in seen_angles:
                        angle_obj = Angle(index1=atom1, index2=central_atom, index3=atom3)
                        angle_obj.set_angle(value=calc_angle(a=self.atoms[atom1],
                                                    b=self.atoms[central_atom],
                                                    c=self.atoms[atom3]))
                        angles.append(angle_obj)
                        seen_angles.add(angle_key)
                
                # Case 2: bond_i.atom1 == bond_j.atom2 (first atom of bond_i matches second atom of bond_j)
                if bond_i.atom1 == bond_j.atom2:
                    central_atom = bond_i.atom1
                    atom1 = bond_i.atom2
                    atom3 = bond_j.atom1
                    angle_key = tuple(sorted([atom1, central_atom, atom3]))

                    if angle_key not in seen_angles:
                        angle_obj = Angle(index1=atom1, index2=central_atom, index3=atom3)
                        angle_obj.set_angle(value=calc_angle(a=self.atoms[atom1],
                                                    b=self.atoms[central_atom],
                                                    c=self.atoms[atom3]))
                        angles.append(angle_obj)
                        seen_angles.add(angle_key)

                # Case 3: bond_i.atom2 == bond_j.atom1 (second atom of bond_i matches first atom of bond_j)
                if bond_i.atom2 == bond_j.atom1:
                    central_atom = bond_i.atom2
                    atom1 = bond_i.atom1
                    atom3 = bond_j.atom2
                    angle_key = tuple(sorted([atom1, central_atom, atom3]))

                    if angle_key not in seen_angles:
                        angle_obj = Angle(index1=atom1, index2=central_atom, index3=atom3)
                        angle_obj.set_angle(value=calc_angle(a=self.atoms[atom1],
                                                    b=self.atoms[central_atom],
                                                    c=self.atoms[atom3]))
                        angles.append(angle_obj)
                        seen_angles.add(angle_key)

                # Case 4: bond_i.atom2 == bond_j.atom2 (both bonds end at same atom)
                if bond_i.atom2 == bond_j.atom2:
                    central_atom = bond_i.atom2
                    atom1 = bond_i.atom1
                    atom3 = bond_j.atom1
                    angle_key = tuple(sorted([atom1, central_atom, atom3]))

                    if angle_key not in seen_angles:
                        angle_obj = Angle(index1=atom1, index2=central_atom, index3=atom3)
                        angle_obj.set_angle(value=calc_angle(a=self.atoms[atom1],
                                                    b=self.atoms[central_atom],
                                                    c=self.atoms[atom3]))
                        angles.append(angle_obj)
                        seen_angles.add(angle_key)

        self.angles = angles




    def print_coords(self) -> str:
        """Prints the coordinates of a molecule object in a format similar to the .xyz format, 
        however without the top 2 lines containing the NAT or the name.
        """
        text = ""
        for at in self.atoms:
            text += at.echo()+"\n"
        return text


def calc_distance(a: Atom|tuple[float,float,float],
             b: Atom|tuple[float,float,float]) -> float:
    """
    Calculate Euclidean distance between two points.

    Args:
        a (Atom|tuple[float,float,float]): Atom/point 1 in the distance
        b (Atom|tuple[float,float,float]): Atom/point 2 in the distance

    Returns:
        float: The distance between two points
    """
    # support atom objects
    if isinstance(a, Atom):
        ax, ay, az = float(a.x), float(a.y), float(a.z)
    else:
        ax, ay, az = map(float, a)
    if isinstance(b, Atom):
        bx, by, bz = float(b.x), float(b.y), float(b.z)
    else:
        bx, by, bz = map(float, b)

    dx = ax - bx
    dy = ay - by
    dz = az - bz
    return (dx*dx + dy*dy + dz*dz) ** 0.5


def calc_angle(a: Atom|tuple[float,float,float],
               b: Atom|tuple[float,float,float],
               c: Atom|tuple[float,float,float]) -> float:
    """Calculates the angle between three atoms.

    Args:
        a (Atom|tuple[float,float,float]): Atom 1 in the bond angle.
        b (Atom|tuple[float,float,float]): Atom 2 in the bond angle.
        c (Atom|tuple[float,float,float]): Atom 3 in the bond angle.

    Returns:
        float: Angle between the three atoms in degrees.
    """
    # support atom objects
    if isinstance(a, Atom):
        ax, ay, az = float(a.x), float(a.y), float(a.z)
    else:
        ax, ay, az = map(float, a)
    if isinstance(b, Atom):
        bx, by, bz = float(b.x), float(b.y), float(b.z)
    else:
        bx, by, bz = map(float, b)
    if isinstance(c, Atom):
        cx, cy, cz = float(c.x), float(c.y), float(c.z)
    else:
        cx, cy, cz = map(float, c)

    v1 = numpy.array([ax-bx, ay-by, az-bz])
    v2 = numpy.array([cx-bx, cy-by, cz-bz])

    CosAng = numpy.dot(v1,v2) / (numpy.linalg.norm(v1) * numpy.linalg.norm(v2))
    Ang = numpy.arccos(CosAng)
    return numpy.degrees(Ang)
