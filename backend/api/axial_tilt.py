# axial tilt imports
# from sun import sunPosition
# from rotational_angle import optimal_rotational_angle
import numpy as np
import serial
import serial.tools.list_ports
import time
from datetime import datetime, timedelta, date
from django.http import JsonResponse
import json


# sun position imports
import math
import numpy as np
from matplotlib import pyplot as plt
import matplotlib.cm as cm
import pandas as pd

# from sun import sunPosition
import numpy as np
from datetime import datetime, timedelta
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

def find_inc_ang(beta, panel_az, el, az):

    beta = np.radians(beta)
    panel_az = np.radians(panel_az)
    zen = np.radians(90 - el)
    azrad = np.radians(az)

    arg = np.cos(beta)*np.cos(zen) + \
        np.sin(beta)*np.sin(zen)*np.cos(azrad-panel_az)
    deg = np.degrees(np.arccos(arg))

    # max value is 90, means output is zero
    if deg > 90:
        deg = 90

    return deg


def tilt_angle_req(request):
    global time_zone, latitude, longitude, start_date, duration, opt_tilt_angle, opt_date
    if request.method == 'POST':
        content_type = request.content_type

        if content_type == 'application/json':
            print("yes")
            # Handle JSON data
            try:
                json_data = json.loads(request.body)
                time_zone = json_data.get('timeZone')
                latitude = json_data.get('latitude')
                longitude = json_data.get('longitude')
                start_date_str = json_data.get('startDate')
                duration = json_data.get('duration')

                # Convert start_date_str to datetime object
                start_date = datetime.strptime(
                    start_date_str, '%Y-%m-%d').date()

                # Perform calculations or call desired functions
                # Example: Call the tilt_angle function with the received parameters
                opt_tilt_angle, opt_date = tilt_angle(time_zone, latitude,
                                    longitude, start_date, duration)

                return JsonResponse({'result': opt_tilt_angle})

            except json.JSONDecodeError:
                # Handle JSON decoding error
                return JsonResponse({'error': 'Invalid JSON format'}, status=400)

    # Return an error response for unsupported HTTP methods
    return JsonResponse({'error': 'Invalid request method'})


def tilt_angle(time_zone, latitude, longitude, start_date, duration):
    # if len(start_date.split("/")) != 3: #TODO: might need to put this to the backend file
    # print("Error: Invalid start date")
    # return

    time_zone = int(time_zone)
    latitude = float(latitude)
    longitude = float(longitude)
    duration = int(duration)

    # [start_month, start_day, start_year] = start_date.split("-")
    start_month = int(start_date.month)
    start_day = int(start_date.day)
    start_year = int(start_date.year)

    start_date = datetime(start_year, start_month, start_day)

    # Use the optimal tile angle calculated on start_date + duration/2
    opt_date = start_date + timedelta(days=int(duration/2))

    year = opt_date.year
    month = opt_date.month
    day = opt_date.day

    pos = sunPosition(year, month, day, 12+time_zone,
                      0, lat=latitude, long=longitude)
    beta_list = np.arange(0.0, 90.0, 0.5)
    current_inc_ang = 90
    for beta in beta_list:
        inc_ang = find_inc_ang(beta, 180, pos[1], pos[0])
        if inc_ang < current_inc_ang:
            opt_tilt_angle = beta
            current_inc_ang = inc_ang

    return opt_tilt_angle, opt_date


