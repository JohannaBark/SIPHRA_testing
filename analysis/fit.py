# *****************************************************************************
#   Description: A set of utilities to ease SIPHRA spectra analysis.
#   Implements PyROOT dependencies.
#   Written by: Oscar Rosero (KTH)
#....
#   Date: 02/2026

import ROOT
import numpy as np

def gauspeak(n_init: int):
    return f"[{n_init}]*TMath::Gaus(x, [{n_init+1}], [{n_init+2}])"

def bg_exp(n_init: int):
    return f"TMath::Exp([{n_init}] + [{n_init+1}]*x)"

def peak_and_bg():
    return f"{bg_exp(0)}+{gauspeak(2)}"


def estimate_exp_params(hist, xl, xr, peak_margin=0.15):
    """
    Estimates the parameters of the exponential using the range bounds,
    avoiding the peak region.
    """
    margin = (xr - xl) * peak_margin

    x1 = xl + margin
    x2 = xr - margin

    y1 = hist.GetBinContent(hist.FindBin(x1))
    y2 = hist.GetBinContent(hist.FindBin(x2))

    # with exp(a + b*x): solve the 2-equation system
    # ln(y1) = a + b*x1
    # ln(y2) = a + b*x2
    if y1 <= 0 or y2 <= 0:
        return 0, -0.01  # fallback

    b = (np.log(y2) - np.log(y1)) / (x2 - x1)
    a = np.log(y1) - b * x1

    return a, b

def fit_peak_expbg(hist: ROOT.TF1,
                   name: str,
                   xl: float, xr: float,
                   norm: float, mean: float, sigma: float,
                   showFit: bool =False, keep_prev_fncs: bool =True):
    '''
    Fits a gaussian peak in a part of a spectrum assuming exponentially decaying background.
    Parameters
    ----------
    hist : ROOT.TH1F
        Histogram of spectrum
    name : str
        Name for the fit function
    xl, xr : float
        Lower and upper limits of the section of the spectrum to be fitted
    norm, mean, sigma : float
        Parameters of the gaussian [norm]*TMmath::Gauss(x, [mean], [sigma])
    const, decay : float
        Parameters of the exponentially decaying background TMmath::Exp([const] + x*[decay])
    showFit : bool
        If false the fit will be executed in silent mode, so the fit function is not displayed
    keep_prev_fncs : bool
        If true the new fit function is added to the list of functions, otherwise it overwrites previous ones.
    '''
    # if not const or not decay:
    const, decay = estimate_exp_params(hist, xl, xr)

    fit_fn = ROOT.TF1(name, peak_and_bg(), xl, xr, 5)
    fit_fn.SetParNames("Const", "Decay", "Norm", "Mean", "Sigma")
    fit_fn.SetParameters(const, decay, norm, mean, sigma)

    options = "L S" if showFit else "0 S"
    options += " +" if keep_prev_fncs else ""
    fit_result = hist.Fit(fit_fn, options, "", xl, xr)
    return fit_fn, fit_result