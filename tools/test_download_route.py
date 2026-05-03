import importlib.util
import os
import sys

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

spec = importlib.util.spec_from_file_location('app_module', os.path.join(repo_root, 'app.py'))
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)
app = getattr(app_module, 'app')

with app.test_client() as c:
    with c.session_transaction() as sess:
        sess['logged_in'] = True
    resp = c.get('/admin/download_qrs')
    print('STATUS:', resp.status_code)
    print('CONTENT-TYPE:', resp.headers.get('Content-Type'))
    print('CONTENT-LENGTH:', len(resp.get_data()))
    data = resp.get_data()
    if data and resp.status_code == 200:
        os.makedirs(os.path.join(os.path.dirname(__file__), '..', 'test_output'), exist_ok=True)
        try:
            with open(os.path.join(os.path.dirname(__file__), '..', 'test_output', 'debug_download_response.bin'), 'wb') as f:
                f.write(data)
            print('Wrote debug output to test_output/debug_download_response.bin')
        except Exception as e:
            print('Failed to write debug file:', e)
