import json
import os
import smtplib
import ssl
from email.mime.text import MIMEText
from random import random

import requests
import time


def main():
    print("Initializing...")

    model = os.environ['MODEL']

    query = (f'{{"query":{{"model":"{model}","condition":"new","options":{{ }},"arrangeby":"Price","order":"asc",'
             '"market":"CA","language":"en","super_region":"north america","lng":-73.9640074,"lat":45.2067646,'
             '"zip":"J0S 1T0","range":200,"region":"QC"},"offset":0,"count":50,"outsideOffset":0,'
             '"outsideSearch":false}')

    url = "https://www.tesla.com/inventory/api/v1/inventory-results?query=" + query

    # create headers

    headers = {
        "Host": "www.tesla.com",
        "Sec-Ch-Ua": "\"Chromium\";v=\"92\", \" Not A;Brand\";v=\"99\", \"Google Chrome\";v=\"92\"",
        "Sec-Ch-Ua-Mobile": "?0",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.5938.63 Safari/537.36",
        "Sec-Ch-Ua-Platform": "\"Windows\"",
        "Accept": "*/*",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": f"https://www.tesla.com/en_CA/inventory/new/{model}?arrangeby=relevance&zip=J0S%201T0&range=200",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
    }

    response = requests.get(url=url, headers=headers)

    if response.status_code == 200:
        print("Successfully retrieved tesla inventory")

        data = response.json()

        cars = data['results']

        # check to see if the dict have the keys 'approximate', if so, there is no cars
        if 'approximate' in cars:
            print("No cars found")
            return

        print("Found " + str(len(cars)) + " cars")

        # check if there is a new car
        new_cars = check_for_new_car(cars)

        # save the new data to a file
        write_to_file(cars)

        # send an email if there is a new car
        if len(new_cars) > 0:
            print("Found " + str(len(new_cars)) + " new cars")
            send_email(new_cars)
        else:
            print("No new cars found")
    else:
        print("Failed with status code: " + str(response.status_code))
        print("Response: " + response.text)


def check_for_new_car(data):
    previous_data = read_from_file()

    if previous_data is None:
        return data

    # new cars
    new_cars = []

    # list all the VINs of the previous data
    previous_vins = []
    for car in previous_data:
        previous_vins.append(str(car['VIN']))

    # check if the VIN is in the previous data
    for car in data:
        if str(car['VIN']) not in previous_vins:
            new_cars.append(car)

    return new_cars


def read_from_file():
    try:
        if os.path.exists('data.json'):
            with open('data.json') as json_file:
                return json.load(json_file)
    except Exception as e:
        print(e)
        return None


def write_to_file(data):
    with open('data.json', 'w') as outfile:
        outfile.write(json.dumps(data, indent=4))


def send_email(new_cars):
    sender = os.environ['GOOGLE_EMAIL']
    password = os.environ['GOOGLE_PASSWORD']
    receivers = os.environ['RECEIVER_EMAILS']

    # split the receivers by ;
    receivers = receivers.split(";")

    if receivers is None:
        receivers = sender

    if sender is None or password is None:
        print("Missing email or password")
        return

    body = create_email_body(new_cars)

    msg = MIMEText(body)
    msg['Subject'] = "New Tesla Inventory Found!"
    msg['From'] = sender
    try:
        simple_email_context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=simple_email_context) as server:
            server.login(sender, password)
            for receiver in receivers:
                msg['To'] = receiver
                print("Sending email to: " + receiver)
                server.sendmail(sender, receiver, msg.as_string())

    except Exception as e:
        print(e)
        return

    print("Emails sent!")


def create_email_body(new_cars):
    print("Creating email body...")
    body = "New Tesla Inventory: \n\n"
    for car in new_cars:
        model = str(car['Model'])
        vin = str(car['VIN'])
        price = str(car['PurchasePrice'])
        trim = str(car['TrimName'])
        currency = str(car['CurrencyCode'])

        print("Adding: " + model + " " + vin + "\n $" + price + " " + currency)
        body += trim + " " + vin + " " + price + "\n"
        body += "https://www.tesla.com" + "/" + "en_CA" + "/" + model + "/order/" + vin + "\n\n"

    return body


if __name__ == "__main__":
    while True:
        main()
        random_time_offset = (60 * 15) + (5 * random())
        time.sleep(random_time_offset)
