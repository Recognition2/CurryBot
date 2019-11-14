from messageHandler import MessageHandler, RandomMessageHandler
from configResponse import Send, Done, AskChild, CreateException
import re


class AbstractSendMessage (RandomMessageHandler):
    def __init__(self, messages, parse_mode, show_preview):
        super(AbstractSendMessage, self).__init__(RandomMessageHandler.get_random_id(), [])
        self.add_options(messages)
        self.parse_mode = parse_mode
        self.show_preview = show_preview

    def apply_message(self, message_text, reply_text):
        '''
        Given the original message and the reply text pattern,
        try filling in the holes in the reply pattern.
        '''
        if '%s' in reply_text:
            return reply_text % message_text
        else:
            return reply_text

    def call(self, bot, msg, target, exclude):
        (id, message) = self.select_random_option(exclude=exclude)
        applied_message = self.apply_message(msg.text, message)
        bot.send_message(chat_id=msg.chat.id,
                         text=applied_message,
                         reply_to_message_id=target,
                         parse_mode=self.parse_mode,
                         disable_web_page_preview=not self.show_preview)
        return [id]

    def has_effect():
        return True

    @classmethod
    def is_entrypoint(cls):
        return False

    @classmethod
    def create(cls, stage, data, arg):
        if stage is 0:
            return (1, None, Send('Please send me the text to reply'))
        elif stage is 1 and arg:
            if not arg.text:
                return (1, None, Send('Please reply with text, not with something else'))
            return (2, arg.text, Send('Should previews be shown for URLs?'))
        elif stage is 2 and arg:
            if not arg.text or not re.match(r'yes|no', arg.text):
                return (2, data, Send('Please reply with yes or no'))
            return (-1, None, Done(cls._create(data, arg.text == 'yes')))
        else:
            print(stage, data, arg)
            raise CreateException('Invalid create state for sendTextMessage')


class SendTextMessage (AbstractSendMessage):
    def __init__(self, message, show_preview=True):
        super(SendTextMessage, self).__init__(message, parse_mode=None, show_preview=show_preview)

    @classmethod
    def get_name(cls):
        return 'Send a message'

    @classmethod
    def _create(cls, msg, show_preview):
        return SendTextMessage(msg, show_preview)

class SendMarkdownMessage (AbstractSendMessage):
    def __init__(self, message, show_preview=True):
        super(SendMarkdownMessage, self).__init__(message, parse_mode='Markdown', show_preview=show_preview)

    @classmethod
    def get_name(cls):
        return "Send Markdown formatted message"

    @classmethod
    def _create(cls, msg, show_preview):
        return SendMarkdownMessage(msg, show_preview)

class SendHTMLMessage (AbstractSendMessage):
    def __init__(self, message, show_preview=True):
        super(SendHTMLMessage, self).__init__(message, parse_mode='HTML', show_preview=show_preview)

    @classmethod
    def get_name(cls):
        return "Send HTML formatted message"

    @classmethod
    def _create(cls, msg, show_preview):
        return SendHTMLMessage(msg, show_preview)


class Forward (MessageHandler):
    '''
    An action that forwards a message.
    '''

    def __init__(self, chat_id, msg_id):
        '''
        Load all the messages from the given config
        '''
        super(ForwardAction, self).__init__([])
        self.chat_id = chat_id
        self.msg_id = msg_id

    def call(self, bot, msg, target, exclude):
        if target:
            raise Exception('You cannot reply using a forwarded message')
        bot.forward_message(chat_id=msg.chat.id, from_chat_id=self.chat_id, message_id=self.msg_id)
        return [self.id]

    @classmethod
    def is_entrypoint(cls):
        return False

    @classmethod
    def get_name(cls):
        return "Forward a message"
