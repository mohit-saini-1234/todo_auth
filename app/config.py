import os
from flask import Flask 
from flask_mail import Mail  
MongoUri =  "mongodb+srv://1111111111:1111111111@cluster0.tzzym.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"

app = Flask(__name__)
mail = Mail(app)

MAIL_SERVER='smtp.gmail.com'
MAIL_USERMAIL = 'mohit_saini@excellencetechnologies.info',
MAIL_PASSWORD = 'pyeyetbwpacvihwp'
MAIL_SERVER='smtp.gmail.com'
MAIL_PORT = 465
#sender's mail
sender_mail = 'mohit_saini@excellencetechnologies.info'
url_api = "(<a href =http://127.0.0.1:5000/set_pass?Email={{DATA}}>Click Here To Chnage Password</a>)"
