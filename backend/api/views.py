from django.shortcuts import render
from django.http import JsonResponse, StreamingHttpResponse, HttpResponse
from .axial_tilt import accelerometer, accelerometerHorz, tilt_angle_req, save_info
from .axial_tilt import time_zone
from datetime import date
import logging
import json
import serial
import serial.tools.list_ports
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
    print(time_zone)

    # print("time_zone:", tilt_angle_req.time_zone)
    # print("latitude:", tilt_angle_req.latitude)
    # print("longitude:", tilt_angle_req.longitude)
    # print("start_date:", tilt_angle_req.start_date)
    # print("opt_date:", tilt_angle_req.opt_date)
    # print("duration:", tilt_angle_req.duration)
    # print("opt_tilt_angle:", tilt_angle_req.opt_tilt_angle)

    # save_info(ser, time_zone, latitude, longitude, opt_date, opt_tilt_angle)
    return HttpResponse(status=200)