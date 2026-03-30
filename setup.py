from setuptools import setup
# set up using "pip install -e ."
setup(
    name='pymd',
    version='1.0',
    py_modules=['pymd'],
    entry_points={
        'console_scripts': [
            "pTI = pymd.experiments.protein_thermodynamic_integration:main"
        ],
    },
    install_requires=["pyscf", "rdkit", "spyrmsd", "matplotlib",
                      "plotly", "pyscf-dispersion", "h5py",
                      "pytest", "pytest-cov", "pytest-html",
                      "pytest-subprocess", "numpy"]
)
