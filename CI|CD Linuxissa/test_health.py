import json
from cicd_app import app

def test_health_endpoint():
    client = app.test_client()
    resp = client.get('/health')
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data['status'] in ('healthy', 'ok')
    assert 'timestamp' in data
