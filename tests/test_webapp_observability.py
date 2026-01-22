from fastapi.testclient import TestClient
import sys
import os

# Ensure the project root is in the path
sys.path.insert(0, os.path.abspath(os.getcwd()))

from exporter.webapp.main import app

def test_metrics_endpoint():
    client = TestClient(app)
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "process_cpu_seconds_total" in response.text
    assert "process_resident_memory_bytes" in response.text
    print("PASS: /metrics endpoint is live and returning system stats.")

def test_home_page():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    print("PASS: Home page is functional.")

if __name__ == "__main__":
    try:
        test_metrics_endpoint()
        test_home_page()
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)
