import asyncio
import uvicorn
from fastapi import FastAPI,WebSocket
import cv2 
from influxdb import InfluxDBClient
from skimage.metrics import structural_similarity
from requests import get

token = '2112790230:AAH9mLzxyJjVwFLyYF4i-akPuQEsjgYAvfA'
url = f'https://api.telegram.org/bot{token}/'
app = FastAPI()


client = InfluxDBClient(host='192.168.100.170',
                    port=8086,
                    username='',
                    password='',
                    database='avc')

def image_filter(img):
    resized_mod = cv2.resize(img, (300, 200))
    crop_mod = resized_mod[50:300, 270:300]
    gray_crop_mod = cv2.cvtColor(crop_mod, cv2.COLOR_BGR2GRAY)
    return gray_crop_mod

def list_image():
    namefile1=[]
    namefile2=[]
    namefile3=[]
    result = client.query('SELECT * FROM "type_data" ORDER BY DESC LIMIT 2')
    for measurement in result.get_points(measurement='type_data'):
        namefile1.append(measurement['cam1_name'])
        namefile2.append(measurement['cam2_name'])
        namefile3.append(measurement['cam3_name'])
    namefile=namefile1+namefile2+namefile3
    return namefile

def similarity(a,b):
    previous_cam1=a
    next_cam1=b
    similar_cam=""
    last_img=cv2.imread(previous_cam1)
    img1= image_filter(last_img)
    new_img=cv2.imread(next_cam1)
    img2= image_filter(new_img)
    similarty = structural_similarity(img1, img2, multichannel=True, gaussian_weights=True, sigma=1.5, use_sample_covariance=False, data_range=1.0)
    if similarty>=0.2:
        similar_cam="similar"
    else:
        similar_cam="tidak similar"
    return similar_cam

def blur_detection(variable_blur):
    next_cam1=variable_blur
    img=cv2.imread(next_cam1,0)
    threshold_buram=cv2.Laplacian(img,cv2.CV_64F).var()
    buram=""
    if threshold_buram>=1000:
        buram="tidak buram"
    elif threshold_buram<=999:
        buram="buram"
    return buram


def kirim_pesan(hasil):
    get(url+'sendMessage',params=hasil)

@app.websocket("/")
async def websocket_b(ws: WebSocket):
    await ws.accept()
    while (True):
        result_cam=list_image()
        try:
            result_cam1=similarity(result_cam[0],result_cam[1])
            result_cam2=similarity(result_cam[2],result_cam[3])
            result_cam3=similarity(result_cam[4],result_cam[5])
        except:
            pass

        if (result_cam[0] and result_cam[1]) is None:
            print("cam 1 kosong")
            hasil={'chat_id':1088065650,"text":"kamera 1 gambar kosong"}
            kirim_pesan(hasil)
            result_cam1="kosong"

        if (result_cam[2] and result_cam[3]) is None:
            print("cam 2 kosong")
            hasil={'chat_id':1088065650,"text":"kamera 2 gambar kosong"}
            kirim_pesan(hasil)
            result_cam2="kosong"

        if (result_cam[4] and result_cam[5]) is None:
            print("cam 3 kosong")
            hasil={'chat_id':1088065650,"text":"kamera 3 gambar kosong"}
            kirim_pesan(hasil)
            result_cam3="kosong"

        print("result kamera 2:" + result_cam2)
        print("--------------------")
        print("result kamera 3:" + result_cam3)

        if result_cam1 == 'tidak similar':
            hasil={'chat_id':1088065650,"text":"kamera 1 gambar tidak similar"}
            kirim_pesan(hasil)
        if result_cam2 == 'tidak similar':
            hasil={'chat_id':1088065650,"text":"kamera 2 gambar tidak similar"}
            kirim_pesan(hasil)
        if result_cam3 == 'tidak similar':
            hasil={'chat_id':1088065650,"text":"kamera 3 gambar tidak similar"}
            kirim_pesan(hasil)

        if (result_cam[1]) is None:
            print("kamera blur 1 kosong")
            hasil={'chat_id':1088065650,"text":"kamera blur 1 gambar kosong"}
            kirim_pesan(hasil)
            blur_cam1="kosong"
        else:
            blur_cam1=blur_detection(result_cam[1])

        if (result_cam[3]) is None:
            print("cam 2 kosong")
            hasil={'chat_id':1088065650,"text":"kamera blur 2 gambar kosong"}
            kirim_pesan(hasil)
            blur_cam2="kosong"
        else:
            blur_cam2=blur_detection(result_cam[3])

        if (result_cam[5]) is None:
            print("cam 3 kosong")
            hasil={'chat_id':1088065650,"text":"kamera blur 3 gambar kosong"}
            kirim_pesan(hasil)
            blur_cam3="kosong"
        else:
            blur_cam2=blur_detection(result_cam[5])

        if blur_cam1 == 'buram':
            hasil={'chat_id':1088065650,"text":"kamera 1 gambar buram"}
            kirim_pesan(hasil)
        if blur_cam2 == 'buram':
            hasil={'chat_id':1088065650,"text":"kamera 2 gambar buram"}
            kirim_pesan(hasil)
        if blur_cam3 == 'buram':
            hasil={'chat_id':1088065650,"text":"kamera 3 gambar buram"}
            kirim_pesan(hasil)
        
        json_payload={'similarity_cam1':result_cam1,'similarity_cam2':result_cam2,'similarity_cam3':result_cam3,"blur_cam1":blur_cam1,"blur_cam2":blur_cam2,"blur_cam3":blur_cam3}
        await ws.send_json(json_payload)
        kirim_pesan(hasil)
        await asyncio.sleep(2)

# app.include_router(api_router)
if __name__ == "__main__":
    uvicorn.run("websocket:app", host="192.168.100.105", port=8080,log_level="info",reload=True)
    