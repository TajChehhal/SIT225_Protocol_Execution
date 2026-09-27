import pandas as pd 
import numpy as np 

SESSIONS = ["A", "B", "C", "D"] # Session labels to process
BLOCK_MINUTES = 10 # Aggregation block size in minutes
THRESHOLD_PCT = 0.15 # 15% above baseline = alert band

# Session A had a documented sun-position shift during this window
# Flag it rather than delete 
SESSION_A_CONDITION_CHANGE_START = "2026-09-23T12:13:00" # Start of the sun-drift 
SESSION_A_CONDITION_CHANGE_END = "2026-09-23T13:01:00" # End of the sun-drift 

all_raw_dataframes = [] # Collects raw DataFrames across sessions
all_processed_dataframes = [] # Collects processed DataFrames across sessions

for label in SESSIONS: # Process each session in turn

    # 1. LOAD 
    raw_filename = f"Session_{label}_raw.csv" 
    df = pd.read_csv(raw_filename) # Load this session's raw sensor log
    all_raw_dataframes.append(df.copy())  # Keep a copy for combined_raw.csv

    # 2. VALIDATE / CLEAN 
    df["timestamp"] = pd.to_datetime(df["timestamp"]) # Convert timestamp column to real dates
    df["soil_raw"] = pd.to_numeric(df["soil_raw"], errors="coerce") # Convert to numeric
    df["lux"] = pd.to_numeric(df["lux"], errors="coerce") # Convert to numeric
    df["temp_c"] = pd.to_numeric(df["temp_c"], errors="coerce") # Convert to numeric
    df["humidity_pct"] = pd.to_numeric(df["humidity_pct"], errors="coerce") # Convert to numeric

    
    # For DHT11 giving impossible values, don't delete, instead blank it out instead
    bad_temp = (df["temp_c"] < -10) | (df["temp_c"] > 60) 
    bad_humidity = (df["humidity_pct"] < 0) | (df["humidity_pct"] > 100) 
    n_sensor_errors = int((bad_temp | bad_humidity).sum()) # Count of bad sensor values found
    df.loc[bad_temp, "temp_c"] = np.nan # Null bad temps so they're skipped by .mean()
    df.loc[bad_humidity, "humidity_pct"] = np.nan # Null bad humidity so it's skipped by .mean()

    # 3. FLAG condition-change window, for session A 
    df["condition_change"] = False # Default every row to not flagged
    if label == "A": # Only session A has a documented condition change
        start = pd.Timestamp(SESSION_A_CONDITION_CHANGE_START)
        end = pd.Timestamp(SESSION_A_CONDITION_CHANGE_END)
        in_window = (df["timestamp"] >= start) & (df["timestamp"] <= end) # Rows falling inside the window
        df.loc[in_window, "condition_change"] = True # Flag those rows

    # 4. TRANSFORM: calculate VPD 
    # VPD using the Tetens equation
    saturation_vapour_pressure = 0.6108 * np.exp((17.27 * df["temp_c"]) / (df["temp_c"] + 237.3)) # Saturation vapour pressure
    df["vpd_kpa"] = saturation_vapour_pressure * (1 - df["humidity_pct"] / 100) # Scale by how far humidity is from saturation

    # 5. AGGREGATE into 10-minute blocks 
    df = df.set_index("timestamp") 
    blocks = df.resample(f"{BLOCK_MINUTES}min").mean(numeric_only=True) # Average each numeric column per block
    blocks["condition_change"] = df["condition_change"].resample(f"{BLOCK_MINUTES}min").max() # True if any row in the block was flagged
    blocks = blocks.dropna(subset=["soil_raw"]).reset_index() # Drop empty blocks, turn timestamp back into a column
    blocks["session"] = f"Session_{label}" # Tag each row with its session
    blocks["decline_rate"] = blocks["soil_raw"].diff() # Per-block change in soil moisture

    # 6. BASELINE and THRESHOLD 
    baseline = df["soil_raw"].iloc[0] # The very first reading is the dry baseline
    threshold_upper = baseline * (1 + THRESHOLD_PCT) # Upper bound of the 15%-above-baseline band

    peak_row_number = blocks["soil_raw"].idxmax() # Block with the highest soil_raw, watering peak
    after_peak = blocks.loc[peak_row_number:] # Only look at blocks from the peak onward
    crossed = after_peak[after_peak["soil_raw"] <= threshold_upper] # Blocks that have dropped into the threshold band
    crossing_time = crossed["timestamp"].iloc[0] if len(crossed) > 0 else None # Time of first block if any

    # 7. EXPORT + SUMMARY 
    out_filename = f"Session_{label}_processed.csv" # Build session's output filename
    blocks.to_csv(out_filename, index=False) # Export session's processed data
    all_processed_dataframes.append(blocks) # Add to the cross-session list

    print(f"\n[Session {label}]")
    print(f"  Raw rows: {len(df)}")
    print(f"  Sensor-error readings excluded from VPD: {n_sensor_errors}")
    print(f"  Dry baseline: {baseline:.1f}  |  Threshold (<=): {threshold_upper:.1f}")
    print(f"  Peak soil_raw (block mean): {blocks['soil_raw'].max():.1f}")
    if crossing_time is not None: # Only print if the band was actually reached
        print(f"  Entered threshold band at: {crossing_time}")
    else:
        print("  Did NOT enter threshold band within the session.")
    print(f"  Aggregated blocks: {len(blocks)}  |  Saved to: {out_filename}")

# COMBINE all sessions into the two files  
combined_raw = pd.concat(all_raw_dataframes, ignore_index=True) # Stack all sessions' raw data together
combined_raw.to_csv("combined_raw.csv", index=False)

combined_processed = pd.concat(all_processed_dataframes, ignore_index=True) # Stack all sessions' processed data together
combined_processed.to_csv("combined_processed.csv", index=False)

print(f"\nSaved combined_raw.csv ({len(combined_raw)} rows)")
print(f"Saved combined_processed.csv ({len(combined_processed)} rows)")