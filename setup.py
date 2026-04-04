from setuptools import setup
# set up using "pip install -e ."
setup(
    name='pymd',
    version='1.0',
    py_modules=['pymd'],
    entry_points={
        'console_scripts': [
            "pTI = pymd.experiments.md.protein_thermodynamic_integration:main",
            "SinglePoint = pymd.experiments.qm.orca:single_point",
            "Opt = pymd.experiments.qm.orca:optimise"
        ],
    },
    install_requires=["pyscf", "rdkit", "spyrmsd", "matplotlib",
                      "plotly", "pyscf-dispersion", "h5py",
                      "pytest", "pytest-cov", "pytest-html",
                      "pytest-subprocess", "numpy"]
)
