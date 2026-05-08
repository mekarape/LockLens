import base64
import json
import requests
from dotenv import load_dotenv
import os

load_dotenv()
AMD_ENDPOINT = os.getenv("AMD_ENDPOINT")
MODEL = "Qwen/Qwen2.5-VL-7B-Instruct"

# takes image file + target string
# returns a dictionary ready to send
def package_request(image_path, target):
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    image_bytes_encoded = base64.b64encode(image_bytes).decode("utf-8")
    data = {
        "model": MODEL,
        "max_tokens": 200,
        "temperature": 0.01,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_bytes_encoded}"
                        }
                    },
                    {
                        "type": "text",
                        "text": f'Locate the {target} in this image. Return ONLY valid JSON: {{"found": true, "cx": 0.5, "cy": 0.5, "w": 0.2, "h": 0.3, "confidence": 0.94}} or {{"found": false}}'
                    }
                ]
            }
        ]
    }
    return data

# takes the package
# sends it to AMD cloud via HTTP POST request
# returns the raw response from the server
def send_request(data):
    response = requests.post(AMD_ENDPOINT, json=data, timeout=60)
    return response

# takes the raw response from AMD
# extracts cx, cy, found, confidence
# returns clean dictionary the motor controller can use
def parse_response(response):
    # unpack the vLLM response wrapper to get Qwen's actual answer
    content = response.json()["choices"][0]["message"]["content"]
    # handle empty or invalid response from model
    if not content or not content.strip():
        return {"found": False}
    try:
        results = json.loads(content)
    except json.JSONDecodeError:
        return {"found": False}
    return results

def get_target_location(image_path, target):
    data = package_request(image_path, target)
    response = send_request(data)
    results = parse_response(response)
    return results