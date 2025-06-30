#!/usr/bin/env python3
"""
Test script for CRUD operations
Run this script to test the basic CRUD functionality
"""

import requests
import json
from datetime import datetime
import uuid

# API base URL
BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Health status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_user_registration():
    """Test user registration"""
    print("Testing user registration...")
    
    user_data = {
        "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
        "password": "testpassword123",
        "name": "Test User",
        "organization_id": None
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=user_data)
    print(f"Registration status: {response.status_code}")
    
    if response.status_code == 200:
        user_info = response.json()
        print(f"User created: {user_info}")
        return user_info
    else:
        print(f"Registration failed: {response.text}")
        return None

def test_user_login(email, password):
    """Test user login"""
    print("Testing user login...")
    
    login_data = {
        "email": email,
        "password": password
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    print(f"Login status: {response.status_code}")
    
    if response.status_code == 200:
        token_info = response.json()
        print(f"Login successful: {token_info['access_token'][:20]}...")
        return token_info['access_token']
    else:
        print(f"Login failed: {response.text}")
        return None

def test_device_creation(token):
    """Test device creation"""
    print("Testing device creation...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    device_data = {
        "name": f"Test ESP32 Device {uuid.uuid4().hex[:8]}",
        "entity_type": "device.esp32",
        "description": "Test device for CRUD operations",
        "location": "Test Lab",
        "firmware_version": "1.0.0",
        "hardware_model": "ESP32-WROOM-32",
        "mac_address": "24:6F:28:XX:XX:XX",
        "sensors": [
            {
                "type": "temperature",
                "unit": "celsius",
                "range": {"min": -40, "max": 125}
            },
            {
                "type": "humidity",
                "unit": "percent",
                "range": {"min": 0, "max": 100}
            }
        ],
        "reading_interval": 300,
        "alert_thresholds": {
            "temperature": {"min": 15, "max": 30},
            "humidity": {"min": 30, "max": 70}
        }
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/devices", json=device_data, headers=headers)
    print(f"Device creation status: {response.status_code}")
    
    if response.status_code == 200:
        device_info = response.json()
        print(f"Device created: {device_info['id']}")
        return device_info
    else:
        print(f"Device creation failed: {response.text}")
        return None

def test_device_listing(token):
    """Test device listing"""
    print("Testing device listing...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/api/v1/devices", headers=headers)
    print(f"Device listing status: {response.status_code}")
    
    if response.status_code == 200:
        devices = response.json()
        print(f"Found {devices['total']} devices")
        for device in devices['devices']:
            print(f"  - {device['name']} ({device['id']})")
        return devices
    else:
        print(f"Device listing failed: {response.text}")
        return None

def test_device_update(token, device_id):
    """Test device update"""
    print("Testing device update...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    update_data = {
        "name": f"Updated Device {uuid.uuid4().hex[:8]}",
        "location": "Updated Lab",
        "reading_interval": 600
    }
    
    response = requests.put(f"{BASE_URL}/api/v1/devices/{device_id}", json=update_data, headers=headers)
    print(f"Device update status: {response.status_code}")
    
    if response.status_code == 200:
        device_info = response.json()
        print(f"Device updated: {device_info['name']}")
        return device_info
    else:
        print(f"Device update failed: {response.text}")
        return None

def test_device_status(token, device_id):
    """Test device status endpoint"""
    print("Testing device status...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/api/v1/devices/{device_id}/status", headers=headers)
    print(f"Device status status: {response.status_code}")
    
    if response.status_code == 200:
        status_info = response.json()
        print(f"Device status: {status_info}")
        return status_info
    else:
        print(f"Device status failed: {response.text}")
        return None

def main():
    """Run all tests"""
    print("Starting CRUD operations test...")
    print("=" * 50)
    
    # Test health
    test_health()
    
    # Test user registration and login
    user_info = test_user_registration()
    if not user_info:
        print("Skipping remaining tests due to registration failure")
        return
    
    token = test_user_login(user_info['email'], "testpassword123")
    if not token:
        print("Skipping remaining tests due to login failure")
        return
    
    # Test device operations
    device_info = test_device_creation(token)
    if device_info:
        test_device_listing(token)
        test_device_update(token, device_info['id'])
        test_device_status(token, device_info['id'])
    
    print("=" * 50)
    print("CRUD operations test completed!")

if __name__ == "__main__":
    main() 