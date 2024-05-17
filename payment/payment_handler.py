import os

import requests
import json
from dotenv import load_dotenv
import uuid
load_dotenv()
"""
Class that generates the appropriate payment through the MercadoPago api

Attributes
----------

api_url: static String
    http url to access the api

method: String
    string representing the payment method. always "pix"

payerData: dict
    dictionary with necessary personal information to generate payment. Needs keys email, first_name, last_name
and identification

currentPayment: String | None
    id of ongoing payment, stored as a string.

publicKey: String
    public key needed to acces MercadoPago api

headers: dict
    http header with the necessary information for every request. Contains the access token for autorization
and the type of the sent data (json)

"""
class PaymentManager:
    api_url = "https://api.mercadopago.com/v1/payments"
    def __init__(self):
        self.method = "pix"
        self.currentPayment = None
        self.headers = {
        'Authorization': f'Bearer {os.getenv("access_token")}',
        'Content-Type': 'application/json'
        }

    """
        Method to set the appropriate payment keys
    """

    def hasPaymentKeys(self):
        return self.headers != None

    """
        Method to create a qrcode for payment of specific amounts. It returs
    True or False depending on success of the request
    """
    def createPayment(self, time_rented):
        from datetime import datetime, timedelta
        expiration = datetime.now() + timedelta(minutes=10)
        date_of_expiration = expiration.astimezone().isoformat(timespec='milliseconds')
        print(date_of_expiration)
        data = {
                "transaction_amount": int(time_rented)*0.01,
                "payment_method_id": self.method,
                "payer": {
                    "email": "customer@parasunflower.com",
                    "first_name": "Parasun",
                    "last_name": "Flower",
                    "identification": {
                        "type": "CPF",
                        "number": "01234567890"
                    }
                },
                "date_of_expiration": date_of_expiration
        }
        # print(f'"date_of_expiration": {date_of_expiration}')
        header = self.headers
        header["X-Idempotency-Key"] = str(uuid.uuid4())
        response = requests.post(PaymentManager.api_url, data=json.dumps(data), headers=header)
        if response.status_code in [201, 200]:
            json_resp = response.json()
            return json_resp, response.status_code
        else:
            print(response.content)
            print(response.text)

        return 0, response.status_code

    """
        Method to check if the last payment created is still valid
    """
    def checkPayment(self, payment_id):
        response = requests.get(PaymentManager.api_url + '/' + payment_id, headers=self.headers)
        if response.status_code not in [201, 200]:
            return 0, response.status_code
        json_resp = response.json()
        return json_resp, response.status_code

    def cancelPayment(self):
        if self.currentPayment == None:
            return None
        response = requests.put(PaymentManager.api_url + '/' + str(self.currentPayment), headers=self.headers, data=json.dumps({"status":"cancelled"}))