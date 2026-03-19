class atom:
    element: str
    x: float
    y: float
    z: float

    def __init__(self, element: str, x: float, y: float, z: float):
        self.element = element
        self.x = x
        self.y = y
        self.z = z

    def echo(self):
        return f"{self.element} {self.x} {self.y} {self.z}"
    
    def translate_x(self, distance: float):
        self.x += distance

    def translate_y(self, distance: float):
        self.y += distance

    def translate_z(self, distance: float):
        self.z += distance

class molecule:
    charge: int
    spin: int
    atoms: list[atom]
    nat: int

    def __init__(self, ):
        pass

    def from_atoms_list(self, atoms: list[atom], charge: int, spin: int):
        self.nat = len(atoms)
        self.atoms = atoms
        self.charge = charge
        self.spin = spin

    def from_xyz(self, lines:list[str], charge:int, spin:int):
        """
        Initialises a molecule object from the text within a .xyz file

        Args:
            lines (list): _description_
            charge (int): _description_
            spin (int): _description_
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
        text = ""
        for at in self.atoms:
            text += at.echo()+"\n"
        return text