from construct import BitStruct, BitsInteger, Padding, Flag

# ---------- Bit Structures of SIPHRA registers ----------

# Registers 0x00 - 0x0F: Channel configuration registers
CHANNEL = BitStruct(
    Padding(6),
    'cmis_detector_voffset' / BitsInteger(8),
    'cmis_detector_ioffset' / BitsInteger(3),
    'cmis_impedance_reduction' / BitsInteger(1),
    'cal_select_channel' / Flag,
    'qc_threshold' / BitsInteger(8),
    'qc_hysteresis' / BitsInteger(3),
    'pu_channel' / Flag,
    'enable_triggering' / Flag,
)

# Register 0x10: Summing channel configuration registers
SUM_CHANNEL = BitStruct(
    Padding(18),
    'cal_select_channel' / Flag,
    'qc_threshold' / BitsInteger(8),
    'qc_hysteresis' / BitsInteger(3),
    'pu_channel' / Flag,
    'enable_triggering' / Flag,
)

# Register 0x11: Configuration register - channel_config
CHANNEL_CONFIG = BitStruct(
    Padding(8),
    'cmis_gain' / BitsInteger(3),
    'ci_gain' / BitsInteger(2),
    'ci_compmode' / BitsInteger(1),
    'shaper_bias' / BitsInteger(4),
    'shaper_feedback_cap' / BitsInteger(4),
    'shaper_feedback_res' / BitsInteger(3),
    'shaper_hold_cap' / BitsInteger(3),
    'shaper_input_cap' / BitsInteger(4),
)

# Register 0x12: Configuration register - channel_control
CHANNEL_CONTROL = BitStruct(
    Padding(9),
    'ci_feedback_dac' / BitsInteger(8),
    'ci_use_reset' / BitsInteger(1),
    'th_select_input' / BitsInteger(1),
    'cb_select_input' / BitsInteger(2),
    'ms_select_input' / BitsInteger(1),
    'cc_enable_dcc' / Flag,
    'cc_threshold' / BitsInteger(8),
    'pt_100_enable_excitation' / Flag,
)

# Register 0x13: Configuration register - ADC configuration
ADC_CONFIG = BitStruct(
    Padding(26),
    'analog_readout_mode' / BitsInteger(1),
    'adc_sample_duration' / BitsInteger(4),
    'adc_mode' / BitsInteger(1),
)

# Register 0x14: Gain Calibration Unit, Voltage DAC setting
CAL_DAC = BitStruct(
    Padding(24),
    'cal_dac' / BitsInteger(8),
)

# Register 0x15: Power modules
PD_MODULES = BitStruct(
    Padding(14),
    'pu_sum_cc' / Flag,
    'pu_sum_ci' / Flag,
    'pu_sum_sha' / Flag,
    'pu_sum_th' / Flag,
    'pu_sum_qc' / Flag,
    'pu_sum_cb' / Flag,
    'pu_cmis' / Flag,
    'pu_cc' / Flag,
    'pu_ci_fb_dac' / Flag,
    'pu_ci' / Flag,
    'pu_sha' / Flag,
    'pu_th' / Flag,
    'pu_qc' / Flag,
    'pu_cb' / Flag,
    'pu_trigger_output_enable' / Flag,
    'pu_adc_ref' / Flag,
    'pu_pt100' / Flag,
    'pu_mb' / Flag,
)

# Register 0x16
CAL_CTRL = BitStruct(
    Padding(26),
    'cal_cv_range_low' / Flag,
    'cal_cv_range_mid' / Flag,
    'cal_cv_range_high' / Flag,
    'cal_trigger_select' / Flag,
    'cal_mode' / BitsInteger(2)
)

# Register 0x17
ch_names = [f'CH_{n}_rofl' for n in range(16, 0, -1)]
READOUT_FIXED_LIST = BitStruct(
    Padding(13),
    'ADC_IN_rofl' / Flag,
    'SUM_CH_rofl' / Flag,
    *[name / Flag for name in ch_names],
    'ADC_PT100_SENSE_rofl' / Flag,
)

# Register 0x18
READOUT_MODE = BitStruct(
    Padding(17),
    'int_hold_tune' / BitsInteger(5),
    'int_hold_delay' / BitsInteger(4),
    'int_hold_source' / BitsInteger(2),
    'readout_list_mode' / BitsInteger(1),
    'readout_en_spi_forced_start' / Flag,
    'readout_en_ext_hold_start' / Flag,
    'readout_en_int_hold_start' / Flag,
)

reg_str_lst = [*[CHANNEL]*16,
               SUM_CHANNEL,
               CHANNEL_CONFIG,
               CHANNEL_CONTROL,
               ADC_CONFIG,
               CAL_DAC,
               PD_MODULES,
               CAL_CTRL,
               READOUT_FIXED_LIST,
               READOUT_MODE,
               ]