""" Exercise with Flask, example of API server and digital signature using JWS

 - Elliptic curve ECDSA. Generate keys for signing data
 - Sign data and verify it
 - QR utilities for easy reading from mobile devices
"""

from flask import Flask, jsonify
from flask_restful import reqparse, abort, Api, Resource

import jws
import qrcode # QR maker
import base64
import numpy as np
import cv2, io # QR reader
from PIL import Image
import ecdsa
import requests
import codecs
import binascii


# Generate key pair
def generate_keys():
    sk256 = ecdsa.SigningKey.generate(curve=ecdsa.NIST256p)
    public = sk256.verifying_key
    return sk256, public

known_tokens = {}
sk256, vk = generate_keys() # Curve, public

# Converting to strings
vk_str = vk.to_string()
sk_str = sk256.to_string()

app = Flask(__name__)
api = Api(app)


################################################################################################
#####################################  UTILS  ##################################################

def sign_data(payload, priv_key = sk256):
    header = { 'alg': 'ES256' }
    sig = jws.sign(header, payload, priv_key)
    return payload, sig, vk
    
def verify_data(payload, sig, vk = vk):
    header = { 'alg': 'ES256' }
    try:
        verified = jws.verify(header, payload, sig, vk)
    except jws.SignatureError:
        print("Validation Error")
        return False
    return verified

# QR STUFF
def generate_qr(content):
    img = qrcode.make(content).convert("L")
    img.save("/tmp/qr-tmp.png")
    
    buffered = io.BytesIO()
    img.save(buffered, format="png")
    img_str = base64.b64encode(buffered.getvalue())
    return img_str

def qr_image(img_str):
    return "data:image/png;base64,"+img_str.decode("ascii")

def read_qr(content):
    stream = io.BytesIO(content)
    img = np.asarray(Image.open(stream))
    detector = cv2.QRCodeDetector()
    data, _, _ = detector.detectAndDecode(img)
    return data

def create_token():
    import time
    import hashlib
    global known_tokens
    
    token = hashlib.sha256(str(time.time()).encode("ascii")).hexdigest()
    known_tokens[token] = False
    return token

def unhexlify(hexdigest):
    return binascii.hexlify(hexdigest)

def hexlify(hex_data):
    return codecs.encode(hex_data, "hex").decode("ascii")

#########################################

class Show(Resource):
    def get(self):
        token = create_token()
        qr_base64 = qr_image(generate_qr(token))
        params = {"data":qr_base64}
        _, sig, _ = sign_data(params)
        
        params["token"] = token
        params["sign"] = hexlify(sig)
        params["vk"] = hexlify(vk_str)

        return params


# Define parser and request args
parser = reqparse.RequestParser()
parser.add_argument('token', type=str)
parser.add_argument('sign', type=str)
parser.add_argument('vk', type=str)
        
class Register(Resource):
    def post(self):
        args = parser.parse_args()
        if args["token"] in known_tokens:
            if verify_data({"token":args["token"]}, args["sign"], args["vk"]):
                known_tokens[args["token"]] = time.time()
                return jsonify({"result":"OK"})
        else:
            return jsonify({"error":f"Token {args['token']} not known"})

        return jsonify({"error":"Not approved"})

class ShowApp(Resource):
    def get(self):
        return None

# ROUTING
api.add_resource(Show, '/')
api.add_resource(Register, '/enter')
api.add_resource(ShowApp, '/app/<path>')

if __name__ == '__main__':
    app.run(debug=True)

