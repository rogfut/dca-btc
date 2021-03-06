import datetime
import logging

import azure.functions as func

import json, hmac, hashlib, time, requests, base64, os
from requests.auth import AuthBase

from sendmail import send_email

class CoinbaseExchangeAuth(AuthBase):
    def __init__(self, api_key, secret_key, passphrase):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase

    def __call__(self, request):
        timestamp = str(time.time())
        message = timestamp + request.method + request.path_url + (request.body or b'').decode()
        hmac_key = base64.b64decode(self.secret_key)
        signature = hmac.new(hmac_key, message.encode(), hashlib.sha256)
        signature_b64 = base64.b64encode(signature.digest()).decode()

        request.headers.update({
            'CB-ACCESS-SIGN': signature_b64,
            'CB-ACCESS-TIMESTAMP': timestamp,
            'CB-ACCESS-KEY': self.api_key,
            'CB-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        })
        return request


def main(mytimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()

    if mytimer.past_due:
        logging.info('The timer is past due!')

    logging.info('Python timer trigger function ran at %s', utc_timestamp)

    api_url = 'https://api.pro.coinbase.com/'
    auth = CoinbaseExchangeAuth(os.environ['API_KEY'], os.environ['SECRET_KEY'], os.environ['PASSPHRASE'])

    def deposit_from_bank(amount, currency, payment_id):
        payment_obj = {
            'amount': amount,
            'currency': currency,
            'payment_method_id': payment_id
        }
        response = requests.post(api_url + 'deposits/payment-method', json=payment_obj, auth=auth)
        return response.json()

    # make deposit
    logging.info('Making a live deposit to coinbase amount: %s', os.environ['DEPOSIT_AMOUNT'])
    deposit = deposit_from_bank(os.environ['DEPOSIT_AMOUNT'], "USD", os.environ['ACCOUNT_ID'])
    logging.info('Response from Coinbase:\n %s', deposit)

    deposit_response_dict = json.loads(deposit)
    if "payout_at" in deposit_response_dict:
        # send mail with details
        send_email(
            os.environ['FROM_EMAIL'],
            os.environ['TO_EMAILS'],
            'CoinbasePro Deposit Successful',
            "<h1>Deposited {value} to CoinbasePro</h1>".format(value=os.environ['DEPOSIT_AMOUNT'])
        )
    else:
        # send failure mail with details
        send_email(
            os.environ['FROM_EMAIL'],
            os.environ['TO_EMAILS'],
            'Coinbase Purchase Failed',
            '<h1>Unable to complete purchase. Check error logs in azure</h1>'
        )