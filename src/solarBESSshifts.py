import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt


# sampling time in hours
Tsamp = 1/12
Rn = 7 # normal rate of grid cost, Rs/Unit

# Load demand
Tlavg = 50 # kW average load demand
# list of periods when there is a load demand at the average value
Tllist = [(0, 3),
          (6, 16),
          (17,24)]

# Solar parameters
Pmax = 100 # Solar capacity in kW

# Simple quad model (trapezium profile) for solar production
# start time, max start, max end, end 
Tsquad = (7, 10, 15, 18)

# Grid slabs
# List of Normal rate periods
Tgnlist = [(10,18)]

# List of Peak rate periods
Tgplist = [(6, 10), (18, 22)] 
Rp = Rn*1.25

# List of off-peak rate periods
Tgnlist = [(0, 6), (22, 24)]
Ro = Rn*0.75



def solar_power(pmax, tsquad, ts):
   # return the solar power production by the simple quad 
   # (trapezium profile) model
   # tsquad = (begin, max start, max end, end)
   # pmax is the maximum solar power in day
   # ts is the sampled time instances when power has to be found

   # from the time series initialise to no production (night)
   Psolar = 0*ts # initialise all to zero

   # ramp up production
   i = np.where((ts>= tsquad[0]) & (ts<=tsquad[1]))
   dt = tsquad[1]-tsquad[0]
   Psolar[i] = pmax/dt * (ts[i] - tsquad[0])

   # sustain at maximum power
   i = np.where((ts>= tsquad[1]) & (ts<=tsquad[2]))
   Psolar[i] = pmax
   
   # wind down production
   i = np.where((ts>= tsquad[2]) & (ts<=tsquad[3]))
   dt = tsquad[3]-tsquad[2]
   Psolar[i] = pmax - pmax/dt * (ts[i] - tsquad[2])

   return Psolar



# sampling times including the end points
ts = np.arange(0, 24+Tsamp, Tsamp)

Psolar = solar_power(Pmax, Tsquad, ts)

#plt.plot(ts, Psolar, label='Solar Power', ls='-', marker='o', color='r')
plt.plot(ts, Psolar, label='Solar Power', ls='-', color='r')


# Add labels and title
plt.xlabel("Time")
plt.ylabel("Power")
plt.title("Solar Power Production (kW)")

# ticks
ax = plt.gca()
ax.xaxis.set_minor_locator(mpl.ticker.MultipleLocator(1))


# Display the plot
plt.show()