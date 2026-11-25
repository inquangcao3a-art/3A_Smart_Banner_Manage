"""Bounded image decoder and Tk animation, shared by client and publisher."""
import io, math
from PIL import Image, ImageTk, ImageEnhance
MAX=2*1024*1024
FORMATS={'PNG':'png','JPEG':'jpg','GIF':'gif','WEBP':'webp'}
def decode(data):
    if len(data)>MAX: raise ValueError('Ảnh vượt 2 MB')
    frames=[]; delays=[]
    with Image.open(io.BytesIO(data)) as im:
        ext=FORMATS.get(im.format)
        if not ext: raise ValueError('Định dạng không hỗ trợ')
        n=getattr(im,'n_frames',1)
        if im.width*im.height>4000000 or n>180 or n*im.width*im.height>80000000: raise ValueError('Ảnh quá lớn hoặc quá nhiều khung hình')
        first_frame = int(im.format == 'PNG' and im.info.get('default_image', False))
        for i in range(first_frame, n):
            im.seek(i); frame=im.convert('RGBA');frame.thumbnail((440,160),Image.Resampling.LANCZOS)
            frames.append(frame);delays.append(max(42,min(10000,int(im.info.get('duration',100) or 100))))
    return ext,frames,delays

def play(label,frames,delays,effect='none',speed=1.0,loop=True):
    photos=[]; times=[]
    if len(frames)==1 and effect!='none':
        original=frames[0]; w,h=original.size
        for i in range(36):
            phase=2*math.pi*i/36
            if effect=='rotate':
                # Fit the rotating image inside its original canvas.
                scale=min(w,h)/math.hypot(w,h); small=original.resize((max(1,int(w*scale)),max(1,int(h*scale))))
                f=Image.new('RGBA',(w,h)); r=small.rotate(-i*10,expand=True,resample=Image.Resampling.BICUBIC);f.alpha_composite(r,((w-r.width)//2,(h-r.height)//2))
            elif effect=='pulse': f=ImageEnhance.Brightness(original).enhance(.82+.18*(1+math.cos(phase))/2)
            else: f=original
            photos.append(ImageTk.PhotoImage(f,master=label));times.append(85)
    else:
        photos=[ImageTk.PhotoImage(f,master=label) for f in frames];times=delays
    state={'job':None,'i':0,'done':False,'stopped':False};label.configure(image=photos[0]);label.image=photos[0]
    def stop(event=None):
        if event is not None and event.widget is not label:return
        if event is None or event.type == '17':state['stopped']=True
        if state['job'] is not None:
            try:label.after_cancel(state['job'])
            except Exception:pass
        state['job']=None
        if event is None:
            for sequence, binding_id in bindings:
                label.unbind(sequence, binding_id)
            bindings.clear()
    def tick():
        state['job']=None
        if not label.winfo_exists() or not label.winfo_viewable():return
        i=state['i'];label.configure(image=photos[i]);label.image=photos[i]
        if i==len(photos)-1 and not loop:state['done']=True;return
        state['i']=(i+1)%len(photos);state['job']=label.after(max(1,int(times[i]/speed)),tick)
    def resume(event=None):
        if not state['stopped'] and not state['done'] and len(photos)>1 and state['job'] is None:state['job']=label.after(1,tick)
    bindings = [
        (sequence, label.bind(sequence, callback, add='+'))
        for sequence, callback in (
            ('<Destroy>', stop), ('<Unmap>', stop), ('<Map>', resume)
        )
    ]
    resume()
    return stop
