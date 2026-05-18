import math
from collections import OrderedDict
import numpy as np
import pandas as pd
import os
import sys
import glob
import matplotlib.pyplot as plt
from scipy import stats
from scipy.stats import bootstrap
import warnings
import datetime
warnings.filterwarnings('ignore')

# Try to import alchemlyb components
try:
    from alchemlyb.estimators import TI, MBAR, BAR
    from alchemlyb.convergence import forward_backward_convergence
    from alchemlyb.visualisation import plot_ti_dhdl, plot_dF_state, plot_convergence
    from alchemlyb.preprocessing import statistical_inefficiency
    ALCHEMLYB_AVAILABLE = True
except ImportError:
    print("# Warning: alchemlyb not available. Using basic analysis only.", file=sys.stderr)
    ALCHEMLYB_AVAILABLE = False

class OnlineAvVar(object):
    '''A class that uses an online algorithm to compute mean and variance.'''

    def __init__(self, store_data = False):
        self.step = 0
        self.mean = 0.0
        self.M2 = 0.0

        self.store = store_data
        self.data = []

    def accumulate(self, x):
        '''Accumulate data points to compute mean and variance on-the-fly.'''

        self.step += 1

        delta = x - self.mean

        self.mean += delta / self.step
        self.M2 += delta * (x - self.mean)

        if self.store:
            self.data.append(x)

    def get_variance(self):
        '''Convenience function to return variance.'''

        if self.step < 2:
            return float('nan')
        return self.M2 / (self.step - 1)

    def get_stat(self):
        '''Convenience function to return mean and standard deviation.'''

        if self.step < 2:
            return self.mean, float('nan')
        return self.mean, math.sqrt(self.M2 / (self.step - 1))


def parse_amber_data_alchemlyb(file_pattern, lambda_value, skip=0, temperature=300.0):
    """Parse AMBER TI files and create alchemlyb-compatible DataFrame"""
    if not ALCHEMLYB_AVAILABLE:
        return None
    
    data_points = []
    
    for en_file in glob.glob(file_pattern):
        with open(en_file, 'r') as f:
            time_step = 0
            data_point_count = 0
            for line in f:
                if line.startswith('L9') and 'dV/dlambda' not in line:
                    try:
                        # Only process data after skipping initial points
                        if time_step >= skip:
                            # Parse the dV/dλ value - handle different possible formats
                            parts = line.split()
                            if len(parts) >= 7 and parts[5] in ['DV/DL', 'dV/dL', 'dHdl']:
                                dhdl_value = float(parts[6])
                            elif len(parts) >= 6:
                                # Try index 5 as fallback
                                dhdl_value = float(parts[5])
                            else:
                                time_step += 1
                                continue
                                
                            data_points.append({
                                'time': data_point_count,  # Use data_point_count for consistent indexing
                                'fep': lambda_value,
                                'dHdl': dhdl_value
                            })
                            data_point_count += 1
                        time_step += 1
                    except (IndexError, ValueError):
                        time_step += 1
                        continue
    
    if not data_points:
        return None
    
    df = pd.DataFrame(data_points)
    df = df.set_index(['time', 'fep'])
    return df


def parse_amber_mbar_data(out_pattern, lambda_states):
    """Parse AMBER output files to extract u_nk data for MBAR/BAR analysis"""
    if not ALCHEMLYB_AVAILABLE:
        return None, None
    
    all_u_nk_data = []
    all_dhdl_data = []
    
    for out_file in glob.glob(out_pattern):
        # Only process ti001.out files (production runs with MBAR data)
        if not out_file.endswith('ti001.out'):
            continue
            
        # Extract lambda value from the directory name
        current_dir = os.path.dirname(out_file)
        current_lambda = float(os.path.basename(current_dir))
        
        print(f"# Processing MBAR data from {out_file} (λ={current_lambda})", file=sys.stderr)
        
        with open(out_file, 'r') as f:
            content = f.read()
        
        # Find all MBAR Energy analysis sections
        mbar_sections = []
        lines = content.split('\n')
        
        time_step = 0
        i = 0
        while i < len(lines):
            if 'MBAR Energy analysis:' in lines[i]:
                # Found start of MBAR section
                i += 1
                energies = {}
                
                # Read energy values for all lambda states
                while i < len(lines) and lines[i].strip().startswith('Energy at'):
                    parts = lines[i].strip().split('=')
                    if len(parts) == 2:
                        try:
                            lambda_val = float(parts[0].split()[-1])
                            energy_str = parts[1].strip()
                            
                            # Check for AMBER overflow indicators (asterisks)
                            if '*' in energy_str or energy_str.lower() in ['nan', 'inf', '-inf']:
                                # print(f"# Warning: Invalid energy value '{energy_str}' for λ={lambda_val} in {out_file}", file=sys.stderr)
                                energy_val = np.nan
                            else:
                                energy_val = float(energy_str)
                            
                            energies[lambda_val] = energy_val
                        except (ValueError, IndexError) as e:
                            print(f"# Warning: Could not parse energy line '{lines[i].strip()}' in {out_file}: {e}", file=sys.stderr)
                            continue
                    i += 1
                
                # If we found energy data, add it to our collection
                if energies:
                    # Create u_nk entry (potential energies at all states)
                    u_nk_entry = {'time': time_step, 'fep': current_lambda}
                    for lam_state in lambda_states:
                        # Find the closest matching lambda value in energies (tolerance-based matching)
                        best_match = None
                        min_diff = float('inf')
                        for energy_lambda in energies.keys():
                            diff = abs(energy_lambda - lam_state)
                            if diff < min_diff and diff < 0.001:  # Tolerance of 0.001
                                min_diff = diff
                                best_match = energy_lambda
                        
                        if best_match is not None:
                            u_nk_entry[lam_state] = energies[best_match]
                        else:
                            u_nk_entry[lam_state] = np.nan
                    
                    all_u_nk_data.append(u_nk_entry)
                    time_step += 1
            else:
                i += 1
    
    # Convert to DataFrames if we have data
    u_nk_df = None
    dhdl_df = None
    
    if all_u_nk_data:
        u_nk_df = pd.DataFrame(all_u_nk_data)
        u_nk_df = u_nk_df.set_index(['time', 'fep'])
        
        # Check for data quality issues
        total_entries = len(u_nk_df)
        nan_count = u_nk_df.isna().sum().sum()
        valid_entries = total_entries * len(lambda_states) - nan_count
        
        print(f"# MBAR data quality: {valid_entries}/{total_entries * len(lambda_states)} valid entries ({nan_count} NaN values)", file=sys.stderr)
        
        if nan_count > 0:
            print(f"# Warning: Found {nan_count} invalid/overflow energy values in MBAR data", file=sys.stderr)
            print(f"# This may indicate numerical instability in the simulation at extreme lambda values", file=sys.stderr)
        
        # Also create dH/dl data from the u_nk data for TI
        dhdl_data = []
        for row_idx, row in u_nk_df.iterrows():
            time_val, fep_val = row_idx
            # Calculate dH/dλ by finite difference if possible
            # For now, we'll skip this as we already have dH/dλ from .en files
            pass
    else:
        print("# No valid MBAR data found in any ti001.out files", file=sys.stderr)
    
    return u_nk_df, dhdl_df


