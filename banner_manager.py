"""Choose a file, preview it and publish a time-limited banner."""
from datetime import date, datetime, timedelta
from pathlib import Path
from queue import Empty, SimpleQueue
from threading import Thread
import tkinter as tk
from tkinter import filedialog, ttk

from publish_banner import publish
from smart_banner import MAX_IMAGE, VIETNAM, decode, image_name, play, validate_manifest


def main():
    root = tk.Tk()
    root.title('3A Smart Banner Manager 1.1.0')
    root.minsize(590, 310)
    form = ttk.Frame(root, padding=20)
    form.pack(fill='both', expand=True)
    form.columnconfigure(1, weight=1)
    now = datetime.now(VIETNAM).date()
    image_path = None
    name = tk.StringVar(value='Chưa chọn ảnh')
    end = tk.StringVar(value=(now + timedelta(days=7)).isoformat())
    token = tk.StringVar()
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
        credential = token.get().strip()
        if not credential:
            status.set('Hãy nhập token GitHub có quyền Contents: Read and write.')
            return
        try:
            if disable:
                manifest, payload = {'schema': 1, 'enabled': False}, b''
            else:
                manifest, payload, _ = prepare()
        except (OSError, ValueError) as error:
            status.set(str(error))
            return
        complete_button.state(['disabled'])
        disable_button.state(['disabled'])
        status.set('Đang cập nhật GitHub…')

        def worker():
            try:
                commit = publish(credential, manifest, payload)
                responses.put(f'Hoàn thành · GitHub commit {commit[:8]}')
            except ValueError as error:
                responses.put(str(error))
            except (OSError, KeyError):
                responses.put('Chưa xác nhận được cập nhật. Kiểm tra GitHub trước khi thử lại.')

        def poll():
            try:
                status.set(responses.get_nowait())
            except Empty:
                root.after(100, poll)
                return
            complete_button.state(['!disabled'])
            disable_button.state(['!disabled'])

        Thread(target=worker, daemon=True).start()
        root.after(100, poll)

    ttk.Label(form, text='3A Smart Banner Manager', font=('Segoe UI', 19, 'bold')).grid(row=0, column=0, columnspan=3, sticky='w')
    ttk.Label(form, text='Khuyến mãi trong khung giá · Dùng thử và đã kích hoạt').grid(row=1, column=0, columnspan=3, sticky='w', pady=(3, 14))
    ttk.Button(form, text='Chọn ảnh', command=choose).grid(row=2, column=0, sticky='w')
    ttk.Label(form, textvariable=name, wraplength=350).grid(row=2, column=1, sticky='w', padx=8)
    ttk.Button(form, text='Xem trước', command=show_preview).grid(row=2, column=2, sticky='e')
    ttk.Label(form, text='Ngày cuối (YYYY-MM-DD)').grid(row=3, column=0, sticky='w', pady=(12, 3))
    ttk.Entry(form, textvariable=end).grid(row=3, column=1, columnspan=2, sticky='ew', padx=(8, 0), pady=(12, 3))
    ttk.Label(form, text='Token GitHub').grid(row=4, column=0, sticky='w', pady=3)
    ttk.Entry(form, textvariable=token, show='*').grid(row=4, column=1, columnspan=2, sticky='ew', padx=(8, 0), pady=3)
    ttk.Label(form, text='Hết ngày cuối theo giờ Việt Nam, ứng dụng tự hiện lại banner giá thường.', wraplength=510).grid(row=5, column=0, columnspan=3, sticky='w', pady=(7, 8))
    disable_button = ttk.Button(form, text='Kết thúc sớm', command=lambda: complete(True))
    disable_button.grid(row=6, column=0, sticky='w')
    complete_button = ttk.Button(form, text='Hoàn thành', command=complete)
    complete_button.grid(row=6, column=2, sticky='e')
    ttk.Label(form, textvariable=status, wraplength=510).grid(row=7, column=0, columnspan=3, sticky='w', pady=(9, 0))
    root.mainloop()


if __name__ == '__main__':
    main()
