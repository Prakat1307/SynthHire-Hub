import requests
import time
import sys
SERVICES = [('Frontend', 'http://localhost:3000'), ('API Gateway', 'http://localhost:80/health'), ('Auth Service', 'http://localhost:8001/health'), ('User Service', 'http://localhost:8002/health'), ('Session Orchestrator', 'http://localhost:8003/health'), ('Speech Pipeline', 'http://localhost:8004/health'), ('Code Executor', 'http://localhost:8005/health'), ('Assessment Engine', 'http://localhost:8006/health'), ('Emotion Analysis', 'http://localhost:8007/health'), ('Report Generator', 'http://localhost:8009/health'), ('Analytics Service', 'http://localhost:8010/health')]

def check_service(name, url):
    try:
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            print(f'✅ {name}: UP')
            return True
        else:
            print(f'⚠️ {name}: Returned {response.status_code}')
            return False
    except requests.exceptions.ConnectionError:
        print(f'❌ {name}: DOWN (Connection Refused)')
        return False
    except Exception as e:
        print(f'❌ {name}: ERROR ({e})')
        return False

def main():
    print('========================================')
    print('      SynthHire Service Health Check')
    print('========================================')
    print('Checking services... (Ensure Docker is running)')
    all_up = True
    for name, url in SERVICES:
        if not check_service(name, url):
            all_up = False
    print('========================================')
    if all_up:
        print('🚀 System is fully operational!')
        print('Go to: http://localhost:3000')
    else:
        print("⚠️ Some services are down. Check 'docker-compose logs <service_name>'")
if __name__ == '__main__':
    main()