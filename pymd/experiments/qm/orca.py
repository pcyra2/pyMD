import argparse
from pprint import pprint
import glob
import shutil
import os

from pymd.qm.kernels.orca import Orca
from pymd.tools import io, structure

def single_point() -> None:
    """Automatically performs a standard single point energy calculation within orca."""
    parser = argparse.ArgumentParser(prog="Orca single point calculation.")
    required = parser.add_argument_group("Required arguments")
    required.add_argument("-m", "--method", help="QM method for the calculation", type = str,
                        required = True)
    required.add_argument("-b","--basis", help="The basis set to be used for the calculation.",
                        type=str, required=True)
    files = parser.add_argument_group("IO arguments")
    files.add_argument("-i", "--input_structure", help="Input structure file. If none is given it " \
                        "will default to the `.xyz` file in the current working directory. If " \
                        "multiple coordinates exist, then a calculation will be " \
                        "performed for each.", type=str, required=False, default=None)
    files.add_argument("-n", "--job_name", help="Name of the input/output file.", type = str,
                        required = False, default = "Orca")
    hw = parser.add_argument_group("Hardware configuration arguments")
    hw.add_argument("-cpu", "--cores", help="Number of cores to use for the calculation.", type = int,
                        required=False, default=4)
    hw.add_argument("-mem", "--memory", help="The total memory for the calculation in MB. " \
                        "Defaults to 4000", type=int, default=4000)
    mol = parser.add_argument_group("Molecular configuration")
    mol.add_argument("-c","--charge", help="Net charge of the system. Make sure if multiple " \
                        "structures are given, they have the same net charge. Defaults to 0", 
                        type = int, default=0, required=False)
    mol.add_argument("-s", "--spin", help="The spin of the system. This should be 2S not 2S+1.",
                        required=False, default=0)
    extra = parser.add_argument_group("Extra calculation configurations")
    extra.add_argument("-d", "--dispersion", help="The dispersion correction to include, if any.",
                        type=str, required=False, default=None)
    extra.add_argument("-conv", "--convergence_criteria", help="The convergence criteria to use. ",
                       choices=["sloppy", "loose", "medium", "strong", "tight", "verytight",
                                "extreme"], default="tight", required=False)
    extra.add_argument("-ri", "--rijcosx", help="Use the resolution of identity to speed up the " \
                        "calculation. No extra arguments required.", action="store_true")
    extra.add_argument("-no_easy", "--no_easy", help="Whether to use easy convergence tactics",action="store_true")
    extra.add_argument("-solv", "--solvent", help="The implicit solvent to use. This will be using the CPCM Model", required=False, default="None")
    extra.add_argument("-f", "--frequency", help="Whether to perform a frequency" \
                        " calculation to check if the system is a true minima/saddle point.", 
                        action="store_true")

    args = parser.parse_args()

    if args.input_structure is None:
        structures = glob.glob("*.xyz")
    else:
        structures = args.input_structure

    if len(structures) > 1:
        paths = [struct.replace(".xyz","") for struct in structures]
        for path in paths:
            io.make_dir(path=path)
            shutil.copy(f"{path}.xyz", os.path.join(path, f"{path}.xyz"))
    else:
        paths = ["./"]
    
    if args.job_name == "Orca" and args.frequency:
        args.job_name = "Freq"


    for i, structure in enumerate(iterable=structures):
        print(f"INfO: Running calculation on {structure}")
        print(f"INFO: Charge: {args.charge}, Spin: {args.spin}")
        job = Orca(input_file_name=f"{args.job_name}.inp", output_file_name=f"{args.job_name}.out", coordinates=structure, charge=args.charge, spin=args.spin, path=paths[i])
        job.set_standard_variables(method=args.method, basis=args.basis, disp=args.dispersion)
        job.set_hardware(cores=args.cores, mem=args.memory, gpu=False)
        if args.rijcosx:
            job.add_job_variables("RIJCOSX")
        job.set_conv_criteria(args.convergence_criteria)
        if args.no_easy is False:
            job.add_job_variables("EasyConv")
        if args.solvent != "None":
            job.add_solvent(solvent=args.solvent, model="CPCM")
        if args.frequency:
            job.add_job_variables("Freq")
        job.run()
        job.print_output()

