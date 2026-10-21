import ROOT
import numpy as np

def calibration_fit(histogram, energy_ranges, energies, expbg = False):
    """Function to create a linear calibration fit based on a histogram. Returns slope and constant of linear fit. 
    Inputs: Histogram to base calibration on.
    Ranges within which the peaks of the histogram are located, input as a list if tuples. AT LEAST 2 points.
    Known energies of these peaks, in MeV."""
    
    channels = []
    for i in range(len(energy_ranges)):
        cal_fit=ROOT.TF1("cal_fit_" + str(i), "gaus", energy_ranges[i][0], energy_ranges[i][1])
        histogram.Fit(cal_fit, "RS0")
        channels.append(cal_fit.GetParameter('Mean'))
    channels = np.array(channels, dtype='float64')
    energies = np.array(energies, dtype='float64')

    graph = ROOT.TGraph(len(channels), channels, energies)
    fit = ROOT.TF1("calib", "pol1", min(channels), max(channels))
    graph.Fit(fit)
    
    a = fit.GetParameter(1)
    b = fit.GetParameter(0)

    return [a, b]


def calibrated_histogram(linear_fit, acquisition, n_of_bins, summed = False, title = "Calibrated Spectrum"):
    a = linear_fit[0]
    b = linear_fit[1]
    if summed:
        data_cal = a * (acquisition['Combined_Summed']/(len(acquisition.active_chs)*2)) + b
    else:
        data_cal = a * (acquisition['s']/len(acquisition.active_chs)) + b
        

    emax = a * n_of_bins + b
    emin = b

    hist_cal = ROOT.TH1F("h_cal", title, n_of_bins, emin, emax)
    hist_cal.Fill(data_cal)

    return(hist_cal)
    

def calibrated_acquisition(linear_fit, acquisition, n_of_bins, summed = False):
    a = linear_fit[0]
    b = linear_fit[1]
    if summed:
        data_cal = a * (acquisition['Combined_Summed']/len(acquisition.active_chs)) + b   
    else:
        data_cal = a * (acquisition['s']/len(acquisition.active_chs)) + b
        

    emax = a * n_of_bins + b
    emin = b

    return(data_cal, emin, emax)
    

def energy_resolution_old(hist, peak_ranges, show_fit = True):
    """Calculates energy resolution. Input peak_ranges as a list of tuples. 
    Outputs a list of resolutions for the different energies."""
    if show_fit:
        spec = ["R+S", "R+S"]
    else:
        spec = ["RS0", "R+S0"]
    resolutions = []
    for i in range (len(peak_ranges)):
        resolution_fit = ROOT.TF1("res_fit_" + str(i), "gaus", peak_ranges[i][0], peak_ranges[i][1])
        if i == 0:
            fit_result = hist.Fit(resolution_fit, spec[0])
        else:
            fit_result = hist.Fit(resolution_fit, spec[1])

        std_dev = resolution_fit.GetParameter('Sigma')
        
        std_dev_error = resolution_fit.GetParError('Sigma')
        mean = resolution_fit.GetParameter('Mean')
        mean_error = resolution_fit.GetParError('Mean')
        cov = fit_result.GetCovarianceMatrix()
        cov_sigma_E = cov[2][1]
        #print(f"Mean: {mean}")
        #print(f"Mean error: {mean_error}")
        #print(f"Sigma: {std_dev}")
        
        #print(f"Sigma error: {std_dev_error}")
        #print(f"Covariance: {cov_sigma_E}")
        resolution = (2.35 * std_dev)/mean
        resolutions.append(resolution)


        import math

        mu = mean
        sigma = std_dev
        
        dmu = mean_error
        dsigma = std_dev_error
        
        #cov = cov_matrix[1][2]   # cov(mu, sigma)
        
        R = 2.35 * sigma / mu
        
        term1 = (2.35 / mu)**2 * dsigma**2
        term2 = (2.35 * sigma / mu**2)**2 * dmu**2
        term3 = 2 * (2.35 / mu) * (-2.35 * sigma / mu**2) * cov_sigma_E
        
        var_R = term1 + term2 + term3
        dR = math.sqrt(var_R)

        #print(f"Resolution: {100*resolution:.3g} %")
        #print(f"Resolution Error: {100*dR:.3g} %")

    return resolutions






