import json, time, math, statistics, requests
import email_conf as cf  # Importing configuration file 
from boltiot import Bolt, Email


"""Defining function to calculate upper and lower bounds""" 
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
"""Defining function to convert sensor value in terms of Temprature in Celcius"""
def Temp(value):
    Temprature= value/10.24
    return round(Temprature)

 
"""To keep track of how long has the temprature been between -33 and - 30  Since data is noted every 10 seconds hence for 20 minutes the count should be 120""" 
count =0

product = Bolt(cf.API, cf.ID) #connecting Bolt using Python Lib

# Setting Up email services 
email=Email(cf.MAIL_API, cf.SANDBOX_URL, cf.SENDER_EMAIL, cf.RECIPENT_EMAIL)

history_data = []  #defining List to store the data to be received from Bolt

while True:
    response = product.analogRead('A0')
    data = json.loads(response)
    # Retreiving temprature value from Bolt 
    if data['success'] != 1:
        print("There was an error while retriving the data.")
        print("This is the error:"+data['value'])
        time.sleep(10)
        continue

    print ("Temprature is : ", Temp(float(data['value'])))
    sensor_value=0
    try:
        sensor_value = int(data['value'])
    except e:
        print("There was an error while parsing the response: ",e)
        continue

    #Computing the bounds from the given amount of data
    bound = compute_bounds(history_data,15,3)
    if not bound:
        required_data_count=15-len(history_data)
        print("Not enough data to compute Z-score. Need ",required_data_count," more data points")
        history_data.append(int(data['value']))
        time.sleep(10)
        continue

    try:
        if sensor_value > bound[0]:
            print ("The temprature is increased suddenly, Sending Alert message!")
            response=email.send_email("Alert","someone opened the door Close it to maintain the temprature")
            response_text=json.loads(response.text)
            print("Response received is :" + str(response_text['message']))
            print("This is the response ",response)
            count =0
        elif sensor_value < bound[1]:
            print ("The temprature is decreasing , Sending Alert message!")
            response=email.send_email("Alert","It is getting too cold, maintain the temprature to avoid freezing of meds")
            response_text=json.loads(response.text)
            print("Response received is :" + str(response_text['message']))
            print("This is the response ",response)
            count =0
        if Temp(sensor_value) > -33  and Temp(sensor_value) < -30: 
            #extra case to keep track of temprature
            #Since it must not stay between -33 to -30 for more than 20 minutes
             
            count=count+1
            if count >= 120:
                print ("The temprature is between -33 and -30 for far too long, Sending Alert message!")
                response=email.send_email("Alert","The temprature is between -33 and -30 for far too long, which is against the guideline please check your system")
                print("Response received is :" + str(response_text['message']))
                print("This is the response ",response)

        history_data.append(sensor_value);
    except Exception as e:
        print ("Error",e)
    time.sleep(10)    