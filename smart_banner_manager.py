"""Choose a file, preview it and publish a time-limited banner."""
from datetime import date, datetime, timedelta
from pathlib import Path
from queue import Empty, SimpleQueue
from threading import Thread
import sys
import tkinter as tk
from tkinter import filedialog, simpledialog, ttk

from PIL import Image, ImageTk

from verify_assets import verify_assets

from publish_banner import publish
from smart_banner import MAX_IMAGE, VIETNAM, decode, image_name, play, validate_manifest


def main():
    root = tk.Tk()
    root.title('smart_banner_manager 1.1.0')
    assets = Path(__file__).resolve().parent / 'assets'
    verify_assets(assets)
    with Image.open(assets / 'icon.ico') as icon:
        root.banner_icon = ImageTk.PhotoImage(icon.convert('RGBA'), master=root)
    root.iconphoto(True, root.banner_icon)
    if root.tk.call('tk', 'windowingsystem') == 'win32':
        root.iconbitmap(default=str(assets / 'icon.ico'))
    with Image.open(assets / 'logo.png') as logo:
        logo = logo.convert('RGBA')
        logo.thumbnail((80, 80), Image.Resampling.LANCZOS)
        root.banner_logo = ImageTk.PhotoImage(logo, master=root)
    ttk.Label(root, image=root.banner_logo).pack(pady=(12, 0))
    root.minsize(520, 260)
    form = ttk.Frame(root, padding=20)
    form.pack(fill='both', expand=True)
    form.columnconfigure(1, weight=1)
    now = datetime.now(VIETNAM).date()
    image_path = None
    name = tk.StringVar(value='Chưa chọn ảnh')
    end = tk.StringVar(value=(now + timedelta(days=7)).isoformat())
    token = None
    status = tk.StringVar()
    responses = SimpleQueue()
    preview = None

    def choose():
        nonlocal image_path
        path = filedialog.askopenfilename(parent=root, filetypes=[('Ảnh banner', '*.png *.jpg *.jpeg *.gif *.webp *.apng')])
        if path:
            image_path = Path(path)
            name.set(image_path.name)
            status.set('')

    def prepare():
        if image_path is None:
            raise ValueError('Hãy chọn ảnh trước.')
        today = datetime.now(VIETNAM).date()
        last = date.fromisoformat(end.get().strip())
        with image_path.open('rb') as source:
            payload = source.read(MAX_IMAGE + 1)
        frames, fmt = decode(payload)
        manifest = validate_manifest({
            'schema': 1, 'enabled': True, 'audience': 'all', 'effect': 'none',
            'speed': 1, 'loop': True, 'start': today.isoformat(),
            'end': last.isoformat(), 'image': image_name(payload, fmt), 'link': '',
        })
        return manifest, payload, frames

    def show_preview():
        nonlocal preview
        try:
            manifest, _, frames = prepare()
            if preview is not None and preview.winfo_exists():
                preview.tk.call(preview.protocol('WM_DELETE_WINDOW'))
            preview = play(root, frames, manifest)
        except (OSError, ValueError) as error:
            status.set(str(error))

    def complete(disable=False):
        nonlocal token
        try:
            if disable:
                manifest, payload = {'schema': 1, 'enabled': False}, b''
            else:
                manifest, payload, _ = prepare()
        except (OSError, ValueError) as error:
            status.set(str(error))
            return
        if token is None:
            entered = simpledialog.askstring(
                'Kết nối GitHub', 'Nhập token có quyền ghi kho 3A_Banner_Public.',
                parent=root, show='*',
            )
            if not entered or not entered.strip():
                return
            token = entered.strip()
        credential = token
        complete_button.state(['disabled'])
        disable_button.state(['disabled'])
        status.set('Đang cập nhật GitHub…')

        def worker():
            try:
                commit = publish(credential, manifest, payload)
                responses.put(f'Đã cập nhật promotion.json · Commit {commit[:8]}. Mở lại AI Font Finder PRO để kiểm tra.')
            except ValueError as error:
                responses.put(str(error))
            except (OSError, KeyError):
                responses.put('Chưa xác nhận được cập nhật. Kiểm tra GitHub trước khi thử lại.')

        def poll():
            nonlocal token
            try:
                message = responses.get_nowait()
                status.set(message)
                if message.startswith('Kiểm tra token'):
                    token = None
            except Empty:
                root.after(100, poll)
                return
            complete_button.state(['!disabled'])
            disable_button.state(['!disabled'])

        Thread(target=worker, daemon=True).start()
        root.after(100, poll)

    ttk.Label(form, text='smart_banner_manager', font=('Segoe UI', 19, 'bold')).grid(row=0, column=0, columnspan=3, sticky='w')
    ttk.Button(form, text='Chọn ảnh', command=choose).grid(row=2, column=0, sticky='w', pady=(10, 0))
    ttk.Label(form, textvariable=name, wraplength=350).grid(row=2, column=1, sticky='w', padx=8)
    ttk.Button(form, text='Xem trước', command=show_preview).grid(row=2, column=2, sticky='e')
    ttk.Label(form, text='Ngày cuối (YYYY-MM-DD)').grid(row=3, column=0, sticky='w', pady=(12, 3))
    ttk.Entry(form, textvariable=end).grid(row=3, column=1, columnspan=2, sticky='ew', padx=(8, 0), pady=(12, 3))
    disable_button = ttk.Button(form, text='Tắt banner', command=lambda: complete(True))
    disable_button.grid(row=6, column=0, sticky='w')
    complete_button = ttk.Button(form, text='Đăng banner', command=complete)
    complete_button.grid(row=6, column=2, sticky='e')
    ttk.Label(form, textvariable=status, wraplength=510).grid(row=7, column=0, columnspan=3, sticky='w', pady=(9, 0))
    if len(sys.argv) == 3 and sys.argv[1] == '--verify-build':
        root.update_idletasks()
        root.destroy()
        Path(sys.argv[2]).write_text('PASS: smart_banner_manager 1.1.0 started', encoding='utf-8')
        return
    root.mainloop()


if __name__ == '__main__':
    main()
