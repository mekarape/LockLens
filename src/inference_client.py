
import base64
import json
import requests

AMD_ENDPOINT = "http://YOUR_IP_ADDRESS:8000/v1/chat/completions"

# takes image file + target string
# returns a dictionary ready to send 
def package_request(image_path, target):
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    image_bytes_encoded = base64.b64encode(image_bytes).decode("utf-8")
    
    data = {
        "image": image_bytes_encoded,
        "target": target
    }

    return data

# takes the package 
# sends it to AMD cloud via HTTP POST request
# returns the raw response from the server
def send_request(data):
    response = requests.post(AMD_ENDPOINT, json=data)
    return response 


# takes the raw response from AMD 
# extracts cx, cy, found, confidence 
# returns clean dictionary the motor controller can use 
def parse_response(response):
   content = response.json()["choices"][0]["message"]["content"]
   results = json.loads(content)
   return results

def get_target_location(image_path, target):
    data = package_request(image_path, target)
    response = send_request(data)
    results = parse_response(response)
    return results 