# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import sys
import traceback
import uuid
import os
import pycron
import time
import requests
from urllib.parse import urljoin
from urllib.request import pathname2url
from datetime import datetime
from http import HTTPStatus
from typing import Dict

from aiohttp import web
from aiohttp.web import Request, Response, json_response
from botbuilder.core import (
    BotFrameworkAdapterSettings,
    TurnContext,
    BotFrameworkAdapter,
    CardFactory,
    MessageFactory,
)
from botbuilder.core.integration import aiohttp_error_middleware
from botbuilder.schema import (
    Activity, 
    ActivityTypes,
    ConversationReference, 
    AnimationCard,
    Attachment,
    MediaUrl,
)

from bots import ProactiveBot
from config import DefaultConfig

CONFIG = DefaultConfig()

# Create adapter.
# See https://aka.ms/about-bot-adapter to learn more about how bots work.
SETTINGS = BotFrameworkAdapterSettings(CONFIG.APP_ID, CONFIG.APP_PASSWORD)
ADAPTER = BotFrameworkAdapter(SETTINGS)


# Catch-all for errors.
async def on_error(context: TurnContext, error: Exception):
    # This check writes out errors to console log .vs. app insights.
    # NOTE: In production environment, you should consider logging this to Azure
    #       application insights.
    print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
    traceback.print_exc()

    # Send a message to the user
    await context.send_activity("The bot encountered an error or bug.")
    await context.send_activity(
        "To continue to run this bot, please fix the bot source code."
    )
    # Send a trace activity if we're talking to the Bot Framework Emulator
    if context.activity.channel_id == "emulator":
        # Create a trace activity that contains the error object
        trace_activity = Activity(
            label="TurnError",
            name="on_turn_error Trace",
            timestamp=datetime.utcnow(),
            type=ActivityTypes.trace,
            value=f"{error}",
            value_type="https://www.botframework.com/schemas/error",
        )
        # Send a trace activity, which will be displayed in Bot Framework Emulator
        await context.send_activity(trace_activity)


ADAPTER.on_turn_error = on_error

# Create a shared dictionary.  The Bot will add conversation references when users
# join the conversation and send messages.
CONVERSATION_REFERENCES: Dict[str, ConversationReference] = dict()

# If the channel is the Emulator, and authentication is not in use, the AppId will be null.
# We generate a random AppId for this case only. This is not required for production, since
# the AppId will have a value.
APP_ID = SETTINGS.app_id if SETTINGS.app_id else uuid.uuid4()

# Create the Bot
BOT = ProactiveBot(CONVERSATION_REFERENCES)


# Listen for incoming requests on /api/messages.
async def messages(req: Request) -> Response:
    # Main bot message handler.
    if "application/json" in req.headers["Content-Type"]:
        body = await req.json()
    else:
        return Response(status=HTTPStatus.UNSUPPORTED_MEDIA_TYPE)

    activity = Activity().deserialize(body)
    auth_header = req.headers["Authorization"] if "Authorization" in req.headers else ""

    response = await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)
    if response:
        return json_response(data=response.body, status=response.status)
    return Response(status=HTTPStatus.OK)


# Listen for requests on /api/notify, and send a messages to all conversation members.
async def notify(req: Request) -> Response:  # pylint: disable=unused-argument
    print (req.query)
    print (req.rel_url.query['gif_name'])

    await _send_proactive_message(req.rel_url.query['gif_name'])
    return Response(status=HTTPStatus.OK, text="Proactive messages have been sent")

# Send a message to all conversation members.
# This uses the shared Dictionary that the Bot adds conversation references to.
async def _send_proactive_message(gif_name):
    for conversation_reference in CONVERSATION_REFERENCES.values():
        reply = MessageFactory.list([])
        reply.attachments.append(create_animation_card(gif_name))
        await ADAPTER.continue_conversation(
            conversation_reference,
            lambda turn_context: turn_context.send_activity(reply),
            APP_ID,
        )


def create_animation_card(gif_name) -> Attachment:
        file_path = os.path.join(os.getcwd(), "resources/"+gif_name+".gif")
        
        card = AnimationCard(
            
            media=[MediaUrl(url=urljoin('file:', pathname2url(file_path)))],
            title="Microsoft Bot Framework",
            subtitle="Animation Card",
        )
        return CardFactory.animation_card(card)
        
def schedule_gifs():
    print ("Inside scheduler")
    while True:
        if pycron.is_now('* * * * *'):   # True Every Sunday at 02:00
            print('running yoga gif')
            payload={'gif_name':'yoga'}
            requests.get("http://localhost:3978/api/notify",params=payload)
            time.sleep(60)               # The process should take at least 60 sec
                                        # to avoid running twice in one minute
        elif pycron.is_now('45 15 * * *'):   # True Every Sunday at 02:00
            print('running water gif')
            payload={'gif_name':'water'}
            requests.get("http://localhost:3978/api/notify",params=payload)
            time.sleep(60) 
        else:
            time.sleep(60)               # Check again in 15 seconds
    
APP = web.Application(middlewares=[aiohttp_error_middleware])
APP.router.add_post("/api/messages", messages)
APP.router.add_get("/api/notify", notify)

if __name__ == "__main__":
    try:
        #schedule_gifs()
        web.run_app(APP, host="localhost", port=CONFIG.PORT)  
    except Exception as error:
        raise error
