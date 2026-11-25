"""Publish a promotion to the fixed public banner repository."""
import base64
import hashlib
import json
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request, build_opener

API = 'https://api.github.com/repos/inquangcao3a-art/3A_Banner_Public/contents/'
BRANCH = 'main'


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def github_request(path, token, method='GET', payload=None):
    url = API + path + ('?ref=' + BRANCH if method == 'GET' else '')
    data = json.dumps(payload).encode() if payload is not None else None
    request = Request(url, data, method=method, headers={
        'Accept': 'application/vnd.github+json',
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    })
    try:
        with build_opener(NoRedirect()).open(request, timeout=20) as response:
            return json.load(response)
    except HTTPError as error:
        if error.code == 404 and method == 'GET':
            return None
        if error.code in (409, 422):
            raise ValueError('GitHub báo xung đột cập nhật. Kiểm tra và thử lại.') from None
        if error.code in (401, 403, 404):
            raise ValueError('Kiểm tra token và quyền ghi Contents của kho banner.') from None
        raise ValueError(f'GitHub trả lỗi HTTP {error.code}.') from None


def publish(token, manifest, image):
    """Upload immutable image first, then switch the public manifest."""
    previous = github_request('promotion.json', token)
    if manifest['enabled']:
        name = manifest['image']
        blob_sha = hashlib.sha1(f'blob {len(image)}\0'.encode() + image).hexdigest()
        existing = github_request(name, token)
        if existing is None:
            github_request(name, token, 'PUT', {
                'branch': BRANCH, 'message': 'Add promotion artwork',
                'content': base64.b64encode(image).decode('ascii'),
            })
        elif existing['sha'] != blob_sha:
            raise ValueError('Tên ảnh đã tồn tại nhưng nội dung không khớp.')
    content = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode()
    update = {'branch': BRANCH, 'message': 'Update promotion banner',
              'content': base64.b64encode(content).decode('ascii')}
    if previous is not None:
        update['sha'] = previous['sha']
    response = github_request('promotion.json', token, 'PUT', update)
    return response['commit']['sha']
