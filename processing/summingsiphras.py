import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import pandas as pd
import numpy as np


def match_events(
    file1,
    file2,
    output_path="matched_events.csv",
    tolerance=999
):
    """
    Fast matching of coincident detector events.

    Parameters
    ----------
    file1 : filepath
    file2 : filepath

    output_path : str

    tolerance : int
        Maximum allowed subsecond difference

    Returns
    -------
    matched_df : pandas.DataFrame
    """

    # ==========================================================
    # CREATE FULL TIMESTAMPS
    # ==========================================================

    CLOCK_FREQ = 40000000

    file1 = pd.read_csv(file1).copy()
    file2 = pd.read_csv(file2).copy()

    file1["timestamp"] = (
        file1["Time_sec"] +
        file1["Time_sub"] / CLOCK_FREQ
    )

    file2["timestamp"] = (
        file2["Time_sec"] +
        file2["Time_sub"] / CLOCK_FREQ
    )

    # ==========================================================
    # SORT FOR merge_asof
    # ==========================================================

    file1 = file1.sort_values("timestamp")
    file2 = file2.sort_values("timestamp")

    # ==========================================================
    # CONVERT TOLERANCE
    # ==========================================================

    tolerance_time = tolerance / CLOCK_FREQ

    # ==========================================================
    # MATCH EVENTS
    # ==========================================================

    matched_df = pd.merge_asof(
        file1,
        file2,
        on="timestamp",
        tolerance=tolerance_time,
        direction="nearest",
        suffixes=("_A", "_B")
    )

    # ==========================================================
    # REMOVE UNMATCHED ROWS
    # ==========================================================

    matched_df = matched_df.dropna()

    # ==========================================================
    # COMPUTE SUBSECOND DIFFERENCE
    # ==========================================================

    """matched_df["subsec_difference"] = np.abs(
        matched_df["Time_sub_A"] -
        matched_df["Time_sub_B"]
    )"""

    matched_df["subsec_difference"] = matched_df["Time_sub_A"] - matched_df["Time_sub_B"]

    # ==========================================================
    # COMBINED SUM
    # ==========================================================

    matched_df["Combined_Summed"] = (
        matched_df["Summed_A"] +
        matched_df["Summed_B"]
    )

    # ==========================================================
    # MATCH STATISTICS
    # ==========================================================
    
    n_file1 = len(file1)
    n_file2 = len(file2)
    
    n_matched = len(matched_df)
    
    discarded_file1 = n_file1 - n_matched
    discarded_file2 = n_file2 - n_matched
    
    print("\n========== MATCH RESULTS ==========")
    print(f"Events in file A:     {n_file1}")
    print(f"Events in file B:     {n_file2}")
    print(f"Matched events:       {n_matched}")
    print(f"Discarded from A:     {discarded_file1}")
    print(f"Discarded from B:     {discarded_file2}")
    
    print(f"\nMatch fraction A: {100*n_matched/n_file1:.2f}%")
    print(f"Match fraction B: {100*n_matched/n_file2:.2f}%")

    # ==========================================================
    # SAVE CSV
    # ==========================================================

    matched_df.to_csv(output_path, index=False)

    print(f"Saved {len(matched_df)} matched events")
    print(f"Output file: {output_path}")

    return matched_df

