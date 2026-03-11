import requests
import sys
import time
SERVICES = {'Auth Service': 'http://localhost:8001/health', 'User Service': 'http://localhost:8002/health', 'Session Orchestrator': 'http://localhost:8003/health', 'Speech Pipeline': 'http://localhost:8004/health', 'Assessment Engine': 'http://localhost:8006/health', 'Report Generator': 'http://localhost:8009/health'}

def check_services():
    print('Checking System Health...')
    all_healthy = True
    for name, url in SERVICES.items():
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                print(f'[OK] {name}: Healthy ({url})')
            else:
                print(f'[FAIL] {name}: Unhealthy (Status {response.status_code})')
                all_healthy = False
        except requests.exceptions.ConnectionError:
            print(f'[DOWN] {name}: Connection Refused at {url}')
            all_healthy = False
        except Exception as e:
            print(f'[ERROR] {name}: Error ({e})')
            all_healthy = False
    if all_healthy:
        print('\nAll systems operational!')
        sys.exit(0)
    else:
        print('\nSome systems are down or unhealthy.')
        sys.exit(1)
if __name__ == '__main__':
    check_services()