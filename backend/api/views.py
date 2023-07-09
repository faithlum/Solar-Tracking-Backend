from django.shortcuts import render
from django.http import JsonResponse
from django.http import StreamingHttpResponse
from .axial_tilt import accelerometer, accelerometerHorz
from datetime import date
import logging
import json

# Create your views here.
def test_function(request):
    print(request)
    print("hello there")
    test_str = "brian moo"
    return JsonResponse({'message': 'test message'})

def stream_output(request):
    def generate_output():
        # output = accelerometer(4, 43.5, -80.5, date.today(), 20)  # Call the accelerometer function with desired arguments
        horizontal_angle = accelerometerHorz()

        output = accelerometer(horizontal_angle)
        for item in output:
            yield f'data: {item}\n\n'
            print("output:", item)

    response = StreamingHttpResponse(generate_output(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['Connection'] = 'keep-alive'

    # Debug print statements
    print("Streaming response created.")
    logging.debug("Streaming response created.")

    return response