def enhanced_integration_analysis(data_dict, temperature=300.0, mbar_data=None, windows=None, skip=0, glob_pattern="*.en"):
    """Perform comprehensive integration analysis using multiple methods"""
    if not ALCHEMLYB_AVAILABLE:
        return None, None, None
    
    results = {}
    ti_df = None
    convergence_data = None
    
    # First, create proper alchemlyb dH/dλ DataFrame from our AMBER data
    try:
        print("# Creating alchemlyb-compatible dH/dλ DataFrame...", file=sys.stderr)
        all_dhdl_data = []
        
        if windows is not None:
            for window in windows:
                # Parse .en files to create proper alchemlyb DataFrame
                en_pattern = os.path.join(window, glob_pattern)
                lambda_val = float(os.path.basename(window))
                
                window_df = parse_amber_data_alchemlyb(en_pattern, lambda_val, skip, temperature)
                if window_df is not None:
                    all_dhdl_data.append(window_df)
            
            if all_dhdl_data:
                # Combine all dH/dλ data into single DataFrame
                ti_df = pd.concat(all_dhdl_data, ignore_index=False)
                print(f"# Successfully created dH/dλ DataFrame with {len(ti_df)} data points", file=sys.stderr)
                
                # Now use alchemlyb's TI estimator
                try:
                    print("# Running alchemlyb TI analysis...", file=sys.stderr)
                    ti_estimator = TI()
                    ti_result = ti_estimator.fit(ti_df)
                    
                    # Get the free energy difference
                    lambda_vals = sorted(ti_df.index.get_level_values('fep').unique())
                    first_idx = ti_result.states_.index(lambda_vals[0])
                    last_idx = ti_result.states_.index(lambda_vals[-1])
                    
                    delta_f_ti = ti_result.delta_f_.iloc[first_idx, last_idx]
                    error_ti = ti_result.d_delta_f_.iloc[first_idx, last_idx]
                    
                    results['TI_alchemlyb'] = {
                        'delta_f': delta_f_ti,
                        'error': error_ti,
                        'method': 'alchemlyb TI estimator with proper dH/dλ data'
                    }
                    
                    print(f"# alchemlyb TI completed: {delta_f_ti:.6f} ± {error_ti:.6f} kcal/mol", file=sys.stderr)
                    
                except Exception as e:
                    print(f"# alchemlyb TI failed: {str(e)}", file=sys.stderr)
                    results['TI_alchemlyb'] = {'error': f'alchemlyb TI analysis failed: {str(e)}'}
                
                # Statistical inefficiency analysis
                try:
                    print("# Attempting statistical inefficiency analysis...", file=sys.stderr)
                    from alchemlyb.preprocessing import statistical_inefficiency
                    
                    # Statistical inefficiency works best on individual lambda windows
                    # We'll try to apply it per-window rather than on combined data
                    lambda_windows = ti_df.index.get_level_values('fep').unique()
                    
                    corrected_data = []
                    total_original = 0
                    total_corrected = 0
                    inefficiency_ratios = []
                    
                    print(f"# Applying statistical inefficiency correction to {len(lambda_windows)} lambda windows...", file=sys.stderr)
                    
                    for lambda_val in sorted(lambda_windows):
                        lambda_data = ti_df.xs(lambda_val, level='fep').copy()
                        original_count = len(lambda_data)
                        
                        try:
                            # Apply statistical inefficiency to this window's data
                            corrected_window = statistical_inefficiency(lambda_data)
                            corrected_count = len(corrected_window)
                            
                            # Add lambda back to the index
                            corrected_window['fep'] = lambda_val
                            corrected_window = corrected_window.reset_index().set_index(['time', 'fep'])
                            corrected_data.append(corrected_window)
                            
                            window_ratio = original_count / corrected_count if corrected_count > 0 else 1.0
                            inefficiency_ratios.append(window_ratio)
                            total_original += original_count
                            total_corrected += corrected_count
                            
                            print(f"#   λ={lambda_val:.3f}: {original_count} -> {corrected_count} points (ratio: {window_ratio:.2f})", file=sys.stderr)
                            
                        except Exception as window_error:
                            print(f"#   λ={lambda_val:.3f}: Statistical inefficiency failed ({str(window_error)}), using original data", file=sys.stderr)
                            # Keep original data for this window
                            lambda_data['fep'] = lambda_val
                            lambda_data = lambda_data.reset_index().set_index(['time', 'fep'])
                            corrected_data.append(lambda_data)
                            total_original += original_count
                            total_corrected += original_count
                            inefficiency_ratios.append(1.0)
                    
                    if corrected_data:
                        ti_df_uncorr = pd.concat(corrected_data)
                        
                        overall_inefficiency = total_original / total_corrected if total_corrected > 0 else 1.0
                        avg_inefficiency = np.mean(inefficiency_ratios) if inefficiency_ratios else 1.0
                        
                        results['Statistical_Inefficiency'] = {
                            'delta_f': f"Inefficiency Analysis Complete",
                            'error': 0.0,
                            'details': {
                                'original_samples': total_original,
                                'uncorrelated_samples': total_corrected,
                                'overall_inefficiency_ratio': overall_inefficiency,
                                'average_window_ratio': avg_inefficiency,
                                'windows_processed': len(lambda_windows),
                                'correlation_description': f"Data reduced from {total_original} to {total_corrected} samples across {len(lambda_windows)} windows"
                            }
                        }
                        
                        print(f"# Statistical inefficiency analysis: {total_original} -> {total_corrected} samples", file=sys.stderr)
                        print(f"# Overall inefficiency ratio: {overall_inefficiency:.2f}, Average per window: {avg_inefficiency:.2f}", file=sys.stderr)
                        
                        # Run TI analysis on uncorrelated data
                        if total_corrected > 10:  # Need sufficient data
                            try:
                                ti_estimator_uncorr = TI()
                                ti_result_uncorr = ti_estimator_uncorr.fit(ti_df_uncorr)
                                
                                lambda_vals = sorted(ti_df_uncorr.index.get_level_values('fep').unique())
                                first_idx = ti_result_uncorr.states_.index(lambda_vals[0])
                                last_idx = ti_result_uncorr.states_.index(lambda_vals[-1])
                                
                                delta_f_ti_uncorr = ti_result_uncorr.delta_f_.iloc[first_idx, last_idx]
                                error_ti_uncorr = ti_result_uncorr.d_delta_f_.iloc[first_idx, last_idx]
                                
                                results['TI_Uncorrelated'] = {
                                    'delta_f': delta_f_ti_uncorr,
                                    'error': error_ti_uncorr,
                                    'method': f'alchemlyb TI with statistical inefficiency correction (n={total_corrected})'
                                }
                                
                                print(f"# TI on uncorrelated data: {delta_f_ti_uncorr:.6f} ± {error_ti_uncorr:.6f} kcal/mol", file=sys.stderr)
                                
                            except Exception as e:
                                print(f"# TI on uncorrelated data failed: {str(e)}", file=sys.stderr)
                        else:
                            print(f"# Insufficient uncorrelated data for TI analysis ({total_corrected} points)", file=sys.stderr)
                    else:
                        print("# No statistical inefficiency corrected data available", file=sys.stderr)
                    
                except Exception as e:
                    print(f"# Statistical inefficiency analysis failed: {str(e)}", file=sys.stderr)
                
                # Convergence analysis
                try:
                    print("# Performing forward-backward convergence analysis...", file=sys.stderr)
                    
                    # Create df_list: separate DataFrames for each lambda value (required format)
                    df_list = []
                    for lambda_val in sorted(ti_df.index.get_level_values('fep').unique()):
                        lambda_data = ti_df.xs(lambda_val, level='fep')
                        # CRITICAL: Keep the MultiIndex format that alchemlyb expects
                        # Each DataFrame must have a MultiIndex with (time, fep) even if fep is constant
                        lambda_data = lambda_data.reset_index()  # Reset to get time as column
                        lambda_data['fep'] = lambda_val  # Add back fep as constant column
                        lambda_data = lambda_data.set_index(['time', 'fep'])  # Recreate MultiIndex
                        df_list.append(lambda_data)
                        
                    print(f"# Created df_list with {len(df_list)} lambda DataFrames for convergence analysis", file=sys.stderr)
                    # print(df_list[0],file=sys.stderr)
                    # Debug: Check the format of the first DataFrame
                    if df_list:
                        first_df = df_list[0]
                        print(f"# First DataFrame index: {first_df.index.names}, shape: {first_df.shape}", file=sys.stderr)
                        print(f"# Sample index values: {first_df.index[:3].tolist()}", file=sys.stderr)
                        print(df_list[0],file=sys.stderr)
                    # Try convergence analysis with correct API
                    try:
                        # Use string estimator (correct API)
                        convergence_data = forward_backward_convergence(df_list, 'ti', num=20)
                        print(f"# Convergence analysis successful with TI estimator", file=sys.stderr)
                        print(f"# Convergence data shape: {convergence_data.shape}", file=sys.stderr)
                        print(f"# Convergence columns: {list(convergence_data.columns)}", file=sys.stderr)
                        print(convergence_data,file=sys.stderr)
                    except Exception as e1:
                        print(f"# TI convergence failed: {e1}", file=sys.stderr)
                        try:
                            # Try with MBAR as fallback (though we don't have u_nk data)
                            convergence_data = forward_backward_convergence(df_list, estimator='MBAR', num=10)
                            print(f"# Convergence analysis successful with MBAR estimator", file=sys.stderr)
                        except Exception as e2:
                            print(f"# MBAR convergence also failed: {e2}", file=sys.stderr)
                            convergence_data = None
                    
                    if convergence_data is not None and len(convergence_data) > 0:
                        # Extract convergence information from the returned DataFrame
                        # Expected columns: Forward, Forward_Error, Backward, Backward_Error, data_fraction
                        conv_forward = convergence_data['Forward'] if 'Forward' in convergence_data.columns else pd.Series()
                        conv_backward = convergence_data['Backward'] if 'Backward' in convergence_data.columns else pd.Series()
                        conv_forward_err = convergence_data['Forward_Error'] if 'Forward_Error' in convergence_data.columns else pd.Series()
                        conv_backward_err = convergence_data['Backward_Error'] if 'Backward_Error' in convergence_data.columns else pd.Series()
                        data_fractions = convergence_data['data_fraction'] if 'data_fraction' in convergence_data.columns else pd.Series()
                        
                        # Get final convergence estimate
                        final_forward = conv_forward.iloc[-1] if len(conv_forward) > 0 else np.nan
                        final_backward = conv_backward.iloc[-1] if len(conv_backward) > 0 else np.nan
                        final_forward_err = conv_forward_err.iloc[-1] if len(conv_forward_err) > 0 else np.nan
                        final_backward_err = conv_backward_err.iloc[-1] if len(conv_backward_err) > 0 else np.nan
                        
                        # Calculate convergence quality based on variation throughout the analysis
                        # Compare early estimates (20% data) with final estimates (100% data)
                        if len(conv_forward) >= 2 and len(conv_backward) >= 2:
                            early_forward = conv_forward.iloc[1]  # 20% data point
                            early_backward = conv_backward.iloc[1]  # 20% data point
                            forward_drift = abs(final_forward - early_forward)
                            backward_drift = abs(final_backward - early_backward)
                            convergence_diff = max(forward_drift, backward_drift)
                        else:
                            convergence_diff = 0.0
                        
                        results['Convergence_Analysis'] = {
                            'delta_f': f"Convergence Analysis Complete",
                            'error': 0.0,
                            'details': {
                                'forward_estimate': final_forward,
                                'backward_estimate': final_backward,
                                'forward_error': final_forward_err,
                                'backward_error': final_backward_err,
                                'convergence_difference': convergence_diff,
                                'convergence_quality': 'Good' if convergence_diff < 0.5 else 'Poor' if convergence_diff > 2.0 else 'Fair',
                                'data_points_forward': len(conv_forward),
                                'data_points_backward': len(conv_backward),
                                'num_fractions': len(data_fractions)
                            }
                        }
                        
                        print(f"# Convergence analysis: Forward={final_forward:.3f}±{final_forward_err:.3f}, Backward={final_backward:.3f}±{final_backward_err:.3f}, Diff={convergence_diff:.3f}", file=sys.stderr)
                    else:
                        print("# Convergence analysis returned no data", file=sys.stderr)
                        # Create a basic convergence analysis result indicating it wasn't available
                        results['Convergence_Analysis'] = {
                            'delta_f': f"Convergence Analysis Failed",
                            'error': float('inf'),
                            'details': {
                                'forward_estimate': np.nan,
                                'backward_estimate': np.nan,
                                'convergence_difference': np.nan,
                                'convergence_quality': 'Unknown',
                                'data_points_forward': 0,
                                'data_points_backward': 0
                            }
                        }
                    
                except Exception as e:
                    print(f"# Convergence analysis failed: {str(e)}", file=sys.stderr)
                    convergence_data = None
                    # Still provide a results entry
                    results['Convergence_Analysis'] = {
                        'delta_f': f"Convergence Analysis Error",
                        'error': float('inf'),
                        'details': {
                            'error_message': str(e),
                            'convergence_quality': 'Error'
                        }
                    }
            else:
                print("# Could not create dH/dλ DataFrame from .en files", file=sys.stderr)
        
    except Exception as e:
        print(f"# Enhanced TI setup failed: {str(e)}", file=sys.stderr)
    
    # Manual integration methods (keep these as backup/comparison)
    try:
        lambdas = sorted(data_dict.keys())
        means = [data_dict[lam][0] for lam in lambdas]
        sems = [data_dict[lam][1] for lam in lambdas]
        
        # Standard trapezoidal integration
        ti_result = np.trapezoid(means, lambdas)
        
        # Error propagation for trapezoidal integration
        error_sq = 0.0
        for i in range(len(lambdas) - 1):
            dx = lambdas[i+1] - lambdas[i]
            avg_sem = (sems[i] + sems[i+1]) / 2.0
            error_sq += (dx * avg_sem)**2
        ti_error = np.sqrt(error_sq)
        
        results['TI_Manual'] = {
            'delta_f': ti_result,
            'error': ti_error,
            'method': 'Manual trapezoidal integration with error propagation'
        }
        
        # Simpson's rule if we have enough points
        if len(lambdas) >= 3:
            try:
                from scipy.integrate import simpson
                simpson_result = simpson(means, lambdas)
                results['TI_Simpson'] = {
                    'delta_f': simpson_result,
                    'error': ti_error,  # Use same error estimate
                    'method': "Manual Simpson's rule integration"
                }
            except:
                pass  # Fall back to trapezoidal only
                
    except Exception as e:
        results['TI_Manual'] = {'error': f'Manual TI calculation failed: {str(e)}'}
    
    # Now try MBAR and BAR if we have u_nk data
    if mbar_data is not None:
        print("# Attempting MBAR/BAR analysis with u_nk data...", file=sys.stderr)
        
        try:
            # MBAR analysis - try with subsampling to improve convergence
            print("# Attempting MBAR analysis...", file=sys.stderr)
            
            # Subsample the data to improve numerical stability
            subsampled_data = mbar_data.groupby(level=['fep']).apply(
                lambda x: x.iloc[::10]  # Take every 10th point
            ).droplevel(0)
            
            print(f"# Using {len(subsampled_data)} subsampled points for MBAR", file=sys.stderr)
            
            mbar_estimator = MBAR()
            mbar_result = mbar_estimator.fit(subsampled_data)
            
            # Get the free energy difference from first to last state
            lambda_vals = sorted(subsampled_data.index.get_level_values('fep').unique())
            first_idx = mbar_result.states_.index(lambda_vals[0])
            last_idx = mbar_result.states_.index(lambda_vals[-1])
            
            delta_f_mbar = mbar_result.delta_f_.iloc[first_idx, last_idx]
            error_mbar = mbar_result.d_delta_f_.iloc[first_idx, last_idx]
            
            results['MBAR'] = {
                'delta_f': delta_f_mbar,
                'error': error_mbar,
                'method': f'Multistate Bennett Acceptance Ratio (subsampled data)'
            }
            
        except Exception as e:
            print(f"# MBAR failed: {str(e)}", file=sys.stderr)
            results['MBAR'] = {'error': f'MBAR analysis failed: {str(e)}'}
        
        try:
            # BAR analysis (between adjacent states)
            from alchemlyb.estimators import BAR
            
            # Get unique lambda values
            lambda_vals = sorted(mbar_data.index.get_level_values('fep').unique())
            
            bar_result = 0.0
            bar_error_sq = 0.0
            successful_bars = 0
            failed_segments = []
            
            print(f"# Attempting BAR analysis for {len(lambda_vals)-1} adjacent state pairs...", file=sys.stderr)
            
            for i in range(len(lambda_vals) - 1):
                lam1, lam2 = lambda_vals[i], lambda_vals[i+1]
                
                try:
                    # Extract data for these two states
                    data1 = mbar_data.xs(lam1, level='fep')
                    data2 = mbar_data.xs(lam2, level='fep')
                    
                    # Create u_nk data for just these two states
                    if lam1 in data1.columns and lam2 in data1.columns and lam1 in data2.columns and lam2 in data2.columns:
                        # Prepare data in the format alchemlyb expects
                        # Combine data from both states
                        combined_data = []
                        
                        # Add state 1 data
                        for idx, row in data1.iterrows():
                            combined_data.append({
                                'time': idx,
                                'fep': lam1,
                                lam1: row[lam1],
                                lam2: row[lam2]
                            })
                        
                        # Add state 2 data
                        for idx, row in data2.iterrows():
                            combined_data.append({
                                'time': len(data1) + idx,
                                'fep': lam2,
                                lam1: row[lam1], 
                                lam2: row[lam2]
                            })
                        
                        # Create DataFrame
                        bar_df = pd.DataFrame(combined_data)
                        bar_df = bar_df.set_index(['time', 'fep'])
                        
                        # Run BAR for this pair with better error handling
                        print(f"# BAR: Processing {lam1:.3f} -> {lam2:.3f}...", file=sys.stderr)
                        bar_estimator = BAR()
                        bar_fit = bar_estimator.fit(bar_df)
                        
                        # Get the result and validate it
                        segment_dg = bar_fit.delta_f_.iloc[0, 1]
                        segment_error = bar_fit.d_delta_f_.iloc[0, 1]
                        
                        # Validate the results - check for NaN, inf, or suspicious values
                        if (np.isnan(segment_dg) or np.isnan(segment_error) or 
                            np.isinf(segment_dg) or np.isinf(segment_error) or
                            segment_error <= 0 or abs(segment_dg) < 1e-10):
                            failed_segments.append(f"{lam1:.3f}->{lam2:.3f} (invalid result: dG={segment_dg:.6f}, err={segment_error:.6f})")
                            print(f"# BAR: {lam1:.3f} -> {lam2:.3f} failed - invalid result", file=sys.stderr)
                            continue
                        
                        # Result looks valid
                        bar_result += segment_dg
                        bar_error_sq += segment_error**2
                        successful_bars += 1
                        print(f"# BAR: {lam1:.3f} -> {lam2:.3f} success: dG={segment_dg:.6f} ± {segment_error:.6f}", file=sys.stderr)
                        
                    else:
                        failed_segments.append(f"{lam1:.3f}->{lam2:.3f} (missing energy columns)")
                        
                except Exception as bar_segment_error:
                    # Skip this segment if it fails
                    failed_segments.append(f"{lam1:.3f}->{lam2:.3f} ({str(bar_segment_error)})")
                    print(f"# BAR: {lam1:.3f} -> {lam2:.3f} failed: {bar_segment_error}", file=sys.stderr)
                    continue
            
            if successful_bars > 0:
                bar_error = np.sqrt(bar_error_sq)
                results['BAR'] = {
                    'delta_f': bar_result,
                    'error': bar_error,
                    'method': f'Bennett Acceptance Ratio ({successful_bars}/{len(lambda_vals)-1} successful segments)'
                }
                print(f"# BAR analysis completed: {bar_result:.6f} ± {bar_error:.6f} kcal/mol", file=sys.stderr)
            else:
                # Provide detailed failure information
                failure_summary = "; ".join(failed_segments[:3])  # Show first 3 failures
                if len(failed_segments) > 3:
                    failure_summary += f" ... and {len(failed_segments)-3} more"
                
                results['BAR'] = {
                    'error': f'BAR analysis failed for all {len(lambda_vals)-1} segments',
                    'details': f'Common issues: {failure_summary}',
                    'note': 'Poor overlap between states due to wide lambda spacing (0.039-0.125 gaps)'
                }
            
        except Exception as e:
            results['BAR'] = {'error': f'BAR analysis failed: {str(e)}'}
    
    else:
        # No MBAR data available
        results['MBAR'] = {
            'error': 'MBAR requires u_nk data (potential energies at all lambda states)',
            'note': 'Run with ifmbar=1 in AMBER to generate u_nk data'
        }
        
        results['BAR'] = {
            'error': 'BAR requires overlapping energy distributions between adjacent states',
            'note': 'Run with ifmbar=1 in AMBER to generate u_nk data'
        }
    
    # Provide analysis of the statistical quality
    try:
        quality_result = analyze_statistical_quality(data_dict)
        results['Statistical_Quality'] = quality_result
    except Exception as e:
        results['Statistical_Quality'] = {'error': f'Quality analysis failed: {str(e)}'}
    
    return results, ti_df, convergence_data