def energy_resolution(hist, peak_ranges, show_fit=True):
    """Calculates energy resolution for Gaussian peaks.

    For each peak range:
      1. Find the maximum bin within the given range.
      2. Fit a Gaussian over 100 bins to either side of the peak.
      3. Calculate the energy resolution.

    Args:
        hist: ROOT histogram.
        peak_ranges: List of (xmin, xmax) tuples.
        show_fit: Whether to draw the fit.

    Returns:
        List of energy resolutions.
    """
    import ROOT
    import math

    resolutions = []
    errors = []

    for i, (xmin, xmax) in enumerate(peak_ranges):

        # Find the maximum bin within the specified range
        bin_min = hist.GetXaxis().FindBin(xmin)
        bin_max = hist.GetXaxis().FindBin(xmax)

        peak_bin = bin_min
        max_content = -float("inf")

        for b in range(bin_min, bin_max + 1):
            content = hist.GetBinContent(b)
            if content > max_content:
                max_content = content
                peak_bin = b

        # Get the peak position in histogram coordinates
        peak_position = hist.GetXaxis().GetBinCenter(peak_bin)

        # Define the fit range using 70 bins on each side
        fit_min_bin = max(1, int(peak_bin - peak_bin*0.1 - 20))
        fit_max_bin = min(hist.GetNbinsX(), int(peak_bin + peak_bin*0.1 + 20))

        fit_min = hist.GetXaxis().GetBinLowEdge(fit_min_bin)
        fit_max = hist.GetXaxis().GetBinUpEdge(fit_max_bin)

        # Create and fit the Gaussian
        resolution_fit = ROOT.TF1(
            "res_fit_" + str(i),
            "gaus",
            fit_min,
            fit_max
        )

        # Initialize the fit near the identified peak
        resolution_fit.SetParameter(1, peak_position)

        if show_fit:
            spec = ["R+S", "R+S"]
        else:
            spec = ["RS0", "R+S0"]

        if i == 0:
            fit_result = hist.Fit(resolution_fit, spec[0])
        else:
            fit_result = hist.Fit(resolution_fit, spec[1])

        # Extract fitted parameters
        sigma = resolution_fit.GetParameter(2)
        sigma_error = resolution_fit.GetParError(2)
        mean = resolution_fit.GetParameter(1)
        mean_error = resolution_fit.GetParError(1)

        # Calculate energy resolution
        resolution = (2.35 * sigma) / mean
        resolutions.append(resolution)

        # Extract covariance between mean and sigma
        cov = fit_result.GetCovarianceMatrix()
        cov_sigma_mean = cov[2][1]

        # Calculate uncertainty on energy resolution
        term1 = (2.35 / mean)**2 * sigma_error**2
        term2 = (2.35 * sigma / mean**2)**2 * mean_error**2
        term3 = (
            2
            * (2.35 / mean)
            * (-2.35 * sigma / mean**2)
            * cov_sigma_mean
        )

        variance = term1 + term2 + term3
        resolution_error = math.sqrt(max(0.0, variance))
        errors.append(resolution_error)

        # Optional diagnostic output
        print(f"Peak position: {peak_position}")
        print(f"Fit range: {fit_min:.3f} to {fit_max:.3f}")
        print(f"Resolution: {100 * resolution:.3g} %")
        print(f"Resolution error: {100 * resolution_error:.3g} %")

        

    return resolutions, errors



def subtract_background(acq_sgnl, acq_bg, name=None, n_chs=None):
    '''Subtract the background from the signal acquisition and return a
    subtracted histogram'''