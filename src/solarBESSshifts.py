import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

# sampling time in hours
Tsamp = 1/60

# BESS parameters
# Capacity of the battery in kWh
Cbess = 215
Rbess = 30000 # Rs./kWh

# C-Rating
Cr = 0.5

# State of Charge (max)
SoCmax = 90

# State of Charge (min6
SoCmin = 10

# Load demand
Plmax = 75 # k2 ma4 contracted load
Tlavg = 55 # kW average load demand

# list of periods when there is a load demand at the average value
Tllist = [(0, 3),
          (6, 16),
          (17,24)]


# Solar parameters
Psmax = 100 # Solar capacity in kW

# Simple quad model (trapezium profile) for solar production
# start time, max start, max end, end 
Tsquad = (9.5, 12, 14, 16.5)

Tsolar = 4.5 # hrs per day
Rsolar = 2 # Rs./ kWh

# Grid slabs
# List of Normal rate periods
Tgnlist = [(10,18)]

Rn = 70 # normal rate of grid, Rs/ 10 Unit



# List of Peak rate periods
Tgplist = [(6, 10), (18, 22)] 
Rp = Rn*1.25

# List of off-peak rate periods
Tgolist = [(0, 6), (22, 24)]
Ro = Rn*0.75




def load_demand(lavg, llist, ts):
    """ Returns a time series of load demand

    Args:
        lavg (float): average load demand
        llist (list): list of periods when the load demand is at the average value
        ts (numpy array): sampling time instances (hours)

    Returns: 
        numpy array: time series of load demand
    """

    Pload = 0*ts # initialise all to zero
    
    for period in llist:
        i = np.where((ts>= period[0]) & (ts<=period[1]))
        Pload[i] = lavg
        
    return Pload


def solar_power(pmax, tsquad, ts):
    """ Returns a time series of solar power production (trapezium profile)

    Args:
        pmax (float): maximum solar power in day
        tsquad (tuple): (solar begin, max start, max end, solar end)
        ts (numpy array): sampling time instances (hours)

    Returns:
        numpy array: time series of solar power production
    """

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

def grid_rates(Tgnlist, Tgplist, Tgolist, Rn, Rp, Ro):
    """ Returns the grid rates

    Args:
        Tgnlist (list): list of Normal rate periods
        Tgplist (list): list of Peak rate periods
        Tgolist (list): list of Off-peak rate periods
        Rn (float): Normal rate of grid cost, Rs/Unit
        Rp (float): Peak rate of grid cost, Rs/Unit
        Ro (float): Off-peak rate of grid cost, Rs/Unit

    Returns:
        numpy array: time series of grid rates
    """

    Rgrid = 0*ts # initialise all to zero

    for period in Tgolist: # off peak
        i = np.where((ts>= period[0]) & (ts<=period[1]))
        Rgrid[i] = Ro

    for period in Tgnlist: # normal
        i = np.where((ts>= period[0]) & (ts<=period[1]))
        Rgrid[i] = Rn

    for period in Tgplist: # peak
        i = np.where((ts>= period[0]) & (ts<=period[1]))
        Rgrid[i] = Rp


    return Rgrid