def optimise() -> None:
    """Automatically performs a standard geometry optimisation calculation within orca."""
    parser = argparse.ArgumentParser(prog="Orca single point calculation.")
    required = parser.add_argument_group("Required arguments")
    required.add_argument("-m", "--method", help="QM method for the calculation", type = str,
                        required = True)
    required.add_argument("-b","--basis", help="The basis set to be used for the calculation.",
                        type=str, required=True)
    files = parser.add_argument_group("IO arguments")
    files.add_argument("-i", "--input_structure", help="Input structure file. If none is given it " \
                        "will default to the `.xyz` file in the current working directory. If " \
                        "multiple coordinates exist, then a calculation will be " \
                        "performed for each.", type=str, required=False, default=None)
    files.add_argument("-n", "--job_name", help="Name of the input/output file.", type = str,
                        required = False, default = "Opt")
    hw = parser.add_argument_group("Hardware configuration arguments")
    hw.add_argument("-cpu", "--cores", help="Number of cores to use for the calculation.", type = int,
                        required=False, default=4)
    hw.add_argument("-mem", "--memory", help="The total memory for the calculation in MB. " \
                        "Defaults to 4000", type=int, default=4000)
    mol = parser.add_argument_group("Molecular configuration")
    mol.add_argument("-c","--charge", help="Net charge of the system. Make sure if multiple " \
                        "structures are given, they have the same net charge. Defaults to 0", 
                        type = int, default=0, required=False)
    mol.add_argument("-s", "--spin", help="The spin of the system. This should be 2S not 2S+1.",
                        required=False, default=0)
    extra = parser.add_argument_group("Extra calculation configurations")
    extra.add_argument("-d", "--dispersion", help="The dispersion correction to include, if any.",
                        type=str, required=False, default=None)
    extra.add_argument("-ts", "--transition_state", help="Whether it is a Transition state " \
                        "or not, defaults to False", action="store_true")
    extra.add_argument("-conv", "--convergence_criteria", help="The convergence criteria to use. ",
                       choices=["sloppy", "loose", "medium", "strong", "tight", "verytight",
                                "extreme"], default="tight", required=False)
    extra.add_argument("-ri", "--rijcosx", help="Use the resolution of identity to speed up the " \
                        "calculation. No extra arguments required.", action="store_true")
    extra.add_argument("-no_easy", "--no_easy", help="Whether to use easy convergence tactics", 
                       action="store_true")
    extra.add_argument("-solv", "--solvent", help="The implicit solvent to use. This will be " \
                        "using the CPCM Model", required=False, default="None")
    extra.add_argument("-f", "--frequency", help="Whether to perform a subsequent frequency" \
                        " calculation to check if the system is a true minima/saddle point.", 
                        action="store_true")
    args = parser.parse_args()

    if args.input_structure is None:
        structures = glob.glob("*.xyz")
    else:
        structures = args.input_structure

    if len(structures) > 1:
        paths = [struct.replace(".xyz","") for struct in structures]
        for path in paths:
            io.make_dir(path=path)
            shutil.copy(f"{path}.xyz", os.path.join(path, f"{path}.xyz"))
    else:
        paths = ["./"]
    
    if args.transition_state and args.job_name == "Opt":
        args.job_name = "OptTS"

    for i, struct in enumerate(iterable=structures):
        print(f"INfO: Running calculation on {struct}")
        print(f"INFO: Charge: {args.charge}, Spin: {args.spin}")
        job = Orca(input_file_name=f"{args.job_name}.inp", output_file_name=f"{args.job_name}.out", coordinates=struct, charge=args.charge, spin=args.spin, path=paths[i])
        job.set_standard_variables(method=args.method, basis=args.basis, disp=args.dispersion)
        job.set_hardware(cores=args.cores, mem=args.memory, gpu=False)
        if args.transition_state:
            job.add_job_variables("OptTS")
        else:
            job.add_job_variables("Opt")
        if args.rijcosx:
            job.add_job_variables("RIJCOSX")
        job.set_conv_criteria(args.convergence_criteria)
        if args.no_easy is False:
            job.add_job_variables("EasyConv")
        if args.solvent != "None":
            job.add_solvent(solvent=args.solvent, model="CPCM")
        if args.frequency:
            job.run_secondary_frequency()

        job.run()
        job.print_output()

