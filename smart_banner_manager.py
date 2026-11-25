"""Owner-only banner publisher: exports static files for HTTPS hosting."""
import tkinter as tk
from tkinter import ttk,filedialog,messagebox
from pathlib import Path
import hashlib,json,datetime
import sys
from PIL import Image,ImageTk
from banner_animation import decode,play
from verify_assets import verify_assets
root = tk.Tk()
root.title('3A_Smart_Banner_Manage 1.0.0')
root.geometry('550x740')

assets = Path(__file__).resolve().parent / 'assets'
icon_path = assets / 'icon.ico'
if icon_path.is_file():
    with Image.open(icon_path) as icon:
        window_icon = ImageTk.PhotoImage(icon.convert('RGBA'), master=root)
    root.iconphoto(True, window_icon)
    if root.tk.call('tk', 'windowingsystem') == 'win32':
        root.iconbitmap(default=str(icon_path))

logo_path = assets / 'logo.png'
if logo_path.is_file():
    with Image.open(logo_path) as logo:
        logo = logo.convert('RGBA')
        logo.thumbnail((96, 96), Image.Resampling.LANCZOS)
        header_logo = ImageTk.PhotoImage(logo, master=root)
    ttk.Label(root, image=header_logo).pack(pady=(8, 0))

fields={}; data=None; ext=None; stop=None
preview=ttk.Label(root);preview.pack(pady=8)
def choose():
 global data,ext,stop
 p=filedialog.askopenfilename(filetypes=[('Ảnh','*.png *.jpg *.jpeg *.webp *.gif *.apng')]);
 if not p:return
 try:
  raw=Path(p).read_bytes(); ext,frames,delays=decode(raw);data=raw
  refresh_preview()
 except Exception as e:messagebox.showerror('Ảnh',str(e))
ttk.Button(root,text='CHỌN ẢNH',command=choose).pack()
for key,label in [('base','URL thư mục HTTPS công khai'),('link','Link giới thiệu (không bắt buộc)'),('start','Bắt đầu YYYY-MM-DD'),('end','Kết thúc YYYY-MM-DD')]:
 ttk.Label(root,text=label).pack(anchor='w',padx=12);v=tk.StringVar();fields[key]=v;ttk.Entry(root,textvariable=v).pack(fill='x',padx=12)
aud=tk.StringVar(value='all');ttk.Combobox(root,textvariable=aud,values=['all','premium','trial'],state='readonly').pack(pady=5)
enabled=tk.BooleanVar(value=True);ttk.Checkbutton(root,text='Bật banner',variable=enabled).pack()
effect=tk.StringVar(value='none');speed=tk.StringVar(value='1');loop=tk.BooleanVar(value=True)
ttk.Label(root,text='Hiệu ứng ảnh tĩnh (GIF/WebP/APNG giữ chuyển động gốc)').pack()
ttk.Combobox(root,textvariable=effect,values=['none','rotate','pulse'],state='readonly').pack()
ttk.Label(root,text='Tốc độ (0.5 – 2)').pack();ttk.Combobox(root,textvariable=speed,values=['0.5','0.75','1','1.5','2'],state='readonly').pack()
ttk.Checkbutton(root,text='Lặp liên tục',variable=loop).pack()
def refresh_preview(*args):
 global stop
 if data is None:return
 if stop:stop()
 _,frames,delays=decode(data);stop=play(preview,frames,delays,effect.get(),float(speed.get()),loop.get())
for var in (effect,speed,loop):var.trace_add('write',refresh_preview)
def export():
 try:
  base=fields['base'].get().strip().rstrip('/')
  if not base.startswith('https://'):raise ValueError('Cần URL HTTPS')
  m={'enabled':enabled.get(),'audience':aud.get()}
  if enabled.get():
   if data is None:raise ValueError('Chọn ảnh trước')
   digest=hashlib.sha256(data).hexdigest();m.update(image=base+'/'+digest+'.'+ext,sha256=digest,effect=effect.get(),speed=float(speed.get()),loop=loop.get())
   for k in ('start','end','link'):
    v=fields[k].get().strip()
    if v:
     if k!='link':datetime.date.fromisoformat(v)
     elif not v.startswith('https://'):raise ValueError('Link phải HTTPS')
     m[k]=v
  dest=filedialog.askdirectory();
  if not dest:return
  p=Path(dest)
  if enabled.get():(p/(digest+'.'+ext)).write_bytes(data)
  (p/'manifest.json').write_text(json.dumps(m,ensure_ascii=False),encoding='utf-8')
  (p/'banner_config.json').write_text(json.dumps({'manifest_url':base+'/manifest.json'}),encoding='utf-8')
  messagebox.showinfo('Đã xuất','Đưa ảnh và manifest.json lên thư mục HTTPS. Chép banner_config.json vào mã nguồn khách trước khi build lần đầu.')
 except Exception as e:messagebox.showerror('Lỗi',str(e))
ttk.Button(root,text='XUẤT BANNER',command=export).pack(pady=10)
if len(sys.argv) == 3 and sys.argv[1] == '--verify-build':
    verify_assets(assets)
    root.update_idletasks()
    root.destroy()
    Path(sys.argv[2]).write_text('PASS: Smart Banner Manager started', encoding='utf-8')
else:
    root.mainloop()
