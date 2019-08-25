from flask import Flask, request, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, desc

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
import datetime


app = Flask(__name__)

# Get enviroment variables
## Line
CHANNEL_ACCESS_TOKEN = os.environ['CHANNEL_ACCESS_TOKEN']
CHANNEL_SECRET = os.environ['CHANNEL_SECRET']

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

## Database
db_uri = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
db = SQLAlchemy(app)


class Account(db.Model):
    __tablename__ = 'accounts'
    id = db.Column(db.Integer, primary_key=True)
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
    
    message = event.message.text.split(' ')

    if message[0] == 'add':
        add_account(message)
        result = '追加しました！'
        # push_message(event, '追加しました！')
    elif message[0] == 'delete':
        delete_account()
        result = '消しました！'
        # push_message(event, '消しました！')
    elif message[0] == 'summary':
        result = get_summary()
        # push_message(event, get_summary())
    else:
        result = 'こんにちは！'

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text = result)
    )


def add_account(message):
    account = Account()

    if len(message) == 4:
        account.date = message[3]
    else:
        account.date = datetime.date.today().isoformat()
    account.amount = int(message[2])
    account.type = message[1]
    
    db.session.add(account)
    db.session.commit()

def delete_account():
    account = db.session.query(Account).order_by(desc(Account.id)).first()
    db.session.delete(account)
    db.session.commit()

def get_summary():
    mes = ''
    dt = datetime.datetime.today()
    first_date = dt.date() - datetime.timedelta(days=dt.day - 1)

    month_total = 0
    # where
    accounts = db.session.query(Account.type, func.sum(Account.amount)).filter(Account.date >= first_date).group_by(Account.type)
    for account in accounts:
        month_total += account[1]
        mes += account[0] + ' \\' + '{:,}'.format(str(account[1])) + '\n'
    mes += '----------\n'
    mes += '月合計 \\' + '{:,}'.format(str(month_total)) + '\n'

    accounts = db.session.query(func.sum(Account.amount))
    for account in accounts:
        mes += '合計 \\' + '{:,}'.format(str(account[0]))

    return mes

def push_message(event, message):
    line_bot_api.push_message(
            line_bot_api.get_profile(event.source.user_id).user_id,
            TextSendMessage(text = message)
        )

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    # app.run(host='0.0.0.0', port=port, debug=True)
    app.run(host='0.0.0.0', port=port)

