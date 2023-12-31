from django.shortcuts import render
from django.http import JsonResponse, StreamingHttpResponse, HttpResponse
from .axial_tilt import accelerometer, accelerometerHorz, tilt_angle_req, save_info, send_data_to_views
# from .axial_tilt import time_zone, latitude, longitude, start_date, opt_date, duration, opt_tilt_angle
from datetime import date
import logging
import json
import serial
import serial.tools.list_ports
import datetime
ser = None

# Create your views here.
def test_function(request):
    print(request)
    print("hello there")
    test_str = "brian moo"
    return JsonResponse({'message': 'test message'})

def setup():
    ports = serial.tools.list_ports.comports()
    for i, port in enumerate(ports):
        if 'usb' in port.device:
            usb_port = port.device
    
    comm_rate = 115200
    ser = serial.Serial(usb_port, comm_rate)
    return ser

def stream_output(request):
    global ser
    ser = setup()

    def generate_output(ser):
        # output = accelerometer(4, 43.5, -80.5, date.today(), 20)  # Call the accelerometer function with desired arguments
        horizontal_angle = accelerometerHorz(ser)

        output = accelerometer(ser, horizontal_angle)
        for item in output:
            yield f'data: {item}\n\n'
            print("output:", item)

    response = StreamingHttpResponse(generate_output(ser), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['Connection'] = 'keep-alive'

    # Debug print statements
    print("Streaming response created.")
    logging.debug("Streaming response created.")

    return response

def sse_close_notification(request):
    print("SSE stream closed")

    time_zone, latitude, longitude, start_date, duration, opt_tilt_angle, opt_date_str = send_data_to_views()

    # temp_date = opt_date_str.split(" ")
    # year, month, day = temp_date.split("-")
    # opt_date = date(year, month, day)

    save_info(ser, int(time_zone), float(latitude), float(longitude), opt_date_str, float(opt_tilt_angle))
    return HttpResponse(status=200)