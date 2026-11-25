"""Manifest validation, bounded image decoding and Tk playback for Smart Banner."""
import base64
from datetime import date, datetime, timedelta, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import tempfile
import tkinter as tk
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, build_opener

from PIL import Image, ImageEnhance, ImageSequence, ImageTk

MAX_IMAGE = 2 * 1024 * 1024
MAX_FRAMES = 180
MAX_MANIFEST = 16 * 1024
VIETNAM = timezone(timedelta(hours=7))
EFFECTS = ('none', 'rotate', 'glow', 'sweep', 'zoom')
AUDIENCES = ('all', 'licensed', 'trial')


def https_url(value):
    parsed = urlsplit(value)
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username or
            parsed.password or any(ord(c) <= 32 for c in value)):
        raise ValueError('Cần đường dẫn HTTPS hợp lệ.')
    return parsed


def validate_manifest(data):
    if not isinstance(data, dict) or data.get('schema') != 1:
        raise ValueError('Manifest banner không hợp lệ.')
    if not isinstance(data.get('enabled'), bool):
        raise ValueError('Trạng thái banner không hợp lệ.')
    if not data['enabled']:
        return {'schema': 1, 'enabled': False}
    if data.get('audience') not in AUDIENCES or data.get('effect') not in EFFECTS:
        raise ValueError('Đối tượng hoặc hiệu ứng không hợp lệ.')
    speed = data.get('speed')
    if type(speed) not in (int, float) or not 0.5 <= speed <= 2 or not isinstance(data.get('loop'), bool):
        raise ValueError('Tốc độ hoặc chế độ lặp không hợp lệ.')
    start = date.fromisoformat(data['start'])
    end = date.fromisoformat(data['end'])
    if end < start:
        raise ValueError('Ngày kết thúc phải từ ngày bắt đầu trở đi.')
    if not re.fullmatch(r'banner-[0-9a-f]{64}\.(?:png|jpg|gif|webp)', data['image']):
        raise ValueError('Tên ảnh banner không hợp lệ.')
    link = data.get('link', '')
    if link:
        https_url(link)
    return data


def eligible(data, license_status, today=None):
    today = today or datetime.now(VIETNAM).date()
    return (data['enabled'] and license_status in ('trial', 'licensed')
            and data['audience'] in ('all', license_status)
            and date.fromisoformat(data['start']) <= today <= date.fromisoformat(data['end']))


def image_name(payload, image_format):
    return 'banner-' + hashlib.sha256(payload).hexdigest() + '.' + {
        'PNG': 'png', 'JPEG': 'jpg', 'GIF': 'gif', 'WEBP': 'webp',
    }[image_format]


def decode(payload):
    if not 0 < len(payload) <= MAX_IMAGE:
        raise ValueError('Ảnh banner phải có dung lượng tối đa 2 MB.')
    frames = []
    with Image.open(io.BytesIO(payload)) as source:
        if source.format not in ('PNG', 'JPEG', 'GIF', 'WEBP'):
            raise ValueError('Chỉ hỗ trợ PNG, JPEG, GIF, WebP và APNG.')
        if source.width * source.height > 2_000_000 or getattr(source, 'n_frames', 1) > MAX_FRAMES:
            raise ValueError('Ảnh quá lớn hoặc vượt quá 180 khung hình.')
        for index, frame in enumerate(ImageSequence.Iterator(source)):
            if index == 0 and source.info.get('default_image'):
                continue
            still = frame.convert('RGBA')
            still.thumbnail((720, 260), Image.Resampling.LANCZOS)
            duration = max(40, min(3000, int(frame.info.get('duration') or 100)))
            frames.append((still, duration))
        if not frames:
            raise ValueError('Ảnh không có khung hình.')
        return frames, source.format


class SameOriginRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if https_url(newurl).netloc.lower() != https_url(req.full_url).netloc.lower():
            raise ValueError('Chuyển hướng banner phải cùng máy chủ HTTPS.')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch(url, limit, origin):
    if https_url(url).netloc.lower() != origin:
        raise ValueError('Banner phải được lưu cùng máy chủ cấu hình.')
    with build_opener(SameOriginRedirect()).open(url, timeout=5) as response:
        final = https_url(response.geturl())
        if final.netloc.lower() != origin:
            raise ValueError('Banner phải được lưu cùng máy chủ cấu hình.')
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError('Tệp banner vượt giới hạn dung lượng.')
    return data


