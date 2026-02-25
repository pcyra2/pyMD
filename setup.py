from setuptools import setup
# set up using "pip install -e ."
setup(
    name='pyMD',
    version='1.0',
    py_modules=['pyMD'],
    entry_points={
        'console_scripts': [
        ],
    },
    install_requires=["pyscf", "rdkit", "spyrmsd", 
                      "plotly", "pyscf-dispersion", "h5py",
                      "pytest", "pytest-cov", "pytest-html"]
)
