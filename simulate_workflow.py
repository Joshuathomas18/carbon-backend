import requests
import time
import json

BASE_URL = "http://localhost:8000/api/v1"
TEST_PHONE = "+918497010516"

def simulate_phase_1():
    print("\n--- PHASE 1: Enrolment (Farmer texts 'Hi') ---")
    data = {
        "From": f"whatsapp:{TEST_PHONE}",
        "Body": "Hi"
    }
    response = requests.post(f"{BASE_URL}/webhook/whatsapp", data=data)
    print(f"Status: {response.status_code}")
    print(f"Response (TwiML):\n{response.text.encode('ascii', 'ignore').decode('ascii')}")
    return response

def simulate_phase_2():
    print("\n--- PHASE 2: Mapping (Farmer saves polygon on React App) ---")
    payload = {
        "phone_number": TEST_PHONE,
        "polygon": {
            "type": "Polygon",
            "coordinates": [[
                [75.8, 30.9],
                [75.81, 30.9],
                [75.81, 30.91],
                [75.8, 30.91],
                [75.8, 30.9]
            ]]
        },
        "area_hectares": 3.5
    }
    response = requests.post(f"{BASE_URL}/plots/save-with-phone", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response (JSON):\n{json.dumps(response.json(), indent=2)}")
    return response

def simulate_phase_3():
    print("\n--- PHASE 3: Survey (Farmer answers questions on WhatsApp) ---")
    data = {
        "From": f"whatsapp:{TEST_PHONE}",
        "Body": "Yes, No, 10" # Answers: burned=ha, zero-till=na, urea=10
    }
    response = requests.post(f"{BASE_URL}/webhook/whatsapp", data=data)
    print(f"Status: {response.status_code}")
    print(f"Response (TwiML):\n{response.text.encode('ascii', 'ignore').decode('ascii')}")
    return response

if __name__ == "__main__":
    print(f"Starting End-to-End Simulation for {TEST_PHONE}")
    
    simulate_phase_1()
    time.sleep(2) # Wait a bit to simulate human interaction
    
    simulate_phase_2()
    time.sleep(2)
    
    simulate_phase_3()
    
    print("\nSimulation Complete!")