def check_banner(url, cache_path):
    """Fetch once per launch, reusing a validated image or an offline cache."""
    if not url:
        return None
    origin = https_url(url).netloc.lower()
    try:
        with cache_path.open('rb') as source:
            cached = json.loads(source.read(3 * 1024 * 1024))
        if cached.get('url') != url:
            cached = {}
    except (OSError, ValueError, AttributeError):
        cached = {}
    try:
        data = validate_manifest(json.loads(fetch(url, MAX_MANIFEST, origin)))
        payload = b''
        if data['enabled']:
            cached_data = cached.get('manifest', {})
            if isinstance(cached_data, dict) and cached_data.get('image') == data['image']:
                payload = base64.b64decode(cached.get('image', ''))
            if not image_name_from_hash(payload, data['image']):
                payload = fetch(urljoin(url, data['image']), MAX_IMAGE, origin)
            if not image_name_from_hash(payload, data['image']):
                raise ValueError('Nội dung ảnh không khớp mã kiểm tra.')
        if data['enabled']:
            frames, _ = decode(payload)
        else:
            frames = []
    except (OSError, ValueError, KeyError, TypeError, Image.DecompressionBombError):
        try:
            data = validate_manifest(cached['manifest'])
            if not data['enabled']:
                return None
            payload = base64.b64decode(cached['image'])
            if image_name_from_hash(payload, data['image']):
                return data, decode(payload)[0]
        except (OSError, ValueError, KeyError, TypeError, Image.DecompressionBombError):
            return None
        return None
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=cache_path.parent, delete=False) as fp:
            temp_path = Path(fp.name)
            json.dump({'url': url, 'manifest': data, 'image': base64.b64encode(payload).decode('ascii')}, fp)
        try:
            temp_path.replace(cache_path)
        finally:
            temp_path.unlink(missing_ok=True)
    except OSError:
        pass
    return (data, frames) if data['enabled'] else None


def image_name_from_hash(payload, name):
    return bool(payload) and hashlib.sha256(payload).hexdigest() == Path(name).stem.removeprefix('banner-')


def play(parent, frames, manifest, link_action=None):
    """Display a banner and cancel its only timer when the window closes."""
    import math

    window = tk.Toplevel(parent)
    window.title('smart_banner_manager')
    bg = '#151C27'
    window.configure(bg=bg)
    width = max(frame.width for frame, _ in frames)
    height = max(frame.height for frame, _ in frames)
    canvas = tk.Canvas(window, width=width, height=height, bg=bg, highlightthickness=0)
    canvas.pack()
    item = canvas.create_image(width // 2, height // 2)
    bar = tk.Frame(window, bg=bg)
    bar.pack(fill='x', padx=10, pady=7)
    if link_action is not None and manifest.get('link'):
        tk.Button(bar, text='Tìm hiểu sản phẩm mới', command=link_action).pack(side='left')
        canvas.bind('<Button-1>', lambda event: link_action())
        canvas.configure(cursor='hand2')
    job = None
    position = 0
    elapsed = 0
    duration_total = sum(duration for _, duration in frames)
    effect = manifest['effect']
    cycle = max(duration_total, 3200) if effect != 'none' else duration_total

    def close():
        if job is not None:
            window.after_cancel(job)
        window.destroy()

    def draw():
        nonlocal position, elapsed, job
        job = None
        if not window.winfo_viewable():
            job = window.after(150, draw)
            return
        frame, duration = frames[position]
        phase = elapsed / cycle
        rendered = frame
        if effect == 'rotate':
            rendered = frame.rotate(-360 * phase, Image.Resampling.BICUBIC)
        elif effect == 'glow':
            rendered = ImageEnhance.Brightness(frame).enhance(0.96 + 0.12 * (1 - math.cos(phase * math.tau)) / 2)
        elif effect == 'zoom':
            scale = 0.9 + 0.1 * (1 - math.cos(phase * math.tau)) / 2
            rendered = frame.resize((max(1, round(frame.width * scale)), max(1, round(frame.height * scale))), Image.Resampling.LANCZOS)
        window.banner_photo = ImageTk.PhotoImage(rendered, master=window)
        canvas.itemconfigure(item, image=window.banner_photo)
        canvas.delete('sweep')
        if effect == 'sweep':
            x = int((width + 70) * phase) - 35
            canvas.create_rectangle(x, 0, x + 35, height, fill='#A9D9FF', stipple='gray12', outline='', tags='sweep')
        if len(frames) == 1 and effect == 'none':
            return
        step = duration if effect == 'none' else min(70, duration)
        elapsed += step
        if elapsed >= cycle and not manifest['loop']:
            return
        elapsed %= cycle
        frame_time = elapsed % duration_total if manifest['loop'] else min(elapsed, duration_total - 1)
        position = 0
        while frame_time >= frames[position][1] and position < len(frames) - 1:
            frame_time -= frames[position][1]
            position += 1
        job = window.after(max(20, round(step / manifest['speed'])), draw)

    tk.Button(bar, text='Đóng', command=close).pack(side='right')
    window.protocol('WM_DELETE_WINDOW', close)
    window.bind('<Escape>', lambda event: close())
    job = window.after_idle(draw)
    return window
