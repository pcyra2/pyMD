from setuptools import setup
# set up using "pip install -e ."
setup(
    name='pymd',
    version='1.0',
    py_modules=['pymd'],
    entry_points={
        'console_scripts': [
            "pTI = pymd.experiments.md.ti.experiment:main",
            "pMD = pymd.experiments.md.replica_md.experiment:main",
            "mdout = pymd.experiments.md.analysis:md_out_analysis",
            "rmsd = pymd.experiments.md.analysis:rmsd",
            "SinglePoint = pymd.experiments.qm.orca:single_point",
            "Opt = pymd.experiments.qm.orca:optimise",
            "plt_csv = pymd.experiments.analysis.plotter:csv_plotter"
        ],
    },
    install_requires=["pyscf", "rdkit", "spyrmsd", "matplotlib",
                      "plotly", "pyscf-dispersion", "h5py",
                      "pytest", "pytest-cov", "pytest-html",
                      "pytest-subprocess", "numpy", "MDAnalysis",
                      "kaleido", "pandas", "mkdocs", "mkdocstrings",
                      "mkdocs-material", "mkdocstrings-python", 
                      "mkdocs-coverage", "mkdocs-material-extensions"]
)
