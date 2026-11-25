"""Seller-only banner preview and export."""
from datetime import timedelta
from pathlib import Path
import json
import sys
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog, ttk

from smart_banner import MAX_IMAGE, VIETNAM, decode, image_name, play, validate_manifest
from datetime import datetime


def main():
    if '--self-test' in sys.argv:
        import io
        buf = io.BytesIO()
        Image.new('RGB', (32, 16)).save(buf, format='PNG')
        frames, fmt = decode(buf.getvalue())
        assert fmt == 'PNG' and len(frames) == 1
        assets = Path(__file__).resolve().parent / 'assets'
        for name in ('logo.png', 'app.ico'):
            with Image.open(assets / name) as asset:
                asset.load()
        return
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("3A_Smart_Banner_Manage")
    root = tk.Tk()
    assets = Path(__file__).resolve().parent / 'assets'
    root.iconbitmap(default=str(assets / 'app.ico')) if sys.platform == 'win32' else None
    root.brand_logo = ImageTk.PhotoImage(Image.open(assets / 'logo.png').resize((80, 80), Image.Resampling.LANCZOS), master=root)
    root.iconphoto(True, root.brand_logo)
    root.title('3A_Smart_Banner_Manage 1.0.1')
    form = ttk.Frame(root, padding=18)
    form.pack(fill='both', expand=True)
    form.columnconfigure(1, weight=1)
    now = datetime.now(VIETNAM).date()
    selected = tk.StringVar()
    start = tk.StringVar(value=now.isoformat())
    end = tk.StringVar(value=(now + timedelta(days=30)).isoformat())
    link = tk.StringVar()
    speed = tk.StringVar(value='1.0')
    audience = tk.StringVar(value='Tất cả khách')
    effect = tk.StringVar(value='Không')
    enabled = tk.BooleanVar(value=True)
    loop = tk.BooleanVar(value=True)
    status = tk.StringVar()
    preview_window = None
    audience_keys = {'Tất cả khách': 'all', 'Đã kích hoạt': 'licensed', 'Đang dùng thử': 'trial'}
    effect_keys = {'Không': 'none', 'Xoay 360° 2D': 'rotate', 'Nhấp sáng nhẹ': 'glow',
                   'Quét sáng': 'sweep', 'Phóng to – thu nhỏ': 'zoom'}

    def select():
        path = filedialog.askopenfilename(parent=root, filetypes=[('Ảnh banner', '*.png *.jpg *.jpeg *.gif *.webp *.apng')])
        if path:
            selected.set(path)

    def prepare():
        if not enabled.get():
            return validate_manifest({'schema': 1, 'enabled': False}), b'', []
        if not selected.get():
            raise ValueError('Hãy chọn ảnh banner.')
        with Path(selected.get()).open('rb') as file:
            payload = file.read(MAX_IMAGE + 1)
        frames, fmt = decode(payload)
        data = validate_manifest({
            'schema': 1, 'enabled': True, 'audience': audience_keys[audience.get()],
            'effect': effect_keys[effect.get()], 'speed': float(speed.get()), 'loop': loop.get(),
            'start': start.get(), 'end': end.get(), 'image': image_name(payload, fmt),
            'link': link.get().strip(),
        })
        status.set(f'{fmt} · {len(frames)} khung hình · {len(payload) / 1024:.0f} KB')
        return data, payload, frames

    def preview():
        nonlocal preview_window
        try:
            data, _, frames = prepare()
            if not frames:
                status.set('Banner đang tắt.')
                return
            if preview_window is not None and preview_window.winfo_exists():
                preview_window.tk.call(preview_window.protocol('WM_DELETE_WINDOW'))
            preview_window = play(root, frames, data)
            preview_window.title('3A_Smart_Banner_Manage – Xem trước')
        except (OSError, ValueError, KeyError, TypeError) as exc:
            status.set(f'Không thể xem trước: {exc}')

    def export():
        try:
            data, payload, _ = prepare()
            destination = filedialog.askdirectory(parent=root)
            if not destination:
                return
            target = Path(destination)
            if data['enabled']:
                (target / data['image']).write_bytes(payload)
            (target / 'banner.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            status.set('Đã xuất. Đăng ảnh lên trước, rồi đăng banner.json.')
        except (OSError, ValueError, KeyError, TypeError) as exc:
            status.set(f'Không thể xuất: {exc}')

    ttk.Label(form, text='3A_Smart_Banner_Manage 1.0.1', image=root.brand_logo, compound='left', font=('Segoe UI', 18, 'bold')).grid(row=0, column=0, columnspan=3, sticky='w', pady=(0, 10))
    ttk.Entry(form, textvariable=selected, width=45, state='readonly').grid(row=1, column=0, columnspan=2, sticky='ew')
    ttk.Button(form, text='Chọn ảnh', command=select).grid(row=1, column=2, padx=(6, 0))
    for row, (title, value, choices) in enumerate((
        ('Đối tượng', audience, tuple(audience_keys)), ('Hiệu ứng', effect, tuple(effect_keys)),
        ('Tốc độ', speed, ('0.5', '0.75', '1.0', '1.25', '1.5', '2.0')),
        ('Bắt đầu (YYYY-MM-DD)', start, ()), ('Kết thúc (YYYY-MM-DD)', end, ()),
        ('Đường dẫn HTTPS', link, ()),
    ), start=2):
        ttk.Label(form, text=title).grid(row=row, column=0, sticky='w', pady=5)
        field = ttk.Combobox(form, textvariable=value, values=choices, state='readonly') if choices else ttk.Entry(form, textvariable=value)
        field.grid(row=row, column=1, columnspan=2, sticky='ew')
    ttk.Checkbutton(form, text='Hiển thị banner', variable=enabled).grid(row=8, column=0, sticky='w')
    ttk.Checkbutton(form, text='Lặp chuyển động', variable=loop).grid(row=8, column=1, sticky='w')
    ttk.Label(form, textvariable=status, wraplength=470).grid(row=9, column=0, columnspan=3, sticky='w', pady=8)
    ttk.Button(form, text='Xem trước', command=preview).grid(row=10, column=0, sticky='w')
    ttk.Button(form, text='Xuất banner', command=export).grid(row=10, column=2, sticky='e')
    root.mainloop()


if __name__ == '__main__':
    main()
