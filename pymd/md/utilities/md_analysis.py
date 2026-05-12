import MDAnalysis
import MDAnalysis.analysis
import MDAnalysis.analysis.align
import MDAnalysis.analysis.rms
import numpy

def gen_universe(parm_file: str, coordinates: str|list[str], in_memory_step: int = 1) -> MDAnalysis.Universe:
    u = MDAnalysis.Universe(parm_file, coordinates, in_memory_step=in_memory_step)
    return u

def RMSD_traj(u: MDAnalysis.Universe, ref: int=0, rmsd_type: str|list[str] = "backbone") : 
    # aligned = MDAnalysis.analysis.align.AlignTraj(mobile=u,
    #                                         reference=ref,
    #                                         select=rmsd_type,
    #                                         in_memory=True,
    #                                         match_atoms=True)
    # rmsd_data = numpy.zeros(len(u.trajectory))
    # for i, frame in enumerate(u.trajectory):
    #     r = MDAnalysis.analysis.rms.RMSD(u, ref, select=rmsd_type, ref_frame=i).run()

    if isinstance(rmsd_type, list):
        if len(rmsd_type) == 1:
            select = rmsd_type[0]
            group_select = None
        select = rmsd_type[0]
        group_select = rmsd_type[1:]
    else:
        select = rmsd_type
        group_select = None
    R = MDAnalysis.analysis.align.rms.RMSD(u, u, 
                                        select=select, ref_frame=ref,
                                        groupselections=group_select)        
    R.run()
    return R.results.rmsd
    

def RMSF(u: MDAnalysis.Universe, rmsd_type: str|list[str] = "backbone") : 
    if isinstance(rmsd_type, list):
        if len(rmsd_type) > 1:
            reference_type = "backbone"
        else:
            reference_type = rmsd_type[0]
    else:
        reference_type = rmsd_type


    ref_str = MDAnalysis.analysis.align.AverageStructure(u, u, select=reference_type, in_memory=True)

    
    


    aligned = MDAnalysis.analysis.align.AlignTraj(mobile=u,
                                            reference=ref_str.results.universe,
                                            select=reference_type,
                                            in_memory=True,
                                            match_atoms=True).run()
    
    if isinstance(rmsd_type, str):
        rmsd_type = [rmsd_type]
    data = dict()
    for var in rmsd_type:
        
        selection = u.select_atoms(var)
        R = MDAnalysis.analysis.rms.RMSF(selection).run()
        residues = selection.residues.resnames.tolist()
        residues_all = [residues[i-1] for i in selection.resids.tolist()]
        # for i in selection.resids.tolist():
        #     print(i)
        #     print(residues[i-1])
        data[var] = dict(resids =selection.resids.tolist(), rmsf = R.results.rmsf.tolist(), residues=residues_all )
    return data