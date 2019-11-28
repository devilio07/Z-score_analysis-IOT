import conf, json, time, math, statistics, requests
from boltiot import Bolt


def compute_bounds(history_data,frame_size,factor):
    if len(history_data)<frame_size :
        return None

    if len(history_data)>frame_size :
        del history_data[0:len(history_data)-frame_size]
    Mn=statistics.mean(history_data)
    Variance=0
    for data in history_data :
        Variance += math.pow((data-Mn),2)
    Zn = factor * math.sqrt(Variance / frame_size)
    High_bound = history_data[frame_size-1]+Zn
    Low_bound = history_data[frame_size-1]-Zn
    return [High_bound,Low_bound]

def trigger_integromat_webhook():
    response = requests.request("GET", conf.URL)
    print (response.text)

product = Bolt(conf.API, conf.ID)
history_data=[]

while True:
    response = product.analogRead('A0')
    data = json.loads(response)
    if data['success'] != 1:
        print("There was an error while retriving the data.")
        print("This is the error:"+data['value'])
        time.sleep(10)
        continue

    print ("This is the value "+ data['value'])
    sensor_value=0
    try:
        sensor_value = int(data['value'])
    except e:
        print("There was an error while parsing the response: ",e)
        continue

    bound = compute_bounds(history_data,conf.FRAME,conf.MUL)
    if not bound:
        required_data_count=conf.FRAME-len(history_data)
        print("Not enough data to compute Z-score. Need ",required_data_count," more data points")
        history_data.append(int(data['value']))
        time.sleep(10)
        continue

    try:
        if sensor_value > bound[0]:
            print ("The temprature increased suddenly. Tweeting.")
            response = trigger_integromat_webhook()
            print("This is the response ",response)
        history_data.append(sensor_value);
    except Exception as e:
        print ("Error",e)
    time.sleep(10)
