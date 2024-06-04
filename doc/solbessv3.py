## Energy bill calculation for solar+bess system

import math

# energy rates
Rs = 2 # Rs/kWh
Rn = 7 # Rs/kWh
alpha = 0.25 # peak premium

Rp = Rn*(1 + alpha) # Rs/kWh


Tp = 8
Pp = 40

Tnd = 8 # day time normal load
Pn = 50

Tnn = 0 # night time normal load

Ts = 7 # solar duration in Chennai avg in a year

eta = 0.9 # round-trip efficiency of BESS

Esp = 4.5 # Energy provided per panel per day, kWh

K = 30000 # cost of BESS, Rs/kWh
dy = 300 # working days in a year

# Daily load
L = Tp*Pp + Tnd*Pn + Tnn*Pn

print(f"Daily load: {L} kWh")

# Energy bill without solar+bess
Bnow = Tp*Pp*Rp + Tnd*Pn*Rn + Tnn*Pn*Rn

print(f"Daily energy bill without solar+bess: Rs. {round(Bnow)}")

# capacity of BESS
C = Tp*Pp/2/eta + Tnn*Pn/eta

# ceil it to the nearest 15 kWh, battery capacity
C = math.ceil(C/15)*15 

print( f"Capacity of BESS: {C} kWh")

# Solar capacity
Csolar = Tp*Pp/2 + (Ts - Tp/2)*Pn + C

print( f"Solar capacity: {Csolar:.3g} kWh")

# Number of solar panels
Nsp = Csolar/Esp

print("Number of solar panels: ", math.ceil(Nsp))

# Daily energy bill
Bv3 = Rs * Csolar
print(f"Daily energy bill with solar+bess: Rs. {round(Bv3)}")

Sv3 = Bnow - Bv3 # savings

print(f"Daily savings: Rs. {round(Sv3)}")

# BESS capital cost
BESScost = K*C
print(f"BESS capital cost: Rs. {round(BESScost/1e5)} lakhs")

# Payback period
Yv3 = K*C/Sv3/dy

print(f"Payback period: {math.ceil(Yv3)} years")