def save_info(ser, time_zone, latitude, longitude, opt_date, opt_tilt_angle):
    file_name = "power_captured.csv"
    daylight_start_min, fitted_m, fitted_b = optimal_rotational_angle(opt_date, opt_tilt_angle, time_zone, latitude, longitude)

    fitted_m = round(fitted_m, 3)
    fitted_b = round(fitted_b, 3)

    start_time = str(datetime.now().strftime("%m-%d-%Y-%H-%M-%S"))
    ser.write(start_time.encode('utf-8'))
    ser.write(b'\n')
    ser.write(str(time_zone).encode('utf-8'))
    ser.write(b'\n')
    ser.write(str(latitude).encode('utf-8'))
    ser.write(b'\n')
    ser.write(str(longitude).encode('utf-8'))
    ser.write(b'\n')
    ser.write(str(opt_tilt_angle).encode('utf-8'))
    ser.write(b'\n')
    ser.write(str(daylight_start_min).encode('utf-8'))
    ser.write(b'\n')
    ser.write(str(fitted_m).encode('utf-8'))
    ser.write(b'\n')
    ser.write(str(fitted_b).encode('utf-8'))
    ser.write(b'\n')

    file = open(file_name, 'a')
    while(1): # get power data from arduino
        getData=ser.readline()
        power_string = getData.decode('utf-8')[:-2]
        file.write(power_string) # current time, voltage, current, power
        file.write('\n')
        print(power_string)


def accelerometerHorz(ser):
    getData=ser.readline()
    horizontal_angle = float(getData.decode('utf-8')[:-2])
    return horizontal_angle


def accelerometer(ser, horizontal_angle):
    while(True):
        getData=ser.readline()
        absolute_tilt = float(getData.decode('utf-8')[:-2])
        actual_tilt = (absolute_tilt - horizontal_angle + 180) % 360 - 180
        yield actual_tilt


# def call_accelerometer(request):
#     print(request)
#     # before pressing start button
#     horizontal_angle = await accelerometerHorz()
#     # press start button
#     # actual_tilt = accelerometer() - horizontal_angle
#     # print(actual_tilt)
#     return JsonResponse({'horizontal_angle': horizontal_angle})

# sun position stuff
def sunPosition(year, month, day, hour=12, m=0, s=0, lat=43.5, long=-80.5):
    twopi = 2 * math.pi
    deg2rad = math.pi / 180

    # Get day of the year, e.g. Feb 1 = 32, Mar 1 = 61 on leap years
    len_month = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30]
    day = day + np.cumsum(len_month)[month-1]
    leapdays = (year % 4 == 0 and (year % 400 == 0 | year % 100 != 0)
                and day >= 60 and not (month == 2 and day == 60))
    day += int(leapdays == True)

    # Get Julian date - 2400000
    hour = hour + m / 60 + s / 3600  # hour plus fraction
    delta = year - 1949
    leap = math.floor(delta / 4)  # former leapyears
    jd = 32916.5 + delta * 365 + leap + day + hour / 24

    # The input to the Atronomer's almanach is the difference between
    # the Julian date and JD 2451545.0 (noon, 1 January 2000)
    time = jd - 51545.

    # Ecliptic coordinates

    # Mean longitude
    mnlong = 280.460 + .9856474 * time
    mnlong = mnlong % 360
    mnlong += int(mnlong < 0)*360

    # Mean anomaly
    mnanom = 357.528 + .9856003 * time
    mnanom = mnanom % 360
    mnanom += int(mnanom < 0)*360
    mnanom = mnanom * deg2rad

    # Ecliptic longitude and obliquity of ecliptic
    eclong = mnlong + 1.915 * math.sin(mnanom) + 0.020 * math.sin(2 * mnanom)
    eclong = eclong % 360
    eclong += int(eclong < 0)*360
    oblqec = 23.439 - 0.0000004 * time
    eclong = eclong * deg2rad
    oblqec = oblqec * deg2rad

    # Celestial coordinates
    # Right ascension and declination
    num = math.cos(oblqec) * math.sin(eclong)
    den = math.cos(eclong)
    ra = math.atan(num / den)
    ra += int(den < 0)*math.pi
    ra += int(den >= 0 and num < 0)*twopi
    dec = math.asin(math.sin(oblqec) * math.sin(eclong))

    # Local coordinates
    # Greenwich mean sidereal time
    gmst = 6.697375 + .0657098242 * time + hour
    gmst = gmst % 24
    gmst += int(gmst < 0)*24

    # Local mean sidereal time
    lmst = (gmst + long / 15.)
    lmst = lmst % 24.
    lmst += int(lmst < 0)*24.
    lmst = lmst * 15. * deg2rad

    # Hour angle
    ha = lmst - ra
    ha += int(ha < -math.pi)*twopi
    ha -= int(ha > math.pi)*twopi

    # Latitude to radians
    lat = lat * deg2rad

    # Azimuth and elevation
    el = math.asin(math.sin(dec) * math.sin(lat) +
                   math.cos(dec) * math.cos(lat) * math.cos(ha))
    az = math.asin(-math.cos(dec) * math.sin(ha) / math.cos(el))

    # For logic and names, see Spencer, J.W. 1989. Solar Energy. 42(4):353
    cosAzPos = (0 <= math.sin(dec) - math.sin(el) * math.sin(lat))
    sinAzNeg = (math.sin(az) < 0)
    az += int(cosAzPos and sinAzNeg)*twopi
    if (not cosAzPos):
        az = math.pi - az

    el = el / deg2rad
    az = az / deg2rad
    lat = lat / deg2rad

    return az, el


