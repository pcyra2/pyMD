import argparse
import pandas
import os
from plotly.graph_objects import Figure
from pymd.tools import plot, io

def csv_plotter():
    parser = argparse.ArgumentParser()
    required = parser.add_argument_group("Required arguments")
    required.add_argument("-i", "--input", help="The input CSV file.", type=str, required=True)
    required.add_argument("-x", "--x_key", help="The key for the x-axis data.", type=str, required=True)
    required.add_argument("-y", "--y_key", help="The key for the y-axis data.", type=str, required=True)
    optional = parser.add_argument_group("Optional arguments")
    optional.add_argument("-o", "--output", help="The output plot name. If not provided, the plot will be displayed in a web browser.", required=False, type=str, default=None)
    optional.add_argument("-t", "--title", help="The title of the plot", required=False, type=str)
    optional.add_argument("-lx", "--xlabel", help="The label for the x-axis", required=False, type=str, default=None)
    optional.add_argument("-ly", "--ylabel", help="The label for the y-axis", required=False, type=str, default=None)
    optional.add_argument("-s", "--size", help="The size of the plot. If not provided, the default size will be used.", required=False, type=str, default=None)

    args = parser.parse_args()
    
    assert os.path.isfile(args.input)

    data = pandas.read_csv(args.input)
    fig = plot.plot_df(data, x_label=args.x_key, y_label=args.y_key)
    if args.xlabel is not None:
        fig.update_xaxes(title_text=args.xlabel )
    if args.ylabel is not None:
        fig.update_yaxes(title_text=args.ylabel )
    if args.title is not None:
        fig.update_layout(title_text=args.title)

    fig.show()

    if args.size is not None:
        width=int(args.size.split("x")[0])
        height=int(args.size.split("x")[1])
    else:
        width = 1920
        height = 1080

    if args.output is not None:
        fig.write_image(file=args.output, width=width, height=height)