def isem_control(pload, psolar, plmax, cbess, cr, soc0, socmax, socmin, 
                  tgnlist, tgplist, tgolist, ts):
    """ Returns battery SoC and Grid power used

    Args:
        Pload (numpy array): time series of load demand
        Psolar (numpy array): time series of solar power production
        Plmax (float): Max contracted load
        Cbess (float): Capacity of the battery in kWh
        Cr (float): C-Rating of the battery
        SoC0 (float): initial state of charge
        SoCmax (float): maximum state of charge
        SoCmin (float): minimum state of charge
        Tgnlist (list): list of Normal rate periods
        Tgplist (list): list of Peak rate periods
        Tgolist (list): list of Off-peak rate periods
        Tsamp (float): sampling time instances (hours)

    Returns:
        SoC (numpy array): time series of state of charge
        Grid power (numpy array): time series of grid power in kW
    """

    tsamp = ts[1] - ts[0]

    soct = 0 * ts # initialise all to zero
    pgrid = 0*ts # initialise all to zero

    eps = 1e-3

    for i, t in enumerate(ts):

        if (i==0):
            soc = soc0
            # soc = 25 # 50 kW avg
            # soc = 34 # 50 kW avg
        else:
            soc = soct[i-1]

        # power balance
        pnet = psolar[i] - pload[i]

        if (pnet > eps):  # Solar charging
            # charge/discharge fully in 1/Cr hours
            # print('Solar charging')
            soct[i] = np.min([soc + (100*cr) * tsamp * pnet/(cbess*cr), socmax])
            # Pgrid[i] = 0

        else:
            # Off peak rates, excess grid charging
            for tb,tn in Tgolist:
                if ((t>= tb) and (t<=tn)):
                    # print('Off peak charging')
                    soct[i] = np.min([soc + 100 * tsamp * (plmax+pnet)/cbess, socmax])
                    # note Pnet is negative

            # Normal rates, excess grid charging
            for tb,tn in tgnlist:
                if ((t>= tb) and (t<=tn)):
                    # print('Normal charging')
                    soct[i] = np.min([ soc + 100 * tsamp * (plmax+pnet)/cbess, socmax])

            # Peak rates, discharging
            if (soc >= socmin) : # support load during peak time
                for tb,tn in tgplist:
                    if ((t>= tb) and (t<=tn)):
                        # print('Discharging (at peak)')
                        soct[i] = soc + 100 * tsamp * pnet/cbess
                        soct[i] = np.max([soct[i],socmin])
                        #SoC[i] = SoC[i-1] - (100*Cr) * tsamp 

                # Any time, if the Load requires larger than contracted load, then discharge 
                if (pnet > plmax):
                    # print('Discharging (excess load)')
                    soct[i] = soc + 100 * tsamp * pnet/cbess
                    soct[i] = np.max([soct[i],socmin])

            else:
                print('Battery empty')
                SoC[i] = soc
            

        if (pnet <= eps):
            pgrid[i] = np.max([-pnet + cbess * (soct[i] - soc) / (100 * tsamp), 0])
            # print(f"pgrid[i] = {pgrid[i]}")

        # print(f"t={t}, pnet={pnet}, SoC={soct[i]}")

    return soct,pgrid
                

# sampling times including the end points
ts = np.arange(0, 24+Tsamp, Tsamp)

Pload = load_demand(Tlavg, Tllist, ts)
Psolar = solar_power(Psmax, Tsquad, ts)

Rgrid = grid_rates(Tgnlist, Tgplist, Tgolist, Rn, Rp, Ro)

SoC0 = 50 # initial guess
SoC,Pgrid = isem_control(Pload, Psolar, Plmax, Cbess, Cr, SoC0, SoCmax, SoCmin, Tgnlist, Tgplist, Tgolist, ts)
SoC0 = SoC[-1] # iterate with 24 hr value
SoC,Pgrid = isem_control(Pload, Psolar, Plmax, Cbess, Cr, SoC0, SoCmax, SoCmin, Tgnlist, Tgplist, Tgolist, ts)

# Determine rate of charge/discharge
Crates = np.diff(SoC, append=SoC[0])/Tsamp / 100

## Cost savings

# Current bill
pr = Pload * Rgrid/10
Bnow = Tsamp * (2*sum(pr) - pr[0] - pr[-1])/2
print(f"Bnow = {Bnow}")

# Total solar energy, Area under the curve of Solar power
Esolar = Tsamp * (2*sum(Psolar) - Psolar[0] - Psolar[-1])/2
print(f"Esolar = {Esolar}")

pr = Pgrid * Rgrid/10
Bv1 = Rsolar*Esolar +  Tsamp * (2*sum(pr) - pr[0] - pr[-1])/2

dailySavings = Bnow - Bv1
biMonthlySavings = dailySavings * 26 * 2

print("Bi monthly bill = ", Bnow*2*26)
print(f"Daily Savings = {dailySavings}")
print(f"Bi-Monthly Savings = {biMonthlySavings}")

yony = np.arange(0,15)
yearlySaving = yony * dailySavings * 300


plt.figure()
plt.plot(ts, Pload, label='Load Power', ls='-', color='b')
plt.plot(ts, Psolar, label='Solar Power', ls='-', color='r')
plt.plot(ts, Pgrid, label='Grid Power', ls='-', marker='o', color='k')
plt.plot(ts, Rgrid, label='Grid Cost [Rs/10 kWh]', ls='-', color='m')
plt.plot(ts, SoC, label='SoC', ls='-', marker='o', color='g')


# Add labels and title
plt.xlabel("Time")
plt.ylabel("Power")
plt.title("Demand vs Supply (kW)")
plt.legend()

# ticks
ax1 = plt.gca()
ax1.xaxis.set_minor_locator(mpl.ticker.MultipleLocator(1))

ax2 = ax1.twinx()
ax2.plot(ts, Crates, label='C-Rate', ls='-', color='c')
ax2.set_ylabel("C-Rate")

# adjust the legend to include both axes
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2)


plt.figure()
plt.plot(yony, yearlySaving, label='Yearly Savings', ls='-', marker='o', color='b')

# Display the plot
besscost = np.ones(len(yony))*Cbess*Rbess
plt.plot(yony, besscost, label='BESS Cost', ls='-', color='r')

plt.show()