def analyze_statistical_quality(data_dict):
    """Analyze the statistical quality of the dH/dλ data"""
    lambdas = sorted(data_dict.keys())
    means = [data_dict[lam][0] for lam in lambdas]
    sems = [data_dict[lam][1] for lam in lambdas]
    stds = [data_dict[lam][2] for lam in lambdas]
    ns = [data_dict[lam][3] for lam in lambdas]
    
    # Calculate relative errors
    rel_errors = [sem/abs(mean) if mean != 0 else float('inf') for mean, sem in zip(means, sems)]
    
    # Find maximum relative error
    max_rel_error = max([re for re in rel_errors if re != float('inf')])
    avg_rel_error = np.mean([re for re in rel_errors if re != float('inf')])
    
    # Calculate effective sample sizes (rough estimate)
    eff_samples = [n if not np.isnan(std) and std > 0 else n for n, std in zip(ns, stds)]
    
    # Assess lambda spacing uniformity
    spacings = [lambdas[i+1] - lambdas[i] for i in range(len(lambdas)-1)]
    spacing_cv = np.std(spacings) / np.mean(spacings) if spacings else 0
    
    return {
        'delta_f': f"Quality Analysis Complete",
        'error': 0.0,
        'details': {
            'max_relative_error': max_rel_error,
            'avg_relative_error': avg_rel_error,
            'total_samples': sum(eff_samples),
            'lambda_windows': len(lambdas),
            'spacing_uniformity_cv': spacing_cv
        }
    }


def analyze_ddg_convergence(convergence_data1, convergence_data2, system1_name="System 1", system2_name="System 2"):
    """
    Analyze the convergence of ΔΔG = ΔG_system2 - ΔG_system1
    
    This is useful for relative binding free energies, mutation effects, etc.
    
    Parameters:
    -----------
    convergence_data1 : pandas.DataFrame
        Convergence data for the first system (reference)
    convergence_data2 : pandas.DataFrame  
        Convergence data for the second system (comparison)
    system1_name : str
        Name for the first system (e.g., "Wildtype", "Ligand A")
    system2_name : str
        Name for the second system (e.g., "Mutant", "Ligand B")
        
    Returns:
    --------
    ddg_convergence : pandas.DataFrame
        DataFrame containing ΔΔG convergence analysis
    """
    
    if not ALCHEMLYB_AVAILABLE or convergence_data1 is None or convergence_data2 is None:
        return None
        
    try:
        # Ensure both datasets have the same data fractions
        if 'data_fraction' in convergence_data1.columns and 'data_fraction' in convergence_data2.columns:
            fractions1 = convergence_data1['data_fraction'].values
            fractions2 = convergence_data2['data_fraction'].values
            
            # Use the intersection of fractions (in case they differ)
            common_fractions = np.intersect1d(fractions1, fractions2)
            
            if len(common_fractions) == 0:
                print(f"# Warning: No common data fractions between systems for ΔΔG analysis", file=sys.stderr)
                return None
                
            # Filter both datasets to common fractions
            mask1 = convergence_data1['data_fraction'].isin(common_fractions)
            mask2 = convergence_data2['data_fraction'].isin(common_fractions)
            
            conv1_filtered = convergence_data1[mask1].reset_index(drop=True)
            conv2_filtered = convergence_data2[mask2].reset_index(drop=True)
        else:
            # Assume same indexing if no data_fraction column
            min_len = min(len(convergence_data1), len(convergence_data2))
            conv1_filtered = convergence_data1.iloc[:min_len].reset_index(drop=True)
            conv2_filtered = convergence_data2.iloc[:min_len].reset_index(drop=True)
            common_fractions = np.arange(0.1, 1.1, 0.1)[:min_len]  # Assume 10%, 20%, etc.
        
        # Calculate ΔΔG for forward and backward directions
        ddg_data = {}
        ddg_data['data_fraction'] = common_fractions
        
        # Forward ΔΔG = Forward_system2 - Forward_system1
        if 'Forward' in conv1_filtered.columns and 'Forward' in conv2_filtered.columns:
            ddg_forward = conv2_filtered['Forward'].values - conv1_filtered['Forward'].values
            ddg_data['Forward'] = ddg_forward
            
            # Error propagation for forward ΔΔG
            if 'Forward_Error' in conv1_filtered.columns and 'Forward_Error' in conv2_filtered.columns:
                forward_err1 = conv1_filtered['Forward_Error'].values
                forward_err2 = conv2_filtered['Forward_Error'].values
                # Propagate errors: σ(A-B) = √(σA² + σB²)
                ddg_forward_err = np.sqrt(forward_err1**2 + forward_err2**2)
                ddg_data['Forward_Error'] = ddg_forward_err
        
        # Backward ΔΔG = Backward_system2 - Backward_system1  
        if 'Backward' in conv1_filtered.columns and 'Backward' in conv2_filtered.columns:
            ddg_backward = conv2_filtered['Backward'].values - conv1_filtered['Backward'].values
            ddg_data['Backward'] = ddg_backward
            
            # Error propagation for backward ΔΔG
            if 'Backward_Error' in conv1_filtered.columns and 'Backward_Error' in conv2_filtered.columns:
                backward_err1 = conv1_filtered['Backward_Error'].values
                backward_err2 = conv2_filtered['Backward_Error'].values
                ddg_backward_err = np.sqrt(backward_err1**2 + backward_err2**2)
                ddg_data['Backward_Error'] = ddg_backward_err
        
        # Create DataFrame
        ddg_convergence = pd.DataFrame(ddg_data)
        
        # Add metadata
        ddg_convergence.attrs = {
            'system1_name': system1_name,
            'system2_name': system2_name,
            'analysis_type': 'DDG_Convergence',
            'description': f'ΔΔG convergence: {system2_name} - {system1_name}'
        }
        
        # Calculate final ΔΔG and convergence quality
        if 'Forward' in ddg_convergence.columns and 'Backward' in ddg_convergence.columns:
            final_forward_ddg = ddg_convergence['Forward'].iloc[-1]
            final_backward_ddg = ddg_convergence['Backward'].iloc[-1]
            final_ddg_avg = (final_forward_ddg + final_backward_ddg) / 2.0
            ddg_difference = abs(final_forward_ddg - final_backward_ddg)
            
            print(f"# ΔΔG Convergence Analysis: {system2_name} - {system1_name}", file=sys.stderr)
            print(f"# Final ΔΔG (Forward): {final_forward_ddg:.3f} kcal/mol", file=sys.stderr)
            print(f"# Final ΔΔG (Backward): {final_backward_ddg:.3f} kcal/mol", file=sys.stderr)
            print(f"# Average ΔΔG: {final_ddg_avg:.3f} kcal/mol", file=sys.stderr)
            print(f"# Forward-Backward difference: {ddg_difference:.3f} kcal/mol", file=sys.stderr)
            
            # Assess convergence quality for ΔΔG
            if len(ddg_convergence) >= 2:
                early_forward_ddg = ddg_convergence['Forward'].iloc[1]  # 20% data
                early_backward_ddg = ddg_convergence['Backward'].iloc[1]  # 20% data
                forward_ddg_drift = abs(final_forward_ddg - early_forward_ddg)
                backward_ddg_drift = abs(final_backward_ddg - early_backward_ddg)
                max_ddg_drift = max(forward_ddg_drift, backward_ddg_drift)
                
                ddg_quality = 'Good' if max_ddg_drift < 0.5 else 'Poor' if max_ddg_drift > 2.0 else 'Fair'
                print(f"# ΔΔG Convergence Quality: {ddg_quality} (drift: {max_ddg_drift:.3f} kcal/mol)", file=sys.stderr)
        
        return ddg_convergence
        
    except Exception as e:
        print(f"# ΔΔG convergence analysis failed: {str(e)}", file=sys.stderr)
        return None