def irc() -> None:
    """Automatically performs a standard single point energy calculation within orca."""
    parser = argparse.ArgumentParser(prog="Orca IRC calculation.")
    required = parser.add_argument_group("Required arguments")
    required.add_argument("-m", "--method", help="QM method for the calculation", type = str,
                        required = True)
    required.add_argument("-b","--basis", help="The basis set to be used for the calculation.",
                        type=str, required=True)
    
    files = parser.add_argument_group("IO arguments")
    files.add_argument("-i", "--input_structure", help="Input structure file. If none is given it " \
                        "will default to the `.xyz` file in the current working directory. If " \
                        "multiple coordinates exist, then a calculation will be " \
                        "performed for each.", type=str, required=False, default=None)
    files.add_argument("-n", "--job_name", help="Name of the input/output file.", type = str,
                        required = False, default = "IRC")
    
    hw = parser.add_argument_group("Hardware configuration arguments")
    hw.add_argument("-cpu", "--cores", help="Number of cores to use for the calculation.", type = int,
                        required=False, default=4)
    hw.add_argument("-mem", "--memory", help="The total memory for the calculation in MB. " \
                        "Defaults to 4000", type=int, default=4000)
    
    mol = parser.add_argument_group("Molecular configuration")
    mol.add_argument("-c","--charge", help="Net charge of the system. Make sure if multiple " \
                        "structures are given, they have the same net charge. Defaults to 0", 
                        type = int, default=0, required=False)
    mol.add_argument("-s", "--spin", help="The spin of the system. This should be 2S not 2S+1.",
                        required=False, default=0)
    
    extra = parser.add_argument_group("Extra calculation configurations")
    extra.add_argument("-d", "--dispersion", help="The dispersion correction to include, if any.",
                        type=str, required=False, default=None)
    extra.add_argument("-conv", "--convergence_criteria", help="The convergence criteria to use. ",
                       choices=["sloppy", "loose", "medium", "strong", "tight", "verytight",
                                "extreme"], default="tight", required=False)
    extra.add_argument("-ri", "--rijcosx", help="Use the resolution of identity to speed up the " \
                        "calculation. No extra arguments required.", action="store_true")
    extra.add_argument("-no_easy", "--no_easy", help="Whether to use easy convergence tactics",action="store_true")
    extra.add_argument("-solv", "--solvent", help="The implicit solvent to use. This will be using the CPCM Model", required=False, default="None")
    extra.add_argument("-f", "--frequency", help="Whether to perform a frequency" \
                        " calculation to check if the system is a true minima/saddle point.", 
                        action="store_true")

    args = parser.parse_args()

    if args.input_structure is None:
        structures = glob.glob("*.xyz")
    else:
        structures = args.input_structure

    if len(structures) > 1:
        paths = [struct.replace(".xyz","") for struct in structures]
        for path in paths:
            io.make_dir(path=path)
            shutil.copy(f"{path}.xyz", os.path.join(path, f"{path}.xyz"))
    else:
        paths = ["./"]
    
    if args.job_name == "Orca" and args.frequency:
        args.job_name = "Freq"


    for i, structure in enumerate(iterable=structures):
        print(f"INfO: Running calculation on {structure}")
        print(f"INFO: Charge: {args.charge}, Spin: {args.spin}")
        job = Orca(input_file_name=f"{args.job_name}.inp", output_file_name=f"{args.job_name}.out", coordinates=structure, charge=args.charge, spin=args.spin, path=paths[i])
        job.set_standard_variables(method=args.method, basis=args.basis, disp=args.dispersion)
        job.set_hardware(cores=args.cores, mem=args.memory, gpu=False)
        if args.rijcosx:
            job.add_job_variables("RIJCOSX")
        job.set_conv_criteria(args.convergence_criteria)
        if args.no_easy is False:
            job.add_job_variables("EasyConv")
        if args.solvent != "None":
            job.add_solvent(solvent=args.solvent, model="CPCM")
        if args.frequency:
            job.add_job_variables("Freq")
        job.add_job_variables("IRC")
        job.run()
        job.print_output()