def line_best_fit(R):
    # Define the function you want to fit (linear function: y = mx + b)
    def linear_function(x, m, b):
        return m * x + b

    # Create the x values corresponding to the R array indices
    x = np.arange(len(R))

    # Perform curve fitting
    fit_params, _ = curve_fit(linear_function, x, R)

    # Extract the fitted parameters
    fitted_m, fitted_b = fit_params

    # Generate the curve using the fitted parameters
    fitted_curve = linear_function(x, fitted_m, fitted_b)

    # Plot the original data and the fitted curve
    plt.plot(x, R, 'ro', label='Original Data')
    plt.plot(x, fitted_curve, 'b-', label='Fitted Curve')
    plt.xlabel('Index')
    plt.ylabel('R Values')
    plt.legend()
    plt.show()

    # Print the equation of the fitted line
    print("Equation of the fitted line:")
    print("y =", fitted_m, "x +", fitted_b)
    return fitted_m, fitted_b



def R_opt(beta_ax, az_ax, el, az,limit=90):
    beta_ax = np.radians(beta_ax)
    az_ax = np.radians(az_ax)
    
    zen = np.radians(90 - el)
    
    azrad = np.radians(az)
        
    arg = np.sin(zen)*np.sin(azrad-az_ax)/ \
            (np.sin(zen)*np.cos(azrad-az_ax)*np.sin(beta_ax) \
             + np.cos(zen)*np.cos(beta_ax))
    
    phi = np.where((arg < 0) & ((azrad-az_ax) > 0) , 180, 
            np.where((arg > 0) & ((azrad-az_ax) < 0), -180,0))
    
    
    R = np.degrees(np.arctan(arg)) + phi
    
    R[R>90] = limit
    R[R<-90] = -limit
    
    return R

def optimal_rotational_angle(opt_date, beta_ax, time_zone=4, latitude=43.5, longitude=-80.5):
    # optimal date 
    year = opt_date.year
    month = opt_date.month
    day = opt_date.day

    # other inputs
    az_ax = 180 
    
    hrs = np.arange(0+time_zone,24+time_zone)
    mins = np.arange(0,60)

    pos_every_min = np.array([sunPosition(year,month,day,hr,mn,lat=latitude,long=longitude) 
        for hr,mn in zip(np.repeat(hrs,60),np.tile(mins,24))])

    daylight_start_min = next((i for i, value in enumerate(pos_every_min[:,1]) if value > 0), None)

    # get elevation
    el = pos_every_min[:,1][pos_every_min[:,1]>0]
    # get az
    az = pos_every_min[:,0][pos_every_min[:,1]>0]

    R = R_opt(beta_ax,az_ax,el,az)

    print(el.shape)
    print(R.shape)

    fitted_m, fitted_b = line_best_fit(R)

    # print(f"Opt date: {optimal_date}")
    # print(f"beta_ax: {beta_ax}")
    # print(f"Slope: {fitted_m}")
    # print(f"Intercept: {fitted_b}")

    return daylight_start_min, fitted_m, fitted_b