def create_ddg_convergence_plot(ddg_convergence_data, output_filename="ddg_convergence_plot.png"):
    """
    Create a standalone ΔΔG convergence plot
    
    Parameters:
    -----------
    ddg_convergence_data : pandas.DataFrame
        ΔΔG convergence data from analyze_ddg_convergence()
    output_filename : str
        Name for the output plot file
    """
    
    if ddg_convergence_data is None:
        print("# Error: No ΔΔG convergence data available for plotting", file=sys.stderr)
        return None
    
    try:
        import matplotlib.pyplot as plt
        
        # Create figure
        fig, ax = plt.subplots(1, 1, figsize=(10, 6))
        
        # Extract data
        if 'data_fraction' in ddg_convergence_data.columns:
            x_data = ddg_convergence_data['data_fraction'].values * 100  # Convert to percentage
        else:
            x_data = np.arange(len(ddg_convergence_data)) * 10 + 10  # Assume 10%, 20%, etc.
        
        # Plot forward and backward ΔΔG
        if 'Forward' in ddg_convergence_data.columns:
            forward_ddg = ddg_convergence_data['Forward'].values
            if 'Forward_Error' in ddg_convergence_data.columns:
                forward_err = ddg_convergence_data['Forward_Error'].values
                ax.errorbar(x_data, forward_ddg, yerr=forward_err, 
                           label='Forward ΔΔG', marker='o', capsize=3, linewidth=2)
            else:
                ax.plot(x_data, forward_ddg, label='Forward ΔΔG', marker='o', linewidth=2)
        
        if 'Backward' in ddg_convergence_data.columns:
            backward_ddg = ddg_convergence_data['Backward'].values
            if 'Backward_Error' in ddg_convergence_data.columns:
                backward_err = ddg_convergence_data['Backward_Error'].values
                ax.errorbar(x_data, backward_ddg, yerr=backward_err, 
                           label='Backward ΔΔG', marker='s', capsize=3, linewidth=2)
            else:
                ax.plot(x_data, backward_ddg, label='Backward ΔΔG', marker='s', linewidth=2)
        
        # Add horizontal line at ΔΔG = 0 for reference
        ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5, label='ΔΔG = 0')
        
        # Add ±0.5 kcal/mol significance band around final ΔΔG value
        if 'Forward' in ddg_convergence_data.columns and 'Backward' in ddg_convergence_data.columns:
            final_forward_ddg = ddg_convergence_data['Forward'].iloc[-1]
            final_backward_ddg = ddg_convergence_data['Backward'].iloc[-1]
            final_ddg_avg = (final_forward_ddg + final_backward_ddg) / 2.0
            
            # Add shaded region for ±0.5 kcal/mol around final value
            ax.axhspan(final_ddg_avg - 0.5, final_ddg_avg + 0.5, 
                      color='lightblue', alpha=0.3, 
                      label=f'±0.5 kcal/mol around final ΔΔG')
            
            # Add horizontal lines at the boundaries
            ax.axhline(y=final_ddg_avg + 0.5, color='blue', linestyle=':', alpha=0.7, linewidth=1)
            ax.axhline(y=final_ddg_avg - 0.5, color='blue', linestyle=':', alpha=0.7, linewidth=1)
            ax.axhline(y=final_ddg_avg, color='blue', linestyle='-', alpha=0.8, linewidth=2, 
                      label=f'Final ΔΔG = {final_ddg_avg:.3f} kcal/mol')
        
        # Set labels and title
        ax.set_xlabel('Data Fraction Used (%)')
        ax.set_ylabel('ΔΔG (kcal/mol)')
        
        # Get system names from metadata if available
        if hasattr(ddg_convergence_data, 'attrs'):
            sys1_name = ddg_convergence_data.attrs.get('system1_name', 'System 1')
            sys2_name = ddg_convergence_data.attrs.get('system2_name', 'System 2')
            ax.set_title(f'ΔΔG Convergence Analysis\n{sys2_name} - {sys1_name}')
        else:
            ax.set_title('ΔΔG Convergence Analysis')
        
        # Set y-limits around the converged ΔΔG value
        if 'Forward' in ddg_convergence_data.columns and 'Backward' in ddg_convergence_data.columns:
            final_forward = ddg_convergence_data['Forward'].iloc[-1]
            final_backward = ddg_convergence_data['Backward'].iloc[-1]
            center_ddg = (final_forward + final_backward) / 2.0
            
            # Set y-limits to ±3 kcal/mol around the converged ΔΔG
            y_margin = 4.0
            ax.set_ylim(center_ddg - y_margin, center_ddg + y_margin)
        
        # Add legend and grid
        ax.legend(loc='best', framealpha=0.8)
        ax.grid(True, alpha=0.3)
        
        # Add convergence quality assessment
        if 'Forward' in ddg_convergence_data.columns and 'Backward' in ddg_convergence_data.columns:
            final_forward_ddg = ddg_convergence_data['Forward'].iloc[-1]
            final_backward_ddg = ddg_convergence_data['Backward'].iloc[-1]
            final_ddg_avg = (final_forward_ddg + final_backward_ddg) / 2.0
            ddg_difference = abs(final_forward_ddg - final_backward_ddg)
            
            # Calculate drift if we have enough data points
            if len(ddg_convergence_data) >= 2:
                early_forward = ddg_convergence_data['Forward'].iloc[1]
                early_backward = ddg_convergence_data['Backward'].iloc[1]
                max_drift = max(abs(final_forward_ddg - early_forward), 
                               abs(final_backward_ddg - early_backward))
                quality = 'Good' if max_drift < 0.5 else 'Poor' if max_drift > 2.0 else 'Fair'
            else:
                quality = 'Unknown'
                max_drift = 0.0
            
            info_text = f'Convergence: {quality}\n'
            info_text += f'Final ΔΔG: {final_ddg_avg:.3f} kcal/mol\n'
            info_text += f'Forward: {final_forward_ddg:.3f} kcal/mol\n'
            info_text += f'Backward: {final_backward_ddg:.3f} kcal/mol\n'
            info_text += f'Difference: {ddg_difference:.3f} kcal/mol'
            
            ax.text(0.02, 0.98, info_text, 
                    transform=ax.transAxes, fontsize=10,
                    verticalalignment='top', horizontalalignment='left',
                    bbox=dict(boxstyle="round,pad=0.3", 
                            facecolor='lightgreen' if quality=='Good' else 'lightcoral' if quality=='Poor' else 'lightyellow', 
                            alpha=0.8))
        
        plt.tight_layout()
        
        # Save the plot
        plt.savefig(output_filename, dpi=300, bbox_inches='tight')
        print(f"# ΔΔG convergence plot saved as '{output_filename}'", file=sys.stderr)
        
        return fig
        
    except Exception as e:
        print(f"# Warning: ΔΔG convergence plot creation failed: {e}", file=sys.stderr)
        return None


def analyze_convergence(df):
    """Analyze convergence of the free energy calculation"""
    if not ALCHEMLYB_AVAILABLE or df is None:
        return None
    
    try:
        convergence = forward_backward_convergence(df, estimator=TI())
        return convergence
    except Exception as e:
        print(f"# Warning: Convergence analysis failed: {e}", file=sys.stderr)
        return None


def bootstrap_error_analysis(x, y, n_bootstrap=1000):
    """Perform bootstrap analysis for error estimation on integration"""
    def integrate_sample(x_sample, y_sample):
        return np.trapezoid(y_sample, x_sample)
    
    bootstrap_results = []
    n_points = len(x)
    
    for _ in range(n_bootstrap):
        # Bootstrap sample indices
        indices = np.random.choice(n_points, size=n_points, replace=True)
        x_sample = [x[i] for i in indices]
        y_sample = [y[i] for i in indices]
        
        # Sort by x values
        sorted_pairs = sorted(zip(x_sample, y_sample))
        x_sorted = [pair[0] for pair in sorted_pairs]
        y_sorted = [pair[1] for pair in sorted_pairs]
        
        dg = integrate_sample(x_sorted, y_sorted)
        bootstrap_results.append(dg)
    
    return np.array(bootstrap_results)


def quality_control_checks(data_dict):
    """Perform automated quality control checks"""
    checks = {}
    
    # Check for sufficient sampling
    min_samples = min([n for _, _, _, n in data_dict.values() if n > 0])
    max_samples = max([n for _, _, _, n in data_dict.values() if n > 0])
    checks['sampling_uniformity'] = max_samples / min_samples if min_samples > 0 else float('inf')
    
    # Check for outliers in dV/dl values
    means = [mean for mean, _, _, _ in data_dict.values()]
    mean_of_means = np.mean(means)
    std_of_means = np.std(means)
    outliers = [abs(mean - mean_of_means) > 3 * std_of_means for mean in means]
    checks['outlier_windows'] = sum(outliers)
    
    # Check lambda spacing
    lambdas = sorted(data_dict.keys())
    spacings = [lambdas[i+1] - lambdas[i] for i in range(len(lambdas)-1)]
    checks['max_lambda_spacing'] = max(spacings) if spacings else 0
    checks['min_lambda_spacing'] = min(spacings) if spacings else 0
    
    return checks


