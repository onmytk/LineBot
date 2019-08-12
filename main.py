from flask import Flask, request, abort
from flask_sqlalchemy import SQLAlchemy

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage
)

import os


app = Flask(__name__)

# Get enviroment variables
CHANNEL_ACCESS_TOKEN = os.environ['CHANNEL_ACCESS_TOKEN']
CHANNEL_SECRET = os.environ['CHANNEL_SECRET']

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

db_uri = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
db = SQLAlchemy(app)


class Account(db.Model):
    __tablename__ = 'accounts'
    date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(), nullable=False)


# Webhook from LINE
@app.route('/callback', methods=['POST'])
def callback():
    # Get signature from request header
    signature = request.headers['X-Line-Signature']

    # Get request body
    body = request.get_data(as_text=True)
    app.logger.info('Request body: ' + body)

    # Verification signature
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    
    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text = event.message.text)
    )

def add_account():
    pass

def delete_account():
    pass

def get_summary():
    pass

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

