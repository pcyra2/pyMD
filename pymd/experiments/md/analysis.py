import argparse
from audioop import rms
import pandas
import os
from plotly.graph_objects import Figure
from pymd.tools import plot, io
from pymd.md.utilities import md_analysis




def md_out_analysis() -> None:
    parser = argparse.ArgumentParser(prog="MD output data miner.")
    required = parser.add_argument_group("Required arguments")
    required.add_argument("-i", "--input", help="The MD output file that contains the simulation "\
        "data. This file is usually a .out or .log file. If multiple files are provided, use a " \
        "comma separated list", type=str, required=True)
    required.add_argument("-p", "--plot", help="Plot the specific property of the simulation. " \
        "This can be one of the following: energy, temperature, pressure, volume, or a custom "\
        "property that is defined in the MD output file. Multiple variables can be " \
        "supplied using a comma seperated list", type=str, required=False, default="None")
    optional = parser.add_argument_group("Optional arguments")
    optional.add_argument("-o", "--output", help="The output file that will contain the raw " \
        "data csv. If not provided, the results will be printed to the saved to `mdout.csv.", 
        default="mdout.csv", type=str, required=False)
    optional.add_argument("-s", "--software", help = "What software the output file is made from." \
        "Defaults to amber", required=False, default="amber", type=str)
    optional.add_argument("-x", "--x_axis", help="What should be on the x axis of the plot, " \
        "defaults to TotalTime however can also be TotalSteps or another variable that is tracked",
        required=False, default="TotalTime", type=str)


    args: argparse.Namespace = parser.parse_args()

    if args.software == "amber":
        from pymd.user_configs.amber_defaults import OUTPUTFILE_DATAFLAGS
        print(f"INFO: The known trackable keys for amber are: {OUTPUTFILE_DATAFLAGS.keys()}")
        from pymd.md.kernels.amber import Amber
        mm = Amber(start_coordinates="", parm_file="")
        
    else:
        raise NotImplementedError
    
    core_data = ["time", "temperature", "pressure", "volume", "density", "energy", ]
    data_types: list[str] = args.plot.split(",")
    print(data_types)
    if data_types[0] != "None":
        for d in data_types:
            if d not in core_data:
                core_data += d

    # for i, data in enumerate(data_types):
    #     if data in OUTPUTFILE_DATAFLAGS.keys():
    #         data_types[i] = OUTPUTFILE_DATAFLAGS[data]

    input_files: list[str] = args.input.split(",")
    data_list: list[pandas.DataFrame] = []
    for file in input_files:
        if len(data_list)>0:
            start_time = data_list[-1]["TotalTime"].iloc[-1]
            start_steps = data_list[-1]["TotalSteps"].iloc[-1]
        else:
            start_time = 0
            start_steps = 0
        print(f"INFO: Extracting data from {file}")
        
        data = mm.parse_outfile(file, core_data, start_time=start_time, start_steps = start_steps)
        if data_types[0] != "None":
            for var in data_types:
                print(f"INFO: {var} mean = {round(data[var].mean(),3)} with std. deviation of {round(data[var].std(),3)}")
            
        data_list += [data]
        # print(data)
    df: pandas.DataFrame = pandas.concat(data_list, ignore_index=True)
    print(df)
    df.to_csv(args.output, index=False)
    if data_types[0] != "None":
        for var in data_types:
            plt: Figure = plot.plot_df(df=df, x_label=args.x_axis, y_label=var)
            plt.show()

def rmsd():
    parser = argparse.ArgumentParser(prog="MD output data miner.")
    required = parser.add_argument_group("Required arguments")
    required.add_argument("-p", "--parm", help="Parameter file", type=str, required=True)
    required.add_argument("-c", "--coords", help="Comma delimited list of coordinate/trajectory" \
        " files", required=True, type=str)
    optional = parser.add_argument_group("Optional arguments")
    optional.add_argument("-o", "--outfile", help="Name of the output csv file", required=False, default="RMSD.csv")
    optional.add_argument("-r","--ref", help="Reference Frame to align to", required=False,
                          type=int, default=0)
    optional.add_argument("-t", "--type", help="The type of RMSD to calculate. " \
        "Defaults to `backbone`",  nargs="+",
          action="extend",default=[], required=False)
    optional.add_argument("-plt", "--plot", help="Whether to plot", required=False, default=False)

    args = parser.parse_args()
    traj_files= args.coords.split(",")
    assert os.path.isfile(args.parm)
    for file in traj_files:
        assert os.path.isfile(file)
    
    if len(args.type) > 0:
        rmsd_tpyes= args.type
    else:
        rmsd_tpyes = ["backbone"]


    
    u = md_analysis.gen_universe(args.parm, traj_files)
    # print(vars(u))
    rmsf = md_analysis.RMSF(u=u, rmsd_type="protein and name CA")
    rmsd = md_analysis.RMSD_traj(u, ref=args.ref, rmsd_type=rmsd_tpyes)
    # print(rmsd)
    if isinstance(rmsd_tpyes, str):
        rmsd_tpyes = [rmsd_tpyes]
    df = pandas.DataFrame(rmsd, columns=["Frame", "Time"]+rmsd_tpyes)
    if args.plot:
        for var in rmsd_tpyes:
            plt = plot.plot_df(df, "Frame", var)
            plt.show()
    df.to_csv(args.outfile, index=False)
    for var in rmsf.keys():
        df_tmp = pandas.DataFrame()#[rmsf[var]["resids"],rmsf[var]["residues"], rmsf[var]["rmsf"] ], 
                                  #columns=["resids", "residues", "rmsf"])
        for i, x in enumerate(["resids", "residues", "rmsf"]):
            df_tmp.insert(loc=i, column=x, value=rmsf[var][x], )
            print(df_tmp)
        df_tmp.to_csv(f"RMSF.csv")
        if args.plot:
            plt = plot.plot_df(df_tmp, "resids", "rmsf")
            plt.show()
            