from dotenv import load_dotenv

load_dotenv()
from linebot.models import *
from flask import Flask, request, abort, render_template
from linebot_hooks import *
from pyngrok.conf import PyngrokConfig
from pyngrok import ngrok

# from google.cloud import speech
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import cv2
import json
import datetime
import os
import hashlib
import threading
import time
import models
import paho.mqtt.client as mqtt

# from pydub import AudioSegment
# from google.cloud import speech_v1 as speech

# Prepare web framework
app = Flask(__name__, static_url_path="/static")
app.config["TESTING"] = True
app.config["DEBUG"] = True
app.config["FLASK_ENV"] = "development"

CH_ACCESS_TOKEN = os.environ["CH_ACCESS_TOKEN"]
CH_SECRET = os.environ["CH_SECRET"]
line_bot_api = LineBotApi(CH_ACCESS_TOKEN)
handler = WebhookHandler(CH_SECRET)

notify = ""


def setup_mqtt():
    mqttc = mqtt.Client(client_id="bbfd18c2-92e0-459c-9849-1cd3fd520728")
    mqttc.username_pw_set("SVfwxncUxShtkU9CmrnJx7JqnHrNBbXM")
    mqttc.on_connect = on_connect
    mqttc.on_message = on_message
    mqttc.on_subscribe = on_subscribe
    mqttc.connect("mqtt.netpie.io", 1883, 60)
    mqttc.subscribe("@msg/report")
    mqttc.loop_forever()
    time.sleep(10)


def on_connect(client, data, flags, rc):
    print("Connected")


def on_message(client, data, msg):
    global notify
    notify = "Now " + msg.payload.decode()
    print("Topic: " + msg.topic + ": " + msg.payload.decode())


def on_subscribe(client, userdata, mid, granted_qos):
    print("Subscribed")


# Use a service account
# cred = credentials.Certificate('linehack-7ccc5-firebase-adminsdk-39yiv-7ec23db792.json')
# firebase_admin.initialize_app(cred)


def decode_json(part):
    return json.loads(open("static/flexs/flex.json", "rb").read().decode("utf8"))[part]


@app.route("/")
def liff_main():
    """ Main page rendering """
    print(request.headers)
    print(request.get_data(as_text=True))
    return render_template("main.html")


@app.route("/callback", methods=["POST"])
def callback():
    """ Main webhook for LINE """
    # get X-Line-Signature header and body
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    print("Request body: " + body)
    # handle webhook body and signature
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print(
            "Invalid signature. Please check your channel access token/channel secret."
        )
        abort(400)
    except Exception as err:
        print(err)
    return "OK"


NGROK_TOKEN = os.environ["NGROK_TOKEN"]
pyngrok_config = PyngrokConfig(region="jp")
ngrok.set_auth_token(NGROK_TOKEN)


@handler.add(BeaconEvent)
def handle_beacon_event(event):
    global notify
    if isinstance(event.source, SourceUser):
        profile = line_bot_api.get_profile(event.source.user_id)
        # encode_str = hashlib.md5(event.source.user_id.encode())
        if event.beacon.type == "enter":
            line_bot_api.push_message(
                event.source.user_id,
                [
                    TextSendMessage(
                        text=profile.display_name + " Entered beacon's reception range"
                    ),
                    TextSendMessage(text="Welcome " + profile.display_name),
                ],
            )
            if notify == "":
                print("don't have content")
            else:
                line_bot_api.push_message(event.source.user_id, TextSendMessage(text=notify))
        elif event.beacon.type == "leave":
            line_bot_api.push_message(
                event.source.user_id,
                [
                    TextSendMessage(
                        text=profile.display_name + " Left beacon's reception range."
                    ),
                    TextSendMessage(text="Bye, " + profile.display_name),
                ],
            )


@handler.add(FollowEvent)
def follow(event):
    global notify
    profile = line_bot_api.get_profile(event.source.user_id)
    line_bot_api.push_message(
        event.source.user_id, TextSendMessage(text="Hello, " + profile.display_name)
    )
    if notify == "":
        print("don't have content")
    else:
        line_bot_api.push_message(event.source.user_id, TextSendMessage(text=notify))


@handler.add(UnfollowEvent)
def unfollow(event):
    profile = line_bot_api.get_profile(event.source.user_id)
    line_bot_api.push_message(
        event.source.user_id, TextSendMessage(text="Bye Bye, " + profile.display_name)
    )


@handler.add(MessageEvent, message=TextMessage)
def message_text(event):
    global notify
    if isinstance(event.source, SourceUser):
        if event.message.text.startswith("#"):
            cmdline = event.message.text[1:]
            cmdargs = cmdline.split(" ")
            if cmdargs[0] == "print":
                if cmdargs[1] == "user":
                    line_bot_api.reply_message(
                        event.reply_token, TextSendMessage(text=event.source.user_id)
                    )
                elif cmdargs[1] == "echo":
                    line_bot_api.reply_message(
                        event.reply_token, TextSendMessage(text=event.message.text)
                    )
                else:
                    line_bot_api.reply_message(
                        event.reply_token, TextSendMessage(text="I don't understand")
                    )
            elif cmdargs[0] == "capture":
                cap = cv2.VideoCapture(0)
                _, frame = cap.read()
                name = (
                        "img_"
                        + str(datetime.datetime.now())
                        .split(".")[0]
                        .replace(":", "-")
                        .replace(" ", "_")
                        + ".jpg"
                )
                cv2.imwrite(
                    os.path.join(os.path.dirname(__file__), "static/%s" % (name)), frame
                )
                new_url = endpoint + "/static/%s" % (name)
                cap.release()
                line_bot_api.reply_message(
                    event.reply_token, ImageSendMessage(new_url, new_url)
                )
            elif cmdargs[0] == "video":
                video_url = endpoint + "/static/videos/example.mp4"
                image_url = (
                        endpoint
                        + "/static/images/73470510_248452499453849_7973059271739767259_n.jpg"
                )
                line_bot_api.reply_message(
                    event.reply_token,
                    VideoSendMessage(
                        original_content_url=video_url, preview_image_url=image_url
                    ),
                )
            elif cmdargs[0] == "music":
                url = endpoint + "/static/audios/CALL_ME_BABY.m4a"
                line_bot_api.reply_message(
                    event.reply_token,
                    AudioSendMessage(original_content_url=url, duration=191000),
                )
            elif cmdargs[0] == "temp":
                if notify == "":
                    print("don't have content")
                else:
                    line_bot_api.push_message(event.source.user_id, TextSendMessage(text=notify))
            else:
                line_bot_api.reply_message(
                    event.reply_token, TextSendMessage(text="Error")
                )
    if isinstance(event.source, SourceRoom):
        profile = line_bot_api.get_profile(event.source.user_id)
        message = "@%s  shut up!" % profile.display_name
        line_bot_api.push_message(event.source.room_id, TextSendMessage(text=message))


if __name__ == "__main__":
    global endpoint
    bg_thread = threading.Thread(target=setup_mqtt)
    bg_thread.start()
    public_url = ngrok.connect(5001, pyngrok_config=pyngrok_config)
    print(public_url)
    endpoint = public_url.public_url
    endpoint = endpoint.replace("http://", "https://")
    line_bot_api.set_webhook_endpoint(endpoint + "/callback")
    app.run(port=5001, use_reloader=False)
