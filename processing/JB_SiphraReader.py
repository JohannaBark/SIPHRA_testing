
"""SiphraReader.py

PyROOT equivalent of the original C++ SiphraReader.

Usage:
    python3 SiphraReader.py data.txt
    python3 SiphraReader.py data.txt batch

The optional second argument enables batch mode (no GUI event loop).
Output.root is created in the current working directory.
"""

import sys
import os
import csv

import ROOT


def main():

    print()
    print("********************************")
    print("* Welcome to the SiphraReader! *")
    print("********************************")

    # ---------------------------------------------------------
    # Check command-line arguments
    # ---------------------------------------------------------
    if len(sys.argv) < 2:
        print("\nPlease give valid txt file as argument!\n")
        return

    file_path = sys.argv[1]
    file_name = os.path.basename(file_path)

    # More than one argument after the script enables batch mode.
    batch_mode = len(sys.argv) > 2

    if batch_mode:
        ROOT.gROOT.SetBatch(True)

    if not os.path.isfile(file_path):
        print("\nError opening file! Please check target directory!\n")
        return

    print(f"\nProcessing file {file_name}...\n")

    # ---------------------------------------------------------
    # ROOT style and statistics
    # ---------------------------------------------------------
    ROOT.gStyle.SetOptStat(1111)

    # ---------------------------------------------------------
    # Create canvases for the 16 individual channels
    # ---------------------------------------------------------
    spectrum_canvases = []
    for i in range(16):
        canvas = ROOT.TCanvas(
            f"Canvas_{i + 1}",
            f"Channel #{i + 1}",
            50 + 24 * i,
            50 + 24 * i,
            640,
            480,
        )
        canvas.SetLogy()
        spectrum_canvases.append(canvas)

    highest_mean_canvas = ROOT.TCanvas(
        "HighestMean",
        "Highest-mean window",
        24 * 16 + 640 + 100,
        0,
        640,
        480,
    )
    highest_mean_canvas.SetLogy()

    summed_canvas = ROOT.TCanvas(
        "SummedCanvas",
        "Summed-canvas window",
        24 * 16 + 640 + 100,
        510,
        640,
        480,
    )
    summed_canvas.SetLogy()

    # ---------------------------------------------------------
    # Create histograms
    # ---------------------------------------------------------
    channel_spectra = []

    for i in range(16):
        hist = ROOT.TH1F(
            f"Channel_{i + 1}",
            "",
            4096,
            0,
            4095,
        )
        hist.GetXaxis().SetTitle("ADC channel number")
        hist.GetYaxis().SetTitle("Number of counts")
        channel_spectra.append(hist)

    summed_spectrum = ROOT.TH1F(
        "SIPHRA summing channel spectrum",
        "",
        512,
        0,
        4 * 4095,
    )
    summed_spectrum.GetXaxis().SetTitle("ADC channel number")
    summed_spectrum.GetYaxis().SetTitle("Number of counts")

    manual_sum_spectrum = ROOT.TH1F(
        "Manual sum",
        "",
        512,
        0,
        4 * 4095,
    )
    manual_sum_spectrum.GetXaxis().SetTitle("ADC channel number")
    manual_sum_spectrum.GetYaxis().SetTitle("Number of counts")

    # ---------------------------------------------------------
    # Read input file
    # ---------------------------------------------------------
    lines_read = 0

    try:
        with open(file_path, "r", encoding="latin-1", newline="") as data_file:
            # Skip the header line
            next(data_file, None)

            reader = csv.reader(data_file)

            for line_number, row in enumerate(reader, start=2):

                # Skip empty lines.
                if not row or not any(item.strip() for item in row):
                    continue

                # Expected fields:
                # 0-6: metadata
                # 7-22: 16 channel values
                # 23: SIPHRA summing channel
                # 24: ArgMax
                # 25: Manually calculated sum
                if len(row) < 26:
                    print(
                        f"Warning: skipping line {line_number}: "
                        f"expected 26 columns, got {len(row)}."
                    )
                    continue

                try:
                    values = [float(item.strip()) for item in row[:26]]
                except ValueError:
                    print(
                        f"Warning: skipping line {line_number}: "
                        "contains a non-integer value."
                    )
                    continue

                # Metadata fields, retained for compatibility.
                data_detector = values[0]
                data_id = values[1]
                data_trigger = values[2]
                data_time_sub = values[3]
                data_time_sec = values[4]
                data_time_gps = values[5]
                data_temp = values[6]

                # The 16 ADC channel values.
                data_channels = values[7:23]

                data_siphra_sum = values[23]
                data_argmax = values[24]
                data_manual_sum = values[25]

                # Fill each channel histogram.
                for i, channel_value in enumerate(data_channels):
                    channel_spectra[i].Fill(channel_value)

                # Fill the SIPHRA-reported sum.
                summed_spectrum.Fill(data_siphra_sum)

                # Calculate and fill the manual sum.
                manual_sum = sum(data_channels)
                manual_sum_spectrum.Fill(data_manual_sum)

                lines_read += 1

    except OSError as error:
        print(f"\nError opening or reading file: {error}\n")
        return

    # ---------------------------------------------------------
    # Find channel with the highest mean
    # ---------------------------------------------------------
    channel_with_highest_mean = 0
    highest_mean_found = 0.0

    print()

    for i, hist in enumerate(channel_spectra):

        spectrum_canvases[i].cd()
        hist.Draw()
        spectrum_canvases[i].Modified()
        spectrum_canvases[i].Update()

        current_channel_mean = hist.GetMean()

        print(
            f"Mean in channel {i + 1} ==> "
            f"{current_channel_mean}"
        )

        if current_channel_mean > highest_mean_found:
            channel_with_highest_mean = i
            highest_mean_found = current_channel_mean

    print()
    print(
        f"Highest mean in channel "
        f"#{channel_with_highest_mean + 1}"
    )
    print()

    # ---------------------------------------------------------
    # Draw the highest-mean channel
    # ---------------------------------------------------------
    highest_mean_canvas.cd()

    channel_spectra[channel_with_highest_mean].Draw()

    highest_spectrum_draw_copy = channel_spectra[
        channel_with_highest_mean
    ].Clone(
        f"Highest_channel_{channel_with_highest_mean + 1}"
    )

    # ---------------------------------------------------------
    # Draw the summed spectra together
    # ---------------------------------------------------------
    summed_canvas.cd()

    summed_spectrum.SetLineColor(ROOT.kRed)
    manual_sum_spectrum.SetLineColor(ROOT.kGreen)

    # Draw the histogram with the larger maximum first.
    if (
        summed_spectrum.GetMaximum()
        > manual_sum_spectrum.GetMaximum()
    ):
        summed_spectrum.Draw()
        manual_sum_spectrum.Draw("SAME")
    else:
        manual_sum_spectrum.Draw()
        summed_spectrum.Draw("SAME")

    highest_spectrum_draw_copy.SetLineColor(ROOT.kBlue)
    highest_spectrum_draw_copy.Draw("SAME")

    # ---------------------------------------------------------
    # Save the SIPHRA summed spectrum to Output.root
    # ---------------------------------------------------------
    output_file = ROOT.TFile.Open("Output.root", "RECREATE")

    if not output_file or output_file.IsZombie():
        print("Error creating Output.root!")
        return

    output_file.cd()
    summed_spectrum.Write("Spectrum")
    output_file.Close()

    print("Saved summed spectrum to Output.root")

    # ---------------------------------------------------------
    # Legend
    # ---------------------------------------------------------
    legend = ROOT.TLegend(0.40, 0.59, 0.77, 0.79)

    legend.AddEntry(summed_spectrum, "SIPHRA sum", "l")
    legend.AddEntry(manual_sum_spectrum, "Manual sum", "l")
    legend.AddEntry(
        highest_spectrum_draw_copy,
        f"Highest channel (#{channel_with_highest_mean + 1})",
        "l",
    )

    legend.Draw()

    # ---------------------------------------------------------
    # Position and color statistics boxes
    # ---------------------------------------------------------
    summed_canvas.Modified()
    summed_canvas.Update()

    stats_summed = summed_spectrum.FindObject("stats")
    stats_manual = manual_sum_spectrum.FindObject("stats")
    stats_highest = highest_spectrum_draw_copy.FindObject("stats")

    if stats_summed:
        stats_summed.SetTextColor(ROOT.kRed)

    if stats_manual:
        stats_manual.SetTextColor(ROOT.kGreen)
        stats_manual.SetY1NDC(0.615)
        stats_manual.SetY2NDC(0.765)

    if stats_highest:
        stats_highest.SetTextColor(ROOT.kBlue)
        stats_highest.SetY1NDC(0.455)
        stats_highest.SetY2NDC(0.615)

    summed_canvas.Modified()
    summed_canvas.Update()

    # ---------------------------------------------------------
    # Final information
    # ---------------------------------------------------------
    print(f"Lines read: {lines_read}")
    print()

    # Keep the canvases open unless batch mode was requested.
    if not batch_mode:
        ROOT.gApplication.Run(True)


if __name__ == "__main__":
    main()