def create_analysis_plots(x, y, sems, bootstrap_results=None, alchemlyb_results=None, ti_df=None, convergence_data=None):
    """Create comprehensive analysis plots including alchemlyb visualizations"""
    # Determine figure layout based on available data
    if ti_df is not None or convergence_data is not None:
        fig, axes = plt.subplots(3, 2, figsize=(15, 18))  # Larger figure for more plots
    else:
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))  # Original layout
    
    # Plot 1: dV/dλ vs λ with error bars
    axes[0,0].errorbar(x, y, yerr=sems, marker='o', capsize=5, capthick=2)
    axes[0,0].set_xlabel('λ')
    axes[0,0].set_ylabel('dV/dλ (kcal/mol)')
    axes[0,0].set_title('Thermodynamic Integration Profile')
    axes[0,0].grid(True, alpha=0.3)
    
    # Plot 2: Integration curve
    cumulative = np.cumsum([0] + [np.trapezoid(y[i:i+2], x[i:i+2]) for i in range(len(x)-1)])
    axes[0,1].plot(x, cumulative, 'b-', marker='s', linewidth=2)
    axes[0,1].set_xlabel('λ')
    axes[0,1].set_ylabel('Cumulative ΔG (kcal/mol)')
    axes[0,1].set_title('Cumulative Free Energy Change')
    axes[0,1].grid(True, alpha=0.3)
    
    # Plot 3: Bootstrap distribution
    if bootstrap_results is not None:
        axes[1,0].hist(bootstrap_results, bins=50, alpha=0.7, density=True)
        mean_bootstrap = np.mean(bootstrap_results)
        std_bootstrap = np.std(bootstrap_results)
        axes[1,0].axvline(mean_bootstrap, color='red', linestyle='--', 
                         label=f'Mean: {mean_bootstrap:.3f}')
        axes[1,0].axvline(mean_bootstrap - std_bootstrap, color='red', linestyle=':', alpha=0.7)
        axes[1,0].axvline(mean_bootstrap + std_bootstrap, color='red', linestyle=':', alpha=0.7)
        axes[1,0].set_xlabel('ΔG (kcal/mol)')
        axes[1,0].set_ylabel('Density')
        axes[1,0].set_title('Bootstrap Distribution')
        axes[1,0].legend()
        axes[1,0].grid(True, alpha=0.3)
    else:
        axes[1,0].text(0.5, 0.5, 'Bootstrap analysis\nnot available', 
                      ha='center', va='center', transform=axes[1,0].transAxes)
    
    # Plot 4: Method comparison
    if alchemlyb_results:
        methods = []
        values = []
        errors = []
        
        for method, result in alchemlyb_results.items():
            # Check if this is a successful numerical result
            if 'delta_f' in result and not isinstance(result['delta_f'], str):
                # This is a successful numerical result
                methods.append(method.replace('_', '\n'))  # Better formatting
                values.append(result['delta_f'])
                errors.append(result.get('error', 0))
            elif 'error' in result and 'delta_f' not in result:
                # This is a failed method - we'll note it but not plot it
                pass
        
        if methods:
            # Create bar chart with successful methods
            bars = axes[1,1].bar(methods, values, yerr=errors, capsize=5, alpha=0.7, 
                               color=['green', 'blue', 'orange', 'red', 'purple', 'brown'][:len(methods)])
            axes[1,1].set_ylabel('ΔG (kcal/mol)')
            axes[1,1].set_title('Method Comparison')
            axes[1,1].grid(True, alpha=0.3)
            
            # Add value labels on bars
            for bar, value, error in zip(bars, values, errors):
                height = bar.get_height()
                # Handle negative values properly
                if height >= 0:
                    label_y = height + error + 0.5
                    va = 'bottom'
                else:
                    label_y = height - error - 0.5
                    va = 'top'
                
                axes[1,1].text(bar.get_x() + bar.get_width()/2., label_y,
                              f'{value:.2f}±{error:.3f}',
                              ha='center', va=va, fontsize=8, rotation=0)
            
            # Add failed methods info if any
            failed_methods = []
            for method, result in alchemlyb_results.items():
                if 'error' in result and 'delta_f' not in result:
                    failed_methods.append(method)
            
            if failed_methods:
                # Add text box with failed methods
                failed_text = f"Failed: {', '.join(failed_methods)}"
                axes[1,1].text(0.02, 0.98, failed_text, 
                              transform=axes[1,1].transAxes, fontsize=8, 
                              verticalalignment='top', horizontalalignment='left',
                              bbox=dict(boxstyle="round,pad=0.3", facecolor='lightcoral', alpha=0.5))
        else:
            # No successful methods - show limitations
            failed_methods = []
            for method, result in alchemlyb_results.items():
                if 'error' in result and 'delta_f' not in result:
                    failed_methods.append(method)
            
            if failed_methods:
                limitation_text = "Analysis Method Status:\n\n"
                limitation_text += f"✓ TI Enhanced: Available\n"
                limitation_text += f"✗ MBAR: {failed_methods.count('MBAR') > 0 and 'Needs u_nk data' or 'Failed'}\n"
                limitation_text += f"✗ BAR: {failed_methods.count('BAR') > 0 and 'Needs u_nk data' or 'Failed'}\n\n"
                limitation_text += "Note: Advanced methods require\n"
                limitation_text += "potential energy data (u_nk)\n"
                limitation_text += "from AMBER ifmbar=1 runs"
            else:
                limitation_text = "Method Limitations:\n\n"
                limitation_text += "• MBAR/BAR need u_nk data\n"
                limitation_text += "• Current: dH/dλ derivatives\n"
                limitation_text += "• TI is optimal for this data"
            
            axes[1,1].text(0.5, 0.5, limitation_text, 
                          ha='center', va='center', transform=axes[1,1].transAxes,
                          fontsize=10, bbox=dict(boxstyle="round,pad=0.3", alpha=0.3))
            axes[1,1].set_title('Analysis Method Assessment')
    else:
        axes[1,1].text(0.5, 0.5, 'Method comparison\nnot available', 
                      ha='center', va='center', transform=axes[1,1].transAxes)
    
    # Enhanced plots if we have alchemlyb data
    if ti_df is not None or convergence_data is not None:
        try:
            # Plot 5: alchemlyb dH/dλ visualization (if available)
            if ti_df is not None and ALCHEMLYB_AVAILABLE:
                try:
                    # Create a simplified dH/dλ plot since the alchemlyb plot_ti_dhdl may not work
                    # Plot dH/dλ data from the alchemlyb DataFrame
                    lambda_vals = sorted(ti_df.index.get_level_values('fep').unique())
                    
                    for i, lam in enumerate(lambda_vals[::2]):  # Plot every other lambda to avoid crowding
                        lam_data = ti_df.xs(lam, level='fep')
                        if 'dHdl' in lam_data.columns:
                            time_vals = lam_data.index.values
                            dhdl_vals = lam_data['dHdl'].values
                            
                            # Use alpha to make overlapping data visible
                            axes[2,0].plot(time_vals, dhdl_vals, alpha=0.6, linewidth=1, 
                                         label=f'λ={lam:.3f}' if i < 6 else '', markersize=2)
                    
                    axes[2,0].set_xlabel('Time (steps)')
                    axes[2,0].set_ylabel('dH/dλ (kcal/mol)')
                    axes[2,0].set_title('alchemlyb dH/dλ Time Series')
                    axes[2,0].legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
                    axes[2,0].grid(True, alpha=0.3)
                    
                except Exception as e:
                    print(f"# Warning: alchemlyb dH/dλ plot failed: {e}", file=sys.stderr)
                    axes[2,0].text(0.5, 0.5, f'alchemlyb dH/dλ plot\nfailed: {str(e)[:50]}...', 
                                  ha='center', va='center', transform=axes[2,0].transAxes)
            else:
                axes[2,0].text(0.5, 0.5, 'alchemlyb dH/dλ data\nnot available', 
                              ha='center', va='center', transform=axes[2,0].transAxes)
            
            # Plot 6: Convergence analysis (if available)
            if convergence_data is not None:
                try:
                    # Use alchemlyb's built-in plot_convergence function
                    from alchemlyb.visualisation import plot_convergence
                    
                    # Clear the axis and use alchemlyb's native plotting
                    axes[2,1].clear()
                    
                    # Create the convergence plot using alchemlyb
                    plot_convergence(convergence_data, ax=axes[2,1])
                    
                    # Enhance the plot with clearer labeling
                    axes[2,1].set_ylabel('ΔG (kcal/mol)')
                    axes[2,1].set_xlabel('Data Fraction Used (%)')
                    axes[2,1].set_title('Forward-Backward Convergence')
                    
                    # Set y-limits to zoom in on the convergence behavior
                    # Use ±3 kcal/mol around the converged value for better visibility
                    try:
                        if hasattr(convergence_data, 'columns'):
                            all_values = []
                            if 'Forward' in convergence_data.columns:
                                all_values.extend(convergence_data['Forward'].dropna().values)
                            if 'Backward' in convergence_data.columns:
                                all_values.extend(convergence_data['Backward'].dropna().values)
                            
                            if all_values:
                                # Use the final (converged) value as the center
                                if 'Forward' in convergence_data.columns and 'Backward' in convergence_data.columns:
                                    # Use average of final forward and backward values
                                    final_forward = convergence_data['Forward'].iloc[-1]
                                    final_backward = convergence_data['Backward'].iloc[-1]
                                    center_value = (final_forward + final_backward) / 2.0
                                elif 'Forward' in convergence_data.columns:
                                    center_value = convergence_data['Forward'].iloc[-1]
                                else:
                                    center_value = np.mean(all_values)

                                # Set y-limits to ±4 kcal/mol around the converged value
                                y_margin = 4.0
                                axes[2,1].set_ylim(center_value - y_margin, center_value + y_margin)
                    except Exception as e:
                        print(f"# Warning: Could not set y-limits for main convergence plot: {e}", file=sys.stderr)
                    
                    # Ensure legend is visible and clear
                    legend = axes[2,1].get_legend()
                    if legend is None:
                        # If alchemlyb didn't add a legend, add our own
                        lines = axes[2,1].get_lines()
                        if len(lines) >= 2:
                            # Typically first line is forward, second is reverse (backward)
                            axes[2,1].legend(['Forward (beginning → fraction)', 'Reverse (fraction ← end)'], 
                                           loc='best', framealpha=0.8, fontsize=8)
                    else:
                        # Update existing legend to be more descriptive
                        labels = [t.get_text() for t in legend.get_texts()]
                        new_labels = []
                        for label in labels:
                            if 'Forward' in label or 'forward' in label:
                                new_labels.append('Forward (beginning → fraction)')
                            elif 'Reverse' in label or 'reverse' in label or 'Backward' in label or 'backward' in label:
                                new_labels.append('Reverse (fraction ← end)')
                            else:
                                new_labels.append(label)
                        # Only update if we have meaningful labels
                        if any('Forward' in l or 'Reverse' in l for l in new_labels):
                            for i, new_label in enumerate(new_labels):
                                legend.get_texts()[i].set_text(new_label)
                        legend.set_frame_on(True)
                        try:
                            legend.set_framealpha(0.8)
                        except AttributeError:
                            # Older matplotlib versions may not have set_framealpha
                            pass
                        legend.set_fontsize(8)
                    
                    # Add convergence quality assessment
                    if hasattr(convergence_data, 'columns') and 'Forward' in convergence_data.columns and 'Backward' in convergence_data.columns:
                        # Calculate convergence quality using the same method as the main analysis
                        # Compare early estimates (20% data) with final estimates (100% data)
                        forward_final = convergence_data['Forward'].iloc[-1]
                        backward_final = convergence_data['Backward'].iloc[-1]
                        
                        if len(convergence_data) >= 2:
                            # Use the same calculation as in the main convergence analysis
                            early_forward = convergence_data['Forward'].iloc[1]  # 20% data point
                            early_backward = convergence_data['Backward'].iloc[1]  # 20% data point
                            forward_drift = abs(forward_final - early_forward)
                            backward_drift = abs(backward_final - early_backward)
                            conv_diff = max(forward_drift, backward_drift)
                        else:
                            conv_diff = 0.0
                        
                        quality = 'Good' if conv_diff < 0.5 else 'Poor' if conv_diff > 2.0 else 'Fair'
                        
                        info_text = f'Convergence: {quality}\n'
                        info_text += f'Forward: {forward_final:.3f}\n'
                        info_text += f'Backward: {backward_final:.3f}\n'
                        info_text += f'Difference: {conv_diff:.3f}'
                        
                        axes[2,1].text(0.02, 0.98, info_text, 
                                      transform=axes[2,1].transAxes, fontsize=8,
                                      verticalalignment='top', horizontalalignment='left',
                                      bbox=dict(boxstyle="round,pad=0.3", 
                                              facecolor='lightgreen' if quality=='Good' else 'lightcoral' if quality=='Poor' else 'lightyellow', 
                                              alpha=0.7))
                    elif hasattr(convergence_data, 'columns') and 'Forward' in convergence_data.columns:
                        forward_final = convergence_data['Forward'].iloc[-1]
                        axes[2,1].text(0.02, 0.98, f'Forward Only\nFinal: {forward_final:.3f}', 
                                      transform=axes[2,1].transAxes, fontsize=8,
                                      verticalalignment='top', horizontalalignment='left',
                                      bbox=dict(boxstyle="round,pad=0.3", facecolor='lightblue', alpha=0.7))
                    
                    # Add grid for better readability
                    axes[2,1].grid(True, alpha=0.3)
                        
                except Exception as e:
                    print(f"# Warning: alchemlyb convergence plot failed: {e}", file=sys.stderr)
                    axes[2,1].text(0.5, 0.5, f'alchemlyb convergence plot\nfailed: {str(e)[:50]}...', 
                                  ha='center', va='center', transform=axes[2,1].transAxes)
            else:
                axes[2,1].text(0.5, 0.5, 'Convergence analysis\nnot available', 
                              ha='center', va='center', transform=axes[2,1].transAxes)
                
        except Exception as e:
            print(f"# Warning: Enhanced plots failed: {e}", file=sys.stderr)
    
    plt.tight_layout()
    return fig


