# Installation process

## Install

To install pyMD, first clone the repo into a directory:

``` sh
gh repo clone pcyra2/pyMD
```


Next create the conda environment:

``` sh
conda create -n pyMD 
conda activate pyMD
conda install python==3.10
cd pyMD
pip install -e . 
conda install ambertools
```

!!! warning

    Warning, to re-compile this documentation, you also need to instal mkdocs-coverage... sadly this isnt a conda package so install it using:
    ``` sh
    pip install mkdocs-coverage
    ```

## Pre-requisits 

### ORCA

To use the ORCA backend functionality or benchmarking, ORCA must be installed. You can obtain this [here](https://orcaforum.kofo.mpg.de/app.php/portal)

### NAMD

For all dynamics simulations, we use NAMD which can be found [here](http://www.ks.uiuc.edu/Research/namd/). Two versions of NAMD are recommended:

- a CUDA-GPU accelorated version for running standard MD
- a CPU version for running QM/MM


### WHAM

You must also have the WHAM code from the [Grossfield Lab](http://membrane.urmc.rochester.edu/?page_id=126) in order to perform WHAM calculations for Umbrella Sampling.


## Configure

It is important now to configure the default variables! 
Go into the user_configs directory within the source.

``` sh
cd pymd/user_configs
```




??? tip "Other configs."

    Here you can also edit the other files in the directory. This allows you to:

        - Tune your MD parameters (MM_Variables.py)  
        - List available QM methods to ORCA for benchmarking (QM_Methods.py)
        - Change the Default inputs for each calculation type (if you always use the same QM method for example.) (Defaultinputs.py)

!!! note "Final stage (optional)"

    Within the source directory, run:
    ``` sh
    mkdocs build
    ```

    This will compile the documentation webpage and update the current configuration below.

## Current Configuration:

``` py title="Defaultinputs.py"
--8<-- "./UserVars/Defaultinputs.py"
```

``` py title="MM_Variables.py"
--8<-- "./UserVars/MM_Variables.py"
```

``` py title="QM_Methods.py"
--8<-- "./UserVars/QM_Methods.py"
```

``` py title="HPC_Config.py"
--8<-- "./UserVars/HPC_Config.py"
```

``` py title="SoftwarePaths.py"
--8<-- "./UserVars/SoftwarePaths.py"
```