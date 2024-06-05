import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt


# sampling time in hours
Tsamp = 1/12
Rn = 70 # normal rate of grid cost, Rs/Unit

# Load demand
Tlavg = 50 # kW average load demand
# list of periods when there is a load demand at the average value
Tllist = [(0, 3),
          (6.5, 16),
          (17,24)]

# Solar parameters
Pmax = 100 # Solar capacity in kW

# Simple quad model (trapezium profile) for solar production
# start time, max start, max end, end 
Tsquad = (7, 10, 15, 18.5)

# Grid slabs
# List of Normal rate periods
Tgnlist = [(10,18)]

# List of Peak rate periods
Tgplist = [(6, 10), (18, 22)] 
Rp = Rn*1.25

# List of off-peak rate periods
Tgolist = [(0, 6), (22, 24)]
Ro = Rn*0.75

# BESS parameters
# Capacity of the battery in kWh
Cbess = 200

# C-Rating
Cr = 0.5

# State of Charge (max)
SoCmax = 100

# State of Charge (min)
SoCmin = 0



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
        tsquad (tuple): (begin, max start, max end, end)
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

def battery_state(Pload, Psolar, Cr, SoCmax, SoCmin, 
                  Tgnlist, Tgplist, Tgolist, ts):
    """ Returns battery SoC and Grid power used

    Args:
        Pload (numpy array): time series of load demand
        Psolar (numpy array): time series of solar power production
        Cr (float): C-Rating of the battery
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

        #Cbess (float): Capacity of the battery in kWh
    Cbess = 215
    SoC = 0 * ts # initialise all to zero
    Pgrid = 0*ts # initialise all to zero

    eps = 1e-3

    for i, t in enumerate(ts):

        if (i==0):
            soc = SoCmax
        else:
            soc = SoC[i-1]

        # power balance
        Pnet = Psolar[i] - Pload[i]

        if (Pnet > eps):  # Solar charging
            # charge/discharge fully in 1/Cr hours
            print('Solar charging')
            SoC[i] = np.min([soc + (100*Cr) * tsamp, SoCmax])

        else:
            # Off peak rates, grid charging
            for tb,tn in Tgolist:
                if ((t>= tb) and (t<=tn)):
                    print('Off peak charging')
                    SoC[i] = np.min([soc + (100*Cr) * tsamp, SoCmax])

            # Normal rates, grid charging
            for tb,tn in Tgnlist:
                if ((t>= tb) and (t<=tn)):
                    print('Normal charging')
                    SoC[i] = np.min([ soc + (100*Cr) * tsamp, SoCmax])

            # Peak rates, grid discharging
            if (soc >= SoCmin) : # support load during peak time
                for tb,tn in Tgplist:
                    if ((t>= tb) and (t<=tn)):
                        print('Discharging')
                        SoC[i] = soc + (100*Cr) * Tsamp * Pnet/(Cbess*Cr)
                        SoC[i] = np.max([SoC[i],SoCmin])
                        #SoC[i] = SoC[i-1] - (100*Cr) * tsamp 
            else:
                print('Battery empty')
                SoC[i] = SoC[i-1]

        print(f"t={t}, Pnet={Pnet}, SoC={SoC[i]}")

    return SoC
                

# sampling times including the end points
ts = np.arange(0, 24+Tsamp, Tsamp)

Pload = load_demand(Tlavg, Tllist, ts)
Psolar = solar_power(Pmax, Tsquad, ts)

Rgrid = grid_rates(Tgnlist, Tgplist, Tgolist, Rn, Rp, Ro)

SoC = battery_state(Pload, Psolar, Cr, SoCmax, SoCmin, Tgnlist, Tgplist, Tgolist, ts)


plt.plot(ts, Pload, label='Load Power', ls='-', color='b')
plt.plot(ts, Psolar, label='Solar Power', ls='-', color='r')
plt.plot(ts, Rgrid, label='Grid Rate', ls='-', color='m')
plt.plot(ts, SoC, label='SoC', ls='-', marker='o', color='g')

#plt.plot(ts, Psolar, label='Solar Power', ls='-', marker='o', color='r')


# Add labels and title
plt.xlabel("Time")
plt.ylabel("Power")
plt.title("Demand vs Supply (kW)")

# ticks
ax = plt.gca()
ax.xaxis.set_minor_locator(mpl.ticker.MultipleLocator(1))


# Display the plot
plt.legend()
plt.show()