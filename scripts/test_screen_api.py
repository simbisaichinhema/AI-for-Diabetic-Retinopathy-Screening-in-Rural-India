import urllib.request
import json
import cv2
import numpy as np

# Create a sample retinal image
img = np.zeros((512, 512, 3), dtype=np.uint8)
cv2.circle(img, (256, 256), 230, (20, 40, 180), -1)
cv2.circle(img, (200, 256), 35, (40, 180, 240), -1)
cv2.polylines(img, [np.array([[200, 256], [260, 200], [350, 180]])], False, (10, 20, 100), 4)

_, buf = cv2.imencode('.jpg', img)

boundary = '----TestBoundary123'
body = (
    f'--{boundary}\r\n'
    f'Content-Disposition: form-data; name="file"; filename="test.jpg"\r\n'
    f'Content-Type: image/jpeg\r\n\r\n'
).encode('utf-8') + buf.tobytes() + f'\r\n--{boundary}--\r\n'.encode('utf-8')

req = urllib.request.Request(
    'http://127.0.0.1:8000/api/screen',
    data=body,
    headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
)

with urllib.request.urlopen(req, timeout=30) as res:
    print('Status:', res.status)
    data = json.loads(res.read().decode())
    print('Case ID:', data.get('case_id'))
    print('Status:', data.get('status'))
    print('Prediction:', data.get('dr_prediction'))
    print('Quality usable:', data.get('quality', {}).get('usable'))
    print('GradCam length:', len(data.get('gradcam_image') or ''))
    print('Enhanced length:', len(data.get('enhanced_image') or ''))

