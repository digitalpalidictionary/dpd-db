from fastapi.testclient import TestClient
import sys
import os

# Ensure the project root is in the path
sys.path.insert(0, os.path.abspath(os.getcwd()))

from exporter.webapp.main import app


def test_status_endpoint():
    client = TestClient(app)
    response = client.get("/status")
    assert response.status_code == 200
    assert "Memory Usage" in response.text
    assert "MB" in response.text
    assert "DPD Webapp Status" in response.text
    print("PASS: /status dashboard is live and readable.")


if __name__ == "__main__":
    try:
        test_status_endpoint()
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)
