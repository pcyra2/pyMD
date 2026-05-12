"""#TODO
"""

KNOWN_RESIDUES = [
                "ACE", "ALA", "ARG", "ASH", "ASN", "ASP", "CYM", "CYS",
                "CYX", "GLH", "GLN", "GLU", "GLY", "HIE", "HIP", "HIS",
                "HYP", "ILE", "LEU", "LYN", "LYS", "MET", "NME", "PHE", 
                "PRO", "SER", "THR", "TRP", "TYR", "VAL", "HID"
                ]


def mutate_residue(
        lines: list[str],
        residue_number: int,
        new_residue: str,
        chain: str = "A"
        ) -> list[str]:
    """Mutates the residue in a PDB file by replacing the original resname with the mutant resname. 

    Args:
        lines (list[str]): The lines of a PDB file.
        residue_number (int): the resid of the residue to mutate.
        new_residue (str): the 3 letter resname. It must be a residue from KNOWN_RESIDUES.
        chain (str, optional): The chain to mutate. useful if there are multiple proteins 
            in the PDB file. Defaults to A.
    """

    assert new_residue in KNOWN_RESIDUES

    for i, line in enumerate(iterable=lines):
        if line.startswith('ATOM') or line.startswith('HETATM'):
            current_residue_number = int(line[22:26].strip())
            residue_name = line[17:20].strip()
            atom_name = line[12:16].strip()
            current_chain = line[21:22].strip()
            if current_residue_number == residue_number and current_chain == chain:
                if residue_name == new_residue:
                    raise ValueError(f"The residue at position {residue_number} " + \
                                     "is already {new_residue}. No mutation performed.")

                new_line = line[:17] + new_residue.ljust(3) + line[20:]

                if atom_name in ['N', 'CA', 'C', 'O']:
                    lines[i] = new_line
                else:
                    lines[i] = "DELETE_ME"

    mutated_lines = [line for line in lines if line != "DELETE_ME"]

    return mutated_lines


def get_protein_res_id_range(lines: list[str])->int:
    """
    Gets the resid's for the protein amino acid only. Assumes that the PDB only contains 1 chain, 
    and that it is set up in the order as follows: Protein residues, ligands, cofactors, waters, 
    salts.

    Args:
        lines (list[str]): _description_

    Returns:
        int: _description_
    """
    current_residue_number = 1
    for line in lines:
        if line.startswith('ATOM') or line.startswith('HETATM'):
            residue_name = line[17:20].strip()
            if residue_name not in KNOWN_RESIDUES:
                return current_residue_number
            else:
                current_residue_number = int(line[22:26].strip())
    return current_residue_number


def get_residue(lines: list[str], residue_number: int, chain: str = "A"):
    for i, line in enumerate(iterable=lines):
        if line.startswith('ATOM') or line.startswith('HETATM'):
            current_residue_number = int(line[22:26].strip())
            current_chain = line[21:22].strip()
            if current_residue_number == residue_number and current_chain == chain:
                residue_name = line[17:20].strip()
                return residue_name
            
def get_mutant_structure(lines: list[str], delete_resid: int, replace_resid: int, chain: str = "A"):
    # print(lines)
    top_lines: int|None = None
    bottom_lines: int = 0
    middle_lines: int|None = None
    for i, line in enumerate(iterable=lines):
        if line.startswith('ATOM') or line.startswith('HETATM'):
            current_residue_number = int(line[22:26].strip())
            current_chain = line[21:22].strip()
            if current_chain == "":
                current_chain = chain
            if current_residue_number == delete_resid and current_chain == chain:
                if top_lines == None:
                    top_lines = i - 1
                    print(top_lines)
                bottom_lines = i + 1
                print(bottom_lines)
            elif current_residue_number == replace_resid and current_chain == chain:
                if middle_lines == None:
                    middle_lines = i
                print(middle_lines)
                lines[i] = line[:20] + str(delete_resid).rjust(6) + line[26:]
    
    new_pdb = lines[:top_lines] + lines[middle_lines:-2] + lines[bottom_lines:middle_lines]
    for line in lines[middle_lines:-2]:
        print(line)
    return new_pdb