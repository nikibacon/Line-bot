from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib.auth.models import User
from .models import UserProfile

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import (
    MessageEvent, FollowEvent, PostbackEvent,
    TextMessage,
    PostbackAction,
    TextSendMessage, TemplateSendMessage,
    ButtonsTemplate
    )

line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(settings.LINE_CHANNEL_SECRET)


@csrf_exempt
def callback(request):
    if request.method == 'POST':
        # get X-Line-Signature header value
        signature = request.META['HTTP_X_LINE_SIGNATURE']

        # get request body as text
        body = request.body.decode('utf-8')

        # handle webhook body
        try:
            handler.handle(body, signature)
        except InvalidSignatureError:
            return HttpResponseBadRequest()
        return HttpResponse()
    else:
        return HttpResponseBadRequest()


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text))


@handler.add(FollowEvent)
def handle_follow(event):
    line_id = event.source.user_id
    profile = line_bot_api.get_profile(line_id)
    profile_exists = User.objects.filter(username=line_id).count() != 0
    if profile_exists:
        user = User.objects.get(username=line_id)
        user_profile = UserProfile.objects.get(user=user)
        user_profile.line_name = profile.display_name
        user_profile.line_picture_url = profile.picture_url
        user_profile.line_status_message = profile.status_message
        user_profile.unfollow = False
        user_profile.save()
    else:
        user = User(username=line_id)
        user.save()
        user_profile = UserProfile(
            line_id=line_id,
            line_name=profile.display_name,
            line_picture_url=profile.picture_url,
            line_status_message=profile.status_message,
            user=user
        )
        user_profile.save()
    buttons_template_message = TemplateSendMessage(
        alt_text='Product Promotion',
        template=ButtonsTemplate(
            title="Product Promotion",
            text='Do you want to receive the promotion messages?',
            actions=[
                PostbackAction(
                    label='yes',
                    display_text='yes',
                    data='promotion=true'
                ),
            ]
        )
    )
    line_bot_api.reply_message(
        event.reply_token,
        [
            TextSendMessage(text="Hello\U0010007A"),
            buttons_template_message,
        ]
    )


@handler.add(PostbackEvent)
def handle_postback(event):
    line_id = event.source.user_id
    if event.postback.data == "promotion=true":
        line_id = event.source.user_id
        user_profile = User.objects.get(line_id=line_id)
        user_profile.promotable = True  # set promotable to be True
        user_profile.save()

        line_bot_api.reply_message(
                    event.reply_token,
                    [
                        TextSendMessage(text="Thanks\U0010007A"),
                    ]
                )
    elif event.postback.data == "action=nextpage":
        line_bot_api.link_rich_menu_to_user(line_id, "richmenu-fcbc6982734de2b56a7a0753fec90112")
    elif event.postback.data == "action=previouspage":
        line_bot_api.link_rich_menu_to_user(line_id, "richmenu-c47ec4cc9430633f302f4d48c2b9a1e4")

