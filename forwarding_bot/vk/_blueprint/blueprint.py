import logging
from asyncio import sleep

import aiohttp
from vkbottle.types.objects.messages import Message
from vkbottle.user import Blueprint

from forwarding_bot.config import data_config
from . import attachment_handlers, fwd_handlers
from .helpers import MessageHelper, RequestHelper, BadDoctypeError

logger = logging.getLogger("forwarding-bot")

bot_bp = Blueprint()


@bot_bp.on.chat_message()
async def handler(message: Message) -> None:
    """Default handler that handles every message"""
    # VK attachment limit workaround
    # Also needed to have right model parsing
    message_data = (await bot_bp.api.messages.get_by_id(message_ids=[message.id])).items[0]
    message.attachments = message_data.attachments
    message.fwd_messages = message_data.fwd_messages
    #

    request_params = RequestHelper.get_params()

    session = aiohttp.ClientSession()
    if not message.fwd_messages:
        sender = await MessageHelper.get_sender(data_config.user_token, message)
        formatted_message = "{}:\n{}".format(MessageHelper.get_name(
            sender), MessageHelper.get_text(message.text))
        attachments = MessageHelper.get_valid_attachments(message)
        try:
            if not attachments:
                await attachment_handlers.no_attachments(
                    session,
                    request_params,
                    formatted_message
                )
            elif len(attachments) == 1:
                await attachment_handlers.one_attachment(
                    session,
                    request_params,
                    formatted_message,
                    attachments[0]
                )
            else:
                await attachment_handlers.more_attachments(
                    session,
                    request_params,
                    formatted_message,
                    attachments
                )
        except BadDoctypeError as e:
            await message(str(e))
    else:
        await fwd_handlers.handle_fwd(
            session,
            request_params,
            message
        )
    await session.close()
    await sleep(0.1)
