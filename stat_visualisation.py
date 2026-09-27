import pandas as pd 
import matplotlib.pyplot as plt
import numpy as np 

df = pd.read_csv('combined_processed.csv') # Loads the combined sensor dataset
df['timestamp'] = pd.to_datetime(df['timestamp']) # Converts timestamp column from text to datetime objects

# Plot 1: soil moisture over time, one line per session 
fig, ax = plt.subplots(figsize=(9,5.5))
for session in df['session'].unique(): # Loop through each session label
    g = df[df['session']==session].sort_values('timestamp').copy() # Isolates this session's rows, ordered by time
    g['elapsed_h'] = (g['timestamp'] - g['timestamp'].iloc[0]).dt.total_seconds()/3600 # Calculate hours since this session's first reading
    ax.plot(g['elapsed_h'], g['soil_raw'], marker='o', label=session) # Plot soil value vs elapsed time for this session

# Axis labels
ax.set_xlabel('Elapsed time since watering (hours)')
ax.set_ylabel('Soil moisture (raw sensor value)')
ax.set_title('Soil Moisture Decline Over Time by Session')
ax.legend() # Show session labels as a legend
plt.savefig('plot1_timeseries.png', dpi=150) # Save the figure to disk



# Plot 2: distribution of decline rates, grouped by light condition
df['condition'] = df['session'].map({'Session_A':'Sun','Session_C':'Sun','Session_B':'Dark','Session_D':'Dark'}) # Tag each session as Sun or Dark
sun_rates = df[df['condition']=='Sun']['decline_rate'].dropna() # Decline rates for sun sessions and drop any missing values
dark_rates = df[df['condition']=='Dark']['decline_rate'].dropna() # Decline rates for dark sessions

fig, ax = plt.subplots(figsize=(8,5))
ax.hist(sun_rates, bins=15, alpha=0.6, label='Sun') # Histogram of sun-condition decline rates
ax.hist(dark_rates, bins=15, alpha=0.6, label='Dark') # Histogram for dark-condition decline rates
ax.set_xlabel('Decline rate (units per 10-min block)')
ax.set_ylabel('Frequency')
ax.legend()
plt.savefig('plot2_distribution.png', dpi=150)



# Plot 3: lux vs decline rate, sun sessions only, with linear fit 
sun = df[df['session'].isin(['Session_A','Session_C'])].dropna(subset=['decline_rate']) # Sun-session rows with a valid decline rate
x, y = sun['lux'].values, sun['decline_rate'].values # Extract lux and decline rate as arrays for fitting
coef = np.polyfit(x, y, 1) # Fit a straight line to the data
x_line = np.linspace(x.min(), x.max(), 100) # Evenly spaced x-values for drawing the fit line

fig, ax = plt.subplots(figsize=(8,5.5))
ax.scatter(x, y, alpha=0.8) # Plot each data point
ax.plot(x_line, coef[0]*x_line + coef[1], 'k--') # Draw the fitted line
r2 = np.corrcoef(x, y)[0,1]**2 # Compute R^2 to find how well the line fits the data
ax.set_title(f'Lux vs Decline Rate (R²={r2:.3f})')
ax.set_xlabel('Lux'); ax.set_ylabel('Decline rate')
plt.savefig('plot3_lux_vs_decline.png', dpi=150) # Save the figure to disk
