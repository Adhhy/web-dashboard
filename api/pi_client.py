import json
import time
import urllib.request
import urllib.error

class DeviceClient:
    def __init__(self, server_url, device_id, device_name, device_key):
        self.server_url = server_url.rstrip('/')
        self.device_id = device_id
        self.device_name = device_name
        self.device_key = device_key
        self.connection_status = "unconnected"

    def connect(self):
        """Request connection to the dashboard."""
        url = f"{self.server_url}/api/system/connect"
        data = {
            "device_id": self.device_id,
            "device_name": self.device_name,
            "device_key": self.device_key
        }
        
        try:
            req = urllib.request.Request(
                url, 
                data=json.dumps(data).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                if res_data.get("status") == "success":
                    self.connection_status = "pending"
                    print(f"Request sent successfully. Status: {self.connection_status}")
                    return True
                else:
                    print(f"Server rejected request: {res_data.get('error')}")
                    return False
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def check_status(self):
        """Poll the public status endpoint using GET with query params."""
        url = f"{self.server_url}/api/system/device-status/{self.device_id}?device_key={self.device_key}"
        
        try:
            req = urllib.request.Request(url, method='GET')
            with urllib.request.urlopen(req) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                if res_data.get("status") == "success":
                    result = res_data.get("result", {})
                    if result.get("status") == "approved":
                        self.connection_status = "connected"
                        print("Device approved! Connection status: connected")
                        return True
                    else:
                        print(f"Current status: {result.get('status')}")
                return False
        except Exception as e:
            print(f"Status check error: {e}")
            return False

if __name__ == "__main__":
    # Example usage
    client = DeviceClient(
        server_url="http://localhost:5000",
        device_id="71ef74ca-da07-48d5-80bf-665bc4c8c73b",
        device_name="Raspberry Pi Reference",
        device_key="123456"
    )
    
    if client.connect():
        print("Polling for approval...")
        while client.connection_status != "connected":
            client.check_status()
            time.sleep(5)
