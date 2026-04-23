import plotly
from plotly import graph_objects
import pandas

def plot_df(df: pandas.DataFrame,
        x_label: str,
        y_label: str|list[str]
        ) -> graph_objects.Figure:
    if isinstance(y_label, str):
        y_label = [y_label]
    fig = graph_objects.Figure()
    for label in y_label:
        fig.add_trace(graph_objects.Scatter(x=df[x_label], y=df[label]))
    fig.update_layout(template="simple_white")
    fig.update_xaxes(title_text=x_label)
    if len(y_label) == 1:
        fig.update_yaxes(title_text=y_label[0])
    return fig