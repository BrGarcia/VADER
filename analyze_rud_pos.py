import pandas as pd
import numpy as np
import sys

file_path = "Arquivos_para_analise/5956/VADR/05-19-26-09-21-33_RS6158_Mishap Time History Data Set.csv"

# Load the file, skipping the first 8 rows of metadata
df = pd.read_csv(file_path, skiprows=8, low_memory=False)

# Remove the unit row (it's the second row in the original file, now the first row in df)
df = df.iloc[1:].reset_index(drop=True)

# Convert TIME to seconds
def time_to_seconds(t):
    try:
        if pd.isna(t) or t == "": return None
        if not isinstance(t, str): return None
        parts = t.split(':')
        if len(parts) != 3: return None
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    except:
        return None

df['TIME_SEC'] = df['TIME'].apply(time_to_seconds)

# Forward fill to handle different sampling rates
df = df.ffill()

# Filter for the requested time range [500, 510]
df_window = df[(df['TIME_SEC'] >= 500) & (df['TIME_SEC'] <= 510)].copy()

if df_window.empty:
    print("No data found in the time range [500, 510]")
    # Check what the actual time range is
    print(f"Time range in file: {df['TIME_SEC'].min()} to {df['TIME_SEC'].max()}")
    sys.exit(0)

# Convert all columns to numeric where possible
numeric_cols = []
for col in df_window.columns:
    if col not in ['TIME', 'TIME_SEC', 'STIME']:
        df_window[col] = pd.to_numeric(df_window[col], errors='coerce')
        if not df_window[col].isna().all():
            numeric_cols.append(col)

# Keep only numeric columns with variance
df_numeric = df_window[numeric_cols].copy()
df_numeric = df_numeric.loc[:, df_numeric.std() > 0]

if 'RUD_POS' not in df_numeric.columns:
    print("RUD_POS column not found or has no variance in the specified window.")
    if 'RUD_POS' in df_window.columns:
        print(f"RUD_POS values: {df_window['RUD_POS'].unique()}")
    sys.exit(0)

# Calculate correlations with RUD_POS
correlations = df_numeric.corr()['RUD_POS'].sort_values(ascending=False)

print("Top 15 Positively Correlated Variables with RUD_POS:")
print(correlations.head(16))

print("\nTop 15 Negatively Correlated Variables with RUD_POS:")
print(correlations.tail(15))

# RUD_POS stats
print(f"\nRUD_POS stats in window: mean={df_numeric['RUD_POS'].mean():.4f}, std={df_numeric['RUD_POS'].std():.4f}, min={df_numeric['RUD_POS'].min():.4f}, max={df_numeric['RUD_POS'].max():.4f}")

# Calculate Total Absolute Variation (roughness)
roughness = (df_numeric.diff().abs().sum() / df_numeric.std()).sort_values(ascending=False)

print("\nTop 15 Most 'Rough' Variables (Total Variation / Std):")
print(roughness.head(15))

# Also check correlation of absolute differences (captures simultaneous changes/oscillation)
diff_corr = df_numeric.diff().corr()['RUD_POS'].sort_values(ascending=False)
print("\nTop 15 Variables with Correlated Changes (diff) with RUD_POS:")
print(diff_corr.head(16))
print("\nTop 15 Variables with Inversely Correlated Changes (diff) with RUD_POS:")
print(diff_corr.tail(15))

# Print a sample of the data to see the oscillation pattern
print("\nSample Data (around 505s):")
cols_to_show = ['TIME_SEC', 'RUD_POS', 'AIL_POS', 'MAG_HDG', 'NY', 'AYR']
sample = df_window[(df_window['TIME_SEC'] >= 504) & (df_window['TIME_SEC'] <= 506)][cols_to_show]
print(sample.head(20))

# Calculate cross-correlation with lag to see if one leads the other
def crosscorr(datax, datay, lag=0):
    return datax.corr(datay.shift(lag))

lags = range(-20, 21)
rs = [crosscorr(df_window['RUD_POS'], df_window['AIL_POS'], lag) for lag in lags]
max_r_idx = np.argmax(np.abs(rs))
print(f"\nMax cross-correlation between RUD_POS and AIL_POS: {rs[max_r_idx]:.4f} at lag {lags[max_r_idx]}")

rs_hdg = [crosscorr(df_window['RUD_POS'], df_window['MAG_HDG'], lag) for lag in lags]
max_r_hdg_idx = np.argmax(np.abs(rs_hdg))
print(f"Max cross-correlation between RUD_POS and MAG_HDG: {rs_hdg[max_r_hdg_idx]:.4f} at lag {lags[max_r_hdg_idx]}")

# Check AOA and NY stats
print(f"\nAOA correlation: {correlations.get('AOA')}")
print(f"AOA roughness: {roughness.get('AOA')}")
print(f"NY roughness: {roughness.get('NY')}")
print(f"NZ roughness: {roughness.get('NZ')}")

# Check if there is any 'AP' (Autopilot) engaged signal
ap_cols = [col for col in df.columns if 'AP' in col or 'AUTO' in col or 'MODE' in col]
print(f"\nPotential Autopilot/Mode columns: {ap_cols}")
for col in ap_cols:
    if col in df_window.columns:
        unique_vals = df_window[col].unique()
        if len(unique_vals) > 1:
            print(f"{col} unique values in window: {unique_vals}")