def create_convergence_plot(convergence_data):
    """Create a standalone convergence plot"""
    import matplotlib.pyplot as plt
    
    if convergence_data is None:
        print("# Error: No convergence data available for plotting", file=sys.stderr)
        return None
    
    try:
        from alchemlyb.visualisation import plot_convergence
        
        # Create a single figure for convergence plot
        fig, ax = plt.subplots(1, 1, figsize=(10, 6))
        
        # Create the convergence plot using alchemlyb
        plot_convergence(convergence_data, ax=ax)
        
        # Enhance the plot with clearer labeling
        # Fix the y-axis label to show proper units
        ax.set_ylabel('ΔG (kcal/mol)')
        ax.set_xlabel('Data Fraction Used (%)')
        ax.set_title('Forward-Backward Convergence Analysis')
        
        # Ensure legend is visible and clear
        legend = ax.get_legend()
        if legend is None:
            # If alchemlyb didn't add a legend, add our own
            lines = ax.get_lines()
            if len(lines) >= 2:
                # Typically first line is forward, second is reverse (backward)
                ax.legend(['Forward', 'Reverse'], 
                         loc='best', framealpha=0.8)
        else:
            # Update existing legend to be more descriptive
            labels = [t.get_text() for t in legend.get_texts()]
            new_labels = []
            for label in labels:
                if 'Forward' in label or 'forward' in label:
                    new_labels.append('Forward (beginning → fraction)')
                elif 'Reverse' in label or 'reverse' in label or 'Backward' in label or 'backward' in label:
                    new_labels.append('Reverse (fraction ← end)')
                else:
                    new_labels.append(label)
            # Only update if we have meaningful labels
            if any('Forward' in l or 'Reverse' in l for l in new_labels):
                for i, new_label in enumerate(new_labels):
                    legend.get_texts()[i].set_text(new_label)
            legend.set_frame_on(True)
            try:
                legend.set_framealpha(0.8)
            except AttributeError:
                # Older matplotlib versions may not have set_framealpha
                pass
        
        # Set y-limits to zoom in on the convergence behavior
        # Use ±3 kcal/mol around the converged value for better visibility
        # try:
        #     if hasattr(convergence_data, 'columns'):
        #         all_values = []
        #         if 'Forward' in convergence_data.columns:
        #             all_values.extend(convergence_data['Forward'].dropna().values)
        #         if 'Backward' in convergence_data.columns:
        #             all_values.extend(convergence_data['Backward'].dropna().values)
                
        #         if all_values:
        #             # Use the final (converged) value as the center
        #             if 'Forward' in convergence_data.columns and 'Backward' in convergence_data.columns:
        #                 # Use average of final forward and backward values
        #                 final_forward = convergence_data['Forward'].iloc[-1]
        #                 final_backward = convergence_data['Backward'].iloc[-1]
        #                 center_value = (final_forward + final_backward) / 2.0
        #             elif 'Forward' in convergence_data.columns:
        #                 center_value = convergence_data['Forward'].iloc[-1]
        #             else:
        #                 center_value = np.mean(all_values)
                    
                    # Set y-limits to ±3 kcal/mol around the converged value
                    # y_margin = 3.0
                    # ax.set_ylim(center_value - y_margin, center_value + y_margin)
                    # print(f"# Set convergence plot y-limits: [{center_value - y_margin:.3f}, {center_value + y_margin:.3f}] kcal/mol", file=sys.stderr)
        # except Exception as e:
        #     print(f"# Warning: Could not set y-limits for convergence plot: {e}", file=sys.stderr)
        
        # Add convergence quality assessment
        if hasattr(convergence_data, 'columns') and 'Forward' in convergence_data.columns and 'Backward' in convergence_data.columns:
            # Calculate convergence quality using the same method as the main analysis
            # Compare early estimates (20% data) with final estimates (100% data)
            forward_final = convergence_data['Forward'].iloc[-1]
            backward_final = convergence_data['Backward'].iloc[-1]
            
            if len(convergence_data) >= 2:
                # Use the same calculation as in the main convergence analysis
                early_forward = convergence_data['Forward'].iloc[1]  # 20% data point
                early_backward = convergence_data['Backward'].iloc[1]  # 20% data point
                forward_drift = abs(forward_final - early_forward)
                backward_drift = abs(backward_final - early_backward)
                conv_diff = max(forward_drift, backward_drift)
            else:
                conv_diff = 0.0
            
            quality = 'Good' if conv_diff < 0.5 else 'Poor' if conv_diff > 2.0 else 'Fair'
            
            info_text = f'Convergence: {quality}\n'
            info_text += f'Forward: {forward_final:.3f} kcal/mol\n'
            info_text += f'Backward: {backward_final:.3f} kcal/mol\n'
            info_text += f'Difference: {conv_diff:.3f} kcal/mol'
            
            # ax.text(0.02, 0.98, info_text, 
                    # transform=ax.transAxes, fontsize=11,
                    # verticalalignment='top', horizontalalignment='left',
                    # bbox=dict(boxstyle="round,pad=0.3", 
                    #         facecolor='lightgreen' if quality=='Good' else 'lightcoral' if quality=='Poor' else 'lightyellow', 
                    #         alpha=0.8))
        elif hasattr(convergence_data, 'columns') and 'Forward' in convergence_data.columns:
            forward_final = convergence_data['Forward'].iloc[-1]
            ax.text(0.02, 0.98, f'Forward Only\nFinal: {forward_final:.3f} kcal/mol', 
                    transform=ax.transAxes, fontsize=11,
                    verticalalignment='top', horizontalalignment='left',
                    bbox=dict(boxstyle="round,pad=0.3", facecolor='lightblue', alpha=0.8))
        
        # Add explanatory text about forward/reverse analysis
        # explanation = ('Forward: Uses data from beginning to each fraction\n'
        #               'Reverse: Uses data from each fraction to end\n'
        #               'Good convergence: Lines should be similar')
        

        # ax.text(0.98, 0.02, explanation, 
        #         transform=ax.transAxes, fontsize=9,
        #         verticalalignment='bottom', horizontalalignment='right',
        #         bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgray', alpha=0.6))
        
        # Ensure grid for better readability
        # ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
        
    except Exception as e:
        print(f"# Warning: Convergence plot creation failed: {e}", file=sys.stderr)
        return None


