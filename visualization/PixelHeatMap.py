
def SiPM_percentage_of_total(filepath, siphra, adc_min=False, adc_max=False):

    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import seaborn as sns

    # Read CSV
    file = pd.read_csv(filepath)

    channels = [f"Ch{i}" for i in range(1, 17)]

    data = file[channels]
    total_adc = file["Summed"]

    # Filter events within ADC interval
    if adc_max and adc_min:
        filtered_data = data[
            (total_adc >= adc_min) &
            (total_adc <= adc_max)
        ].copy()

        filtered_total = total_adc[
            (total_adc >= adc_min) &
            (total_adc <= adc_max)
        ]
    else:
        filtered_data = data.copy()
        filtered_total = total_adc

    # Avoid division by zero
    filtered_total = filtered_total.replace(0, np.nan)

    # Calculate percentage contribution for every event
    # Each row becomes:
    # channel_value / summed_value * 100
    percentage_contribution = (
        filtered_data.div(filtered_total, axis=0)
    ) * 100

    # Average percentage contribution per channel
    avg_percentage = percentage_contribution.mean(axis=0)

    # Mapping channel -> pixel
    channel_to_pixel = {
        "Ch1": "C1",
        "Ch2": "D1",
        "Ch3": "D2",
        "Ch4": "C2",
        "Ch5": "C3",
        "Ch6": "D3",
        "Ch7": "D4",
        "Ch8": "C4",
        "Ch9": "B4",
        "Ch10": "A4",
        "Ch11": "A3",
        "Ch12": "B3",
        "Ch13": "B2",
        "Ch14": "A2",
        "Ch15": "A1",
        "Ch16": "B1",
    }

    # Empty 4x4 matrix
    heatmap_data = np.zeros((4, 4))

    col_map = {"A": 0, "B": 1, "C": 2, "D": 3}

    # Fill matrix
    for ch, perc in avg_percentage.items():

        pixel = channel_to_pixel[ch]

        col_letter = pixel[0]
        row_number = int(pixel[1])

        row_idx = row_number - 1
        col_idx = col_map[col_letter]

        heatmap_data[row_idx, col_idx] = perc

    # Pixel labels
    labels = np.array([
        ["Ch15", "Ch16", "Ch1", "Ch2"],
        ["Ch14", "Ch13", "Ch4", "Ch3"],
        ["Ch11", "Ch12", "Ch5", "Ch6"],
        ["Ch10", "Ch9", "Ch8", "Ch7"],
    ])



    # Plot
    plt.figure(figsize=(7, 6))

    ax = sns.heatmap(
        heatmap_data,
        annot=True,
        fmt=".2f",
        cmap="hot",
        vmin=2,
        vmax=10,
        cbar_kws={
            "label": "Average contribution to total signal (%)"
        }
    )

    # Add pixel labels
    for i in range(4):
        for j in range(4):
            ax.text(
                j + 0.5,
                i + 0.2,
                labels[i, j],
                ha="center",
                va="center",
                color="cyan",
                fontsize=9,
                fontweight="bold"
            )

    plt.title(
        f"Average percentage contribution per SiPM pixel in photopeak,\n"
        f"Detector {siphra}"
    )

    plt.tight_layout()
    plt.show()


if __name__ == '__main__':

    adc_min = 100*16
    adc_max = 200*16



    SiPM_percentage_of_total(
        '../data/260603/A30_DoubleSiphra_Cs137OnCrystalNearCenter_5e6events.csv',
        'A',
        adc_min=350*16,
        adc_max=550*16
    )

    SiPM_percentage_of_total(
        '../data/260603/B30_DoubleSiphra_Cs137OnCrystalNearCenter_5e6events.csv',
        'B',
        adc_min=200*16,
        adc_max=525*16
    )
