#!/usr/bin/env python3
# *****************************************************************************
# Description: Plot inter-event timing histogram from a .csv file produced
#              by the acquisition script (--timing flag).
# Usage:       python plot_timing.py time_<run>.csv [options]
# Written by:  Oscar Rosero (KTH)
# *****************************************************************************

import argparse
import csv
import sys
import ROOT


def parse_args():
    parser = argparse.ArgumentParser(
        description="Plot inter-event timing histogram from acquisition CSV."
    )
    parser.add_argument("csv_file",
                        help="Path to the time_<run>.csv file.")
    parser.add_argument("-n", "--nbins", type=int, default=500,
                        help="Number of histogram bins. Default: 500.")
    parser.add_argument("--xmin", type=float, default=None,
                        help="Lower bound of the x-axis (seconds). "
                             "Default: auto (min value in data).")
    parser.add_argument("--xmax", type=float, default=None,
                        help="Upper bound of the x-axis (seconds). "
                             "Default: auto (max value in data).")
    parser.add_argument("--log", action="store_true",
                        help="Draw y-axis in log scale.")
    parser.add_argument("--title", type=str, default=None,
                        help="Histogram title. Default: derived from filename.")
    parser.add_argument("-o", "--output", type=str, default=None,
                        help="Save canvas to file (e.g. timing.png, timing.pdf). "
                             "If not given, the canvas is displayed interactively.")
    return parser.parse_args()


def read_times(csv_file):
    times = []
    with open(csv_file, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            times.append(float(row["time_s"]))
    return times


def main():
    args = parse_args()

    # ── Read data ──────────────────────────────────────────────────────────
    try:
        times = read_times(args.csv_file)
    except FileNotFoundError:
        sys.exit(f"[ERROR] File not found: {args.csv_file}")
    except KeyError:
        sys.exit("[ERROR] CSV does not contain a 'time_s' column.")

    if not times:
        sys.exit("[ERROR] No data found in the file.")

    n_events = len(times)
    t_min    = args.xmin if args.xmin is not None else min(times)
    t_max    = args.xmax if args.xmax is not None else max(times)

    # Add a small margin on the right so the last entry is not cut off
    if t_max == t_min:
        t_max = t_min + 1.0
    t_max *= 1.05

    print(f"  Events read : {n_events}")
    print(f"  t min       : {min(times):.6e} s")
    print(f"  t max       : {max(times):.6e} s")
    print(f"  t mean      : {sum(times)/n_events:.6e} s")

    # ── Build histogram ────────────────────────────────────────────────────
    title = args.title if args.title else f"Inter-event timing  ({args.csv_file})"

    h = ROOT.TH1D("h_timing", title, args.nbins, t_min, t_max)
    h.GetXaxis().SetTitle("t  [s]")
    h.GetYaxis().SetTitle("Counts")

    for t in times:
        h.Fill(t)

    # ── Style ──────────────────────────────────────────────────────────────
    ROOT.gStyle.SetOptStat("nemr")   # show N, mean, RMS in stats box
    ROOT.gStyle.SetOptTitle(1)

    h.SetLineColor(ROOT.kAzure + 1)
    h.SetLineWidth(2)
    h.SetFillColorAlpha(ROOT.kAzure + 1, 0.25)

    # ── Canvas & draw ──────────────────────────────────────────────────────
    c = ROOT.TCanvas("c_timing", "Inter-event timing", 900, 600)
    c.SetLeftMargin(0.12)
    c.SetBottomMargin(0.12)

    if args.log:
        c.SetLogy()

    h.Draw("HIST")

    # Vertical line at the mean
    mean_line = ROOT.TLine(h.GetMean(), 0, h.GetMean(), h.GetMaximum())
    mean_line.SetLineColor(ROOT.kRed)
    mean_line.SetLineWidth(2)
    mean_line.SetLineStyle(2)   # dashed
    mean_line.Draw("SAME")

    # Legend entry for the mean line
    leg = ROOT.TLegend(0.65, 0.72, 0.88, 0.88)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.AddEntry(h,         "Counts",         "f")
    leg.AddEntry(mean_line, f"Mean = {h.GetMean():.3e} s", "l")
    leg.Draw()

    c.Update()

    # ── Output ─────────────────────────────────────────────────────────────
    if args.output:
        c.SaveAs(args.output)
        print(f"\n  Saved to: {args.output}")
    else:
        print("\n  Displaying canvas — close the window to exit.")
        ROOT.gApplication.Run()


if __name__ == "__main__":
    main()