def generate_comprehensive_report(x, y, sems, stds, ns, dG, propagated_error, 
                                bootstrap_results=None, alchemlyb_results=None, 
                                qc_checks=None, convergence_data=None):
    """Generate a comprehensive analysis report"""
    
    print("\n" + "="*80)
    print(" COMPREHENSIVE THERMODYNAMIC INTEGRATION ANALYSIS REPORT")
    print("="*80)
    
    # Basic integration results
    print(f"\n1. BASIC INTEGRATION RESULTS:")
    print(f"   Trapezoidal Integration: {dG:.6f} ± {propagated_error:.6f} kcal/mol")
    
    # Bootstrap results
    if bootstrap_results is not None:
        bootstrap_mean = np.mean(bootstrap_results)
        bootstrap_std = np.std(bootstrap_results)
        bootstrap_ci = np.percentile(bootstrap_results, [2.5, 97.5])
        print(f"\n2. BOOTSTRAP ANALYSIS (n=1000):")
        print(f"   Bootstrap Mean: {bootstrap_mean:.6f} ± {bootstrap_std:.6f} kcal/mol")
        print(f"   95% Confidence Interval: [{bootstrap_ci[0]:.6f}, {bootstrap_ci[1]:.6f}] kcal/mol")
    
    # Alchemlyb results
    if alchemlyb_results:
        print(f"\n3. ENHANCED ANALYSIS METHODS:")
        available_methods = 0
        for method, result in alchemlyb_results.items():
            if 'error' in result and 'delta_f' not in result:
                # This is a true error case
                reason = result.get('error', 'Unknown error')
                print(f"   {method:15s}: Not available")
                print(f"                    Reason: {reason}")
                if 'details' in result:
                    print(f"                    Details: {result['details']}")
                if 'note' in result:
                    print(f"                    Note: {result['note']}")
            elif 'delta_f' in result:
                # This is a successful result
                if isinstance(result['delta_f'], str):
                    # Handle quality analysis and convergence analysis results
                    print(f"   {method:15s}: {result['delta_f']}")
                    if 'details' in result:
                        details = result['details']
                        
                        # Handle Statistical_Quality results
                        if 'max_relative_error' in details:
                            max_rel_err = details.get('max_relative_error', None)
                            avg_rel_err = details.get('avg_relative_error', None)
                            max_rel_str = f"{max_rel_err:.1%}" if max_rel_err is not None and not np.isnan(max_rel_err) else "N/A"
                            avg_rel_str = f"{avg_rel_err:.1%}" if avg_rel_err is not None and not np.isnan(avg_rel_err) else "N/A"
                            print(f"                    Max rel. error: {max_rel_str}")
                            print(f"                    Avg rel. error: {avg_rel_str}")
                            print(f"                    Total samples:  {details.get('total_samples', 'N/A')}")
                            print(f"                    Lambda windows: {details.get('lambda_windows', 'N/A')}")
                        
                        # Handle Convergence_Analysis results
                        elif 'forward_estimate' in details:
                            forward_est = details.get('forward_estimate', np.nan)
                            backward_est = details.get('backward_estimate', np.nan)
                            conv_diff = details.get('convergence_difference', np.nan)
                            conv_quality = details.get('convergence_quality', 'Unknown')
                            
                            forward_str = f"{forward_est:.6f}" if not np.isnan(forward_est) else "N/A"
                            backward_str = f"{backward_est:.6f}" if not np.isnan(backward_est) else "N/A"
                            diff_str = f"{conv_diff:.6f}" if not np.isnan(conv_diff) else "N/A"
                            
                            print(f"                    Forward estimate: {forward_str} kcal/mol")
                            print(f"                    Backward estimate: {backward_str} kcal/mol")
                            print(f"                    Convergence diff: {diff_str} kcal/mol")
                            print(f"                    Quality: {conv_quality}")
                            
                        # Handle other analysis types
                        else:
                            # Generic details printing for other analysis types
                            for key, value in details.items():
                                if key not in ['error_message']:  # Skip error messages, they're printed separately
                                    print(f"                    {key.replace('_', ' ').title()}: {value}")
                else:
                    # Handle numerical results
                    error_str = f" ± {result.get('error', 0):.6f}" if not np.isnan(result.get('error', np.nan)) else ""
                    print(f"   {method:15s}: {result['delta_f']:8.6f}{error_str} kcal/mol")
                    if 'method' in result:
                        print(f"                    Method: {result['method']}")
                available_methods += 1
        
        if available_methods == 0:
            print(f"\n   ⚠️  METHOD LIMITATIONS:")
            print(f"      Current data contains dH/dλ derivatives only")
            print(f"      Advanced methods (MBAR/BAR) require u_nk potential energy data")
            print(f"      TI methods are optimal for this type of data")
    else:
        print(f"\n3. ENHANCED ANALYSIS:")
        print(f"   Advanced methods not available (alchemlyb not installed)")
    
    # Quality control
    if qc_checks:
        print(f"\n4. QUALITY CONTROL CHECKS:")
        print(f"   Sampling uniformity ratio: {qc_checks['sampling_uniformity']:.2f}")
        print(f"   Outlier windows detected: {qc_checks['outlier_windows']}")
        print(f"   Lambda spacing (min/max): {qc_checks['min_lambda_spacing']:.3f} / {qc_checks['max_lambda_spacing']:.3f}")
        
        # Quality assessment
        issues = []
        if qc_checks['sampling_uniformity'] > 5:
            issues.append("Uneven sampling across windows")
        if qc_checks['outlier_windows'] > 0:
            issues.append(f"{qc_checks['outlier_windows']} potential outlier windows")
        if qc_checks['max_lambda_spacing'] > 0.2:
            issues.append("Large gaps in lambda spacing")
        
        if issues:
            print(f"   Warning - POTENTIAL ISSUES:")
            for issue in issues:
                print(f"      - {issue}")
        else:
            print(f"   OK - No major quality issues detected")
    
    # Statistical summary
    total_samples = sum(ns)
    # Count only windows with actual samples (not extrapolated endpoints)
    real_windows = sum(1 for n in ns if n > 0)
    extrapolated_windows = len(x) - real_windows
    
    print(f"\n5. STATISTICAL SUMMARY:")
    print(f"   Total windows: {real_windows} (simulated) + {extrapolated_windows} (extrapolated) = {len(x)}")
    print(f"   Total samples: {total_samples}")
    if real_windows > 0:
        print(f"   Average samples per simulated window: {total_samples/real_windows:.1f}")
    print(f"   Lambda range: {min(x):.3f} - {max(x):.3f}")
    
    # Convergence analysis
    if convergence_data is not None:
        print(f"\n6. CONVERGENCE ANALYSIS:")
        print(f"   Convergence analysis completed (see convergence plots)")
    
    print("\n" + "="*80)
    print(" END OF ANALYSIS REPORT")
    print("="*80 + "\n")



def get_dvdl_main(skip:int = 0,
                glob_pattern:str ="ti001.en",
                windows: list[str]|list[float] = [], 
                enable_mbar: bool = False,
                convergence_only: bool = False,
                ddg_reference:str = "",
                ddg_reference_name: str = "Reference",
                ddg_current_name: str = "Current",
                extrap:str = "polyfit",
                path: str = os.getcwd()):
    

    data = OrderedDict()
    cwd = path
    # Collect mean and SEM for each window
    for window in windows:
        if isinstance(window, float):
            window = str(window)
        os.chdir(os.path.join(cwd,window))

        dVdl = OnlineAvVar()
        ln = 0

        for en in glob.glob(glob_pattern):
            with open(en, 'r') as en_file:
                for line in en_file:
                    ln += 1

                    if ln > skip and line.startswith('L9') and not ('dV/dlambda' in line):
                        try:
                            # Parse the dV/dλ value - handle different possible formats
                            parts = line.split()
                            if len(parts) >= 7 and parts[5] in ['DV/DL', 'dV/dL', 'dHdl']:
                                dVdl.accumulate(float(parts[6]))
                            elif len(parts) >= 6:
                                # Try index 5 as fallback
                                dVdl.accumulate(float(parts[5]))
                        except (ValueError, IndexError):
                            # Skip lines that can't be parsed as expected
                            continue

        mean, std = dVdl.get_stat()
        n = dVdl.step if dVdl.step > 0 else 1
        sem = std / math.sqrt(n)
        data[float(os.path.basename(window))] = (mean, sem, std, n)

        os.chdir(cwd)

    # Prepare x, y, sem arrays
    x = list(data.keys())
    y = [d[0] for d in data.values()]
    sems = [d[1] for d in data.values()]
    stds = [d[2] for d in data.values()]
    ns = [d[3] for d in data.values()]

    # Extrapolate endpoints if needed, for both means and SEMs
    if extrap == 'linear':
        # Linear extrapolation for y and sems
        if 0.0 not in x:
            l_y = (x[0]*y[1] - x[1]*y[0]) / (x[0] - x[1])
            l_sem = (x[0]*sems[1] - x[1]*sems[0]) / (x[0] - x[1])
            x.insert(0, 0.0)
            y.insert(0, l_y)
            sems.insert(0, l_sem)
            stds.insert(0, float('nan'))
            ns.insert(0, 0)
        if 1.0 not in x:
            l_y = ((x[-2] - 1.0)*y[-1] + (1.0 - x[-1])*y[-2]) / (x[-2] - x[-1])
            l_sem = ((x[-2] - 1.0)*sems[-1] + (1.0 - x[-1])*sems[-2]) / (x[-2] - x[-1])
            x.append(1.0)
            y.append(l_y)
            sems.append(l_sem)
            stds.append(float('nan'))
            ns.append(0)

    elif extrap == 'polyfit' and (0.0 not in x or 1.0 not in x):
        deg = min(len(x) - 1, 6)
        coeffs_y = np.polyfit(x, y, deg)
        coeffs_sem = np.polyfit(x, sems, deg)
        if 0.0 not in x:
            x.insert(0, 0.0)
            y.insert(0, np.polyval(coeffs_y, 0.0))
            sems.insert(0, np.polyval(coeffs_sem, 0.0))
            stds.insert(0, float('nan'))
            ns.insert(0, 0)
        if 1.0 not in x:
            x.append(1.0)
            y.append(np.polyval(coeffs_y, 1.0))
            sems.append(np.polyval(coeffs_sem, 1.0))
            stds.append(float('nan'))
            ns.append(0)

    # Sort by lambda
    xysem = sorted(zip(x, y, sems, stds, ns), key=lambda t: t[0])
    x = [a for a, _, _, _, _ in xysem]
    y = [b for _, b, _, _, _ in xysem]
    sems = [c for _, _, c, _, _ in xysem]
    stds = [d for _, _, _, d, _ in xysem]
    ns = [e for _, _, _, _, e in xysem]

    # Print means and SEMs for each window (to stdout for dvdl.dat)
    print("# lambda mean_dVdl sem_dVdl std_dVdl n_samples")
    for a, b, c, d, e in zip(x, y, sems, stds, ns):
        print(a, b, c, d, e)

    # Numerical integration (trapezoidal rule)
    dG = np.trapezoid(y, x)

    # Error propagation: 
    # For each segment of the trapezoid, use the SEMs at both ends
    propagated_error_sq = 0.0
    for i in range(len(x) - 1):
        dx = x[i+1] - x[i]
        sem1 = sems[i]
        sem2 = sems[i+1]
        avg_sem = (sem1 + sem2) / 2.0
        propagated_error_sq += (dx * avg_sem)**2

    propagated_error = math.sqrt(propagated_error_sq)

    print(f'# dG = {dG:.6f} , {propagated_error:.6f} (kcal/mol, propagated SEM)')

    # ENHANCED ANALYSIS SECTION (all to stderr)
    print("# Starting enhanced analysis...", file=sys.stderr)
    
    # Prepare to capture all output for text file
    import io
    from contextlib import redirect_stdout
    
    output_buffer = io.StringIO()
    
    # Quality control checks
    qc_checks = quality_control_checks(data)
    
    # Bootstrap error analysis
    try:
        bootstrap_results = bootstrap_error_analysis(x, y, n_bootstrap=1000)
    except Exception as e:
        print(f"# Warning: Bootstrap analysis failed: {e}", file=sys.stderr)
        bootstrap_results = None
    
    # Alchemlyb integration methods
    alchemlyb_results = None
    convergence_data = None
    ti_df = None
    mbar_data = None
    
    if ALCHEMLYB_AVAILABLE:
        try:
            # MBAR/BAR data parsing (optional)
            if enable_mbar:
                print("# MBAR/BAR analysis enabled - checking for MBAR data in output files...", file=sys.stderr)
                
                # Get lambda states from the command line windows (actual simulated states only)
                # This avoids including extrapolated endpoints in MBAR analysis
                lambda_states = sorted([float(os.path.basename(window)) for window in windows])
                
                # Try to parse MBAR data from ti001.out files
                out_files_found = False
                for window in windows:
                    ti_out_pattern = os.path.join(window, "ti001.out")
                    if glob.glob(ti_out_pattern):
                        out_files_found = True
                        break
                
                if out_files_found:
                    print("# Found ti001.out files - attempting to parse MBAR data...", file=sys.stderr)
                    # Collect all u_nk data
                    all_u_nk_data = []
                    
                    for window in windows:
                        ti_out_pattern = os.path.join(window, "ti001.out")
                        u_nk_df, _ = parse_amber_mbar_data(ti_out_pattern, lambda_states)
                        if u_nk_df is not None:
                            all_u_nk_data.append(u_nk_df)
                    
                    if all_u_nk_data:
                        # Combine all u_nk data
                        mbar_data = pd.concat(all_u_nk_data, ignore_index=False)
                        print(f"# Successfully parsed MBAR data: {len(mbar_data)} data points across {len(lambda_states)} states", file=sys.stderr)
                    else:
                        print("# No MBAR data found in ti001.out files", file=sys.stderr)
                else:
                    print("# No ti001.out files found - MBAR analysis not available", file=sys.stderr)
            else:
                print("# MBAR/BAR analysis disabled (use --enable-mbar to enable)", file=sys.stderr)
            
            # Run enhanced analysis
            alchemlyb_results, ti_df, convergence_data = enhanced_integration_analysis(data, mbar_data=mbar_data, windows=windows, skip=skip, glob_pattern=glob_pattern)
            
            # ΔΔG Analysis (if reference data provided)
            ddg_convergence_data = None
            if ddg_reference and convergence_data is not None:
                try:
                    print(f"# Performing ΔΔG analysis using reference: {ddg_reference}", file=sys.stderr)
                    
                    # Load reference convergence data
                    if os.path.exists(ddg_reference):
                        if ddg_reference.endswith('.csv'):
                            # Load from CSV file
                            ref_convergence = pd.read_csv(ddg_reference)
                            print(f"# Loaded reference convergence data from {ddg_reference}", file=sys.stderr)
                        else:
                            print(f"# Error: Reference file must be a CSV file, got: {ddg_reference}", file=sys.stderr)
                            ref_convergence = None
                    else:
                        print(f"# Error: Reference convergence file not found: {ddg_reference}", file=sys.stderr)
                        ref_convergence = None
                    
                    if ref_convergence is not None:
                        # Perform ΔΔG convergence analysis
                        ddg_convergence_data = analyze_ddg_convergence(
                            ref_convergence, convergence_data, 
                            ddg_reference_name, ddg_current_name
                        )
                        
                        if ddg_convergence_data is not None:
                            # Save ΔΔG convergence data
                            ddg_filename = f"ddg_convergence_{ddg_reference_name.lower().replace(' ', '_')}_vs_{ddg_current_name.lower().replace(' ', '_')}.csv"
                            ddg_convergence_data.to_csv(ddg_filename, index=False)
                            print(f"# ΔΔG convergence data saved as '{ddg_filename}'", file=sys.stderr)
                            
                            # Create ΔΔG convergence plot
                            ddg_plot_filename = f"ddg_convergence_{ddg_reference_name.lower().replace(' ', '_')}_vs_{ddg_current_name.lower().replace(' ', '_')}.png"
                            ddg_fig = create_ddg_convergence_plot(ddg_convergence_data, ddg_plot_filename)
                            if ddg_fig is not None:
                                plt.close(ddg_fig)
                        else:
                            print("# ΔΔG convergence analysis failed", file=sys.stderr)
                    
                except Exception as e:
                    print(f"# ΔΔG analysis failed: {str(e)}", file=sys.stderr)
                    ddg_convergence_data = None
            elif ddg_reference:
                print("# Warning: ΔΔG analysis requested but convergence data not available", file=sys.stderr)
                print("# ΔΔG analysis requires successful convergence analysis of current system", file=sys.stderr)
            
            # Convergence analysis is now handled within enhanced_integration_analysis
        except Exception as e:
            print(f"# Warning: Alchemlyb analysis failed: {e}", file=sys.stderr)
    
    # Generate comprehensive report and capture output
    with redirect_stdout(output_buffer):
        generate_comprehensive_report(x, y, sems, stds, ns, dG, propagated_error,
                                    bootstrap_results, alchemlyb_results, qc_checks, convergence_data)
    
    # Print the report to stderr (so it appears in terminal but not in dvdl.dat)
    report_content = output_buffer.getvalue()
    print(report_content, file=sys.stderr)
    
    # Create and save analysis plots
    try:
        # Save current convergence data as CSV for future ΔΔG analyses
        if convergence_data is not None:
            convergence_filename = f"convergence_data_{ddg_current_name.lower().replace(' ', '_')}.csv"
            convergence_data.to_csv(convergence_filename, index=False)
            print(f"# Current convergence data saved as '{convergence_filename}' for future ΔΔG analyses", file=sys.stderr)
        
        if convergence_only:
            # Generate only convergence plot if requested and available
            if convergence_data is not None:
                print("# Generating convergence-only plot...", file=sys.stderr)
                fig = create_convergence_plot(convergence_data)
                if fig is not None:
                    fig.savefig('ti_convergence_plot.png', dpi=300, bbox_inches='tight')
                    print("# Convergence plot saved as 'ti_convergence_plot.png'", file=sys.stderr)
                    plt.close(fig)
                else:
                    print("# Warning: Convergence plot generation failed", file=sys.stderr)
            else:
                print("# Error: Convergence-only mode requested but no convergence data available", file=sys.stderr)
                print("# Note: Convergence analysis requires alchemlyb to be installed", file=sys.stderr)
        else:
            # Generate full analysis plots (default behavior)
            fig = create_analysis_plots(x, y, sems, bootstrap_results, alchemlyb_results, ti_df, convergence_data)
            fig.savefig('ti_analysis_plots.png', dpi=300, bbox_inches='tight')
            print("# Analysis plots saved as 'ti_analysis_plots.png'", file=sys.stderr)
            plt.close(fig)
    except Exception as e:
        print(f"# Warning: Plot generation failed: {e}", file=sys.stderr)
    
    # Write comprehensive CSV summary
    try:
        with open("ti_analysis_summary.csv", "w") as f:
            f.write("lambda,mean_dVdl,sem_dVdl,std_dVdl,n_samples\n")
            for a, b, c, d, e in zip(x, y, sems, stds, ns):
                f.write(f"{a},{b},{c},{d},{e}\n")
            f.write(f"#dG_trapezoidal,{dG},{propagated_error},,\n")
            
            # Add bootstrap results if available
            if bootstrap_results is not None:
                bootstrap_mean = np.mean(bootstrap_results)
                bootstrap_std = np.std(bootstrap_results)
                f.write(f"#dG_bootstrap,{bootstrap_mean},{bootstrap_std},,\n")
            
            # Add alchemlyb results if available
            if alchemlyb_results:
                for method, result in alchemlyb_results.items():
                    if 'delta_f' in result and 'error' not in result and not isinstance(result['delta_f'], str):
                        error_val = result.get('error', 0)
                        f.write(f"#dG_{method.lower()},{result['delta_f']},{error_val},,\n")
        
        print("# Analysis summary saved as 'ti_analysis_summary.csv'", file=sys.stderr)
    except Exception as e:
        print(f"# Warning: CSV writing failed: {e}", file=sys.stderr)
    
    # Write comprehensive text report
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open("ti_analysis_report.txt", "w") as f:
            f.write("="*80 + "\n")
            f.write(" THERMODYNAMIC INTEGRATION ANALYSIS REPORT\n")
            f.write("="*80 + "\n")
            f.write(f"Generated: {timestamp}\n")
            f.write(f"Working directory: {os.getcwd()}\n")
            f.write(f"Command: {' '.join(sys.argv)}\n")
            f.write("="*80 + "\n\n")
            
            # Write raw data table
            f.write("RAW DATA:\n")
            f.write("-" * 60 + "\n")
            f.write(f"{'Lambda':>8} {'Mean dV/dl':>12} {'SEM':>10} {'Std Dev':>10} {'N Samples':>10}\n")
            f.write("-" * 60 + "\n")
            for a, b, c, d, e in zip(x, y, sems, stds, ns):
                f.write(f"{a:8.3f} {b:12.6f} {c:10.6f} {d:10.6f} {e:10d}\n")
            f.write("-" * 60 + "\n\n")
            
            # Write the comprehensive report
            f.write(report_content)
            
            # Add summary section
            f.write("\n" + "="*80 + "\n")
            f.write(" SUMMARY OF RESULTS\n")
            f.write("="*80 + "\n")
            f.write(f"Trapezoidal Integration: {dG:.6f} ± {propagated_error:.6f} kcal/mol\n")
            
            if bootstrap_results is not None:
                bootstrap_mean = np.mean(bootstrap_results)
                bootstrap_std = np.std(bootstrap_results)
                f.write(f"Bootstrap Analysis:      {bootstrap_mean:.6f} ± {bootstrap_std:.6f} kcal/mol\n")
            
            if alchemlyb_results:
                for method, result in alchemlyb_results.items():
                    if 'delta_f' in result and 'error' not in result and not isinstance(result['delta_f'], str):
                        error_str = f" ± {result.get('error', 0):.6f}" if not np.isnan(result.get('error', np.nan)) else ""
                        f.write(f"{method} Analysis:{' '*(15-len(method))} {result['delta_f']:8.6f}{error_str} kcal/mol\n")
            
            f.write("\n" + "="*80 + "\n")
            f.write(" FILES GENERATED\n")
            f.write("="*80 + "\n")
            f.write("- dvdl.dat                 - Primary output with data table\n")
            f.write("- ti_analysis_report.txt   - This comprehensive text report\n")
            f.write("- ti_analysis_summary.csv  - Machine-readable summary\n")
            if os.path.exists("ti_analysis_plots.png"):
                f.write("- ti_analysis_plots.png    - 4-panel analysis visualization\n")
            if os.path.exists("ti_convergence_plot.png"):
                f.write("- ti_convergence_plot.png  - Convergence analysis visualization\n")
            f.write("\n")
        
        print("# Comprehensive report saved as 'ti_analysis_report.txt'", file=sys.stderr)
    except Exception as e:
        print(f"# Warning: Text report writing failed: {e}", file=sys.stderr)



if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Enhanced thermodynamic integration analysis with alchemlyb',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s 0 '*.en' [0-9].*                    # TI analysis only (default)
  %(prog)s --enable-mbar 0 '*.en' [0-9].*     # Include MBAR/BAR analysis
  %(prog)s --with-mbar 0 '*.en' [0-9].*       # Include MBAR/BAR analysis (alias)
  %(prog)s --convergence-only 0 '*.en' [0-9].* # Generate only convergence plot
  
  # ΔΔG Analysis Examples:
  %(prog)s --ddg-reference wildtype_convergence.csv --ddg-reference-name "Wildtype" --ddg-current-name "Mutant" 0 '*.en' [0-9].*
  %(prog)s --ddg-reference ligandA_convergence.csv --ddg-reference-name "Ligand A" --ddg-current-name "Ligand B" --convergence-only 0 '*.en' [0-9].*
        """
    )
    
    parser.add_argument('skip', type=int, 
                        help='Number of initial data points to skip')
    parser.add_argument('glob_pattern', 
                        help='Glob pattern for energy files (e.g., "*.en")')
    parser.add_argument('windows', nargs='+',
                        help='Lambda window directories')
    parser.add_argument('--enable-mbar', '--with-mbar', action='store_true',
                        help='Enable MBAR/BAR analysis (requires ti001.out files with ifmbar=1)')
    parser.add_argument('--convergence-only', action='store_true',
                        help='Generate only the convergence plot (faster, requires alchemlyb)')
    parser.add_argument('--ddg-reference', type=str, metavar='CONV_FILE',
                        help='Reference convergence CSV file for ΔΔG analysis (e.g., wildtype_convergence.csv)')
    parser.add_argument('--ddg-reference-name', type=str, default='Reference',
                        help='Name for the reference system in ΔΔG analysis (default: Reference)')
    parser.add_argument('--ddg-current-name', type=str, default='Current', 
                        help='Name for the current system in ΔΔG analysis (default: Current)')
    
    args = parser.parse_args()
    

    skip = args.skip
    glob_pattern = args.glob_pattern
    windows = args.windows
    enable_mbar = args.enable_mbar
    convergence_only = args.convergence_only
    ddg_reference = args.ddg_reference
    ddg_reference_name = args.ddg_reference_name
    ddg_current_name = args.ddg_current_name
    extrap = 'polyfit' # or linear or polyfit

    get_dvdl_main(skip=skip, glob_pattern=glob_pattern, windows=windows, enable_mbar=enable_mbar,
                convergence_only=convergence_only, ddg_reference=ddg_reference,
                ddg_reference_name=ddg_reference_name, ddg_current_name=ddg_current_name, extrap=extrap)