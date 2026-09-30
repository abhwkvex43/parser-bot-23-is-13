"""
Safe message editing helper.

Aiogram's edit_text() crashes on media messages (video/audio/document) with
"Bad Request: there is no text in the message to edit". This helper tries
edit_text first, then falls back to edit_caption (for media messages),
then to delete + resend (last resort).
"""
import logging

from aiogram.exceptions import TelegramBadRequest

logger = logging.getLogger(__name__)


async def safe_edit(message, text: str, **kwargs):
    """Edit a message's text or caption, handling media messages gracefully.

    Drop-in replacement for message.edit_text(text, **kwargs).
    Tries edit_text → edit_caption → delete+resend.
    """
    try:
        await message.edit_text(text, **kwargs)
    except TelegramBadRequest as e:
        err = str(e).lower()
        if "no text in the message to edit" in err or "message is not modified" in err:
            # Media message — use edit_caption instead
            try:
                # edit_caption uses 'caption' not 'text'; reply_markup passes through
                await message.edit_caption(caption=text, **kwargs)
            except TelegramBadRequest as e2:
                if "message is not modified" in str(e2).lower():
                    return  # Content unchanged — silently skip
                # Last resort: delete and resend
                try:
                    await message.delete()
                except Exception:
                    pass
                reply_markup = kwargs.pop("reply_markup", None)
                await message.answer(text, reply_markup=reply_markup)
        elif "message is not modified" in err:
            return  # Content unchanged — silently skip
        else:
            raise
