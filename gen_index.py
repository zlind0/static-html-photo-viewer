import os 
import cv2
from PIL import Image
import numpy as np
import multiprocessing as mp
import pathlib, json
from datetime import datetime
from tqdm import tqdm
import shutil

def ismedia(path):
    return os.path.splitext(path)[1].lower() in ['.jpg', '.jpeg', '.png', '.gif', 'heic']

def list_files_recursively(path):
    for root, dirs, files in os.walk(path):
        for file in files:
            res=os.path.join(root, file)
            if 'thumbnail' not in res and ismedia(res):
                yield res

def save_thumbnail(path, dir):
    
    dest= os.path.join(dir, path)
    if os.path.exists(dest):
        return 
    pathlib.Path(os.path.dirname(dest)).mkdir(parents=True, exist_ok=True)
    print(f"THUMBNAIL {path} -> {dest}")
    try:
        img = cv2.imread(path)
        h, w, _ = img.shape
        if h > w:
            img = img[int((h-w)/2):int((h+w)/2), :, :]
        else:
            img = img[:, int((w-h)/2):int((w+h)/2), :]
        img = cv2.resize(img, (THUMBNAIL_WIDTH, THUMBNAIL_WIDTH))
        cv2.imwrite(dest, img, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
    except: pass

THUMBNAIL_WIDTH = 200
DATE_DICT={}
IMGS=list(list_files_recursively('.'))
SCRIPT_PATH = pathlib.Path( __file__ ).absolute()


if __name__ == "__main__":

    with mp.Pool(2) as p:
        for path in IMGS:
            p.apply_async(save_thumbnail, args=(path, 'thumbnails'))
        p.close()
        p.join()

    def get_exif_shot_date(path):
        try:
            img = Image.open(path)
            exif_data = datetime.strptime(img._getexif()[36867], '%Y:%m:%d %H:%M:%S')
            return exif_data.strftime('%Y/%m/%d'), exif_data
        except:
            return "1970/01/01", datetime.strptime("1970/01/01", '%Y/%m/%d')

    print("READ DATE")
    for path in tqdm(IMGS):
        date, datetime = get_exif_shot_date(path)
        if date not in DATE_DICT:
            DATE_DICT[date] = []
        DATE_DICT[date].append((datetime, path))

    THUMBNAIL_HTML=[]
    IMGS_IDS={}

    cnt=1
    for date in sorted(DATE_DICT.keys()):
        DATE_DICT[date]=sorted(DATE_DICT[date], key=lambda x: x[0].strftime('%Y/%m/%d-%H:%M:%S')+x[1])
        THUMBNAIL_HTML.append(f"<h1>{date}</h1>")
        THUMBNAIL_HTML.append('<div class="imagegroup">')
        for datetime, path in DATE_DICT[date]:
            THUMBNAIL_HTML.append(f"<a href='view.html?imageid={cnt}' target='_blank'> <img src='thumbnails/{path}'> </a>")
            IMGS_IDS[cnt]=path
            cnt+=1
        THUMBNAIL_HTML.append('</div>')

    HTML='''
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    </head>
    <style>
    .imagegroup {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
    }
    .imagegroup img {
        width: 50pt;
        height: 50pt;
    }
    body{
        font-family: sans-serif;
    }
    h1{
        font-size: 1.5em;
    }
    </style>
    </head>
    <body>
    BODY
    </body>
    '''
    with open('index.html','w') as f:
        f.write(HTML.replace('BODY','\n'.join(THUMBNAIL_HTML)))

    with open('imgs.js','w') as f:
        f.write(f"imageData={json.dumps(IMGS_IDS)}")

    shutil.copyfile(os.path.join(SCRIPT_PATH,"view.html"), os.path.join(os.getcwd(),"view.html"))
# 
