import random, string, copy
from telegram import Message, Chat

from logger import Logger
from cache import Cache
from exceptions import FilterException
from configResponse import CreateException

class Handler (object):
    def __init__(self, children=[]):
        if isinstance(children, list):
            self.children = children
        else:
            self.children = [children]

    def extend_children(self, new_children):
        if not isinstance(new_children, list):
            new_children = [new_children]

        self.children.extend(new_children)
        self.on_children_update(new_children)

    def update(self):
        self.on_update()
        for child in self.children:
            child.update()

    def propagate(self, bot, message, target, exclude):
        res = []
        do_copy = len(self.children) > 1
        for child in self.children:
            res.extend(child.call(bot, message, target, copy.copy(exclude) if do_copy else exclude))
        return res

    def on_children_update(self, children):
        pass

    def on_update(self):
        pass

    def has_effect():
        if len(self.children) > 0:
            for child in self.children:
                if child.has_effect():
                    return True
            return False
        else:
            return False

    @classmethod
    def is_entrypoint(cls):
        raise Exception('is_entrypoint not implemented for %s' % cls)

    @classmethod
    def get_name(cls):
        raise Exception('get_name not implemented for %s' % cls)

    @classmethod
    def create(cls, stage, data, arg):
        raise CreateException('create not implemented for %s' % cls)

    @classmethod
    def create_api(cls, stage, data, arg):
        raise CreateException('create_api not implemented for %s' % cls)

class MessageHandler (Handler):
    def call(self, bot, message, target):
        raise Exception('Filter not implemented')

class RandomMessageHandler (MessageHandler):
    def __init__(self, id, children, do_cache=False):
        super(RandomMessageHandler, self).__init__(children)
        self._id = id
        Cache.config_entry(id, do_cache)

    @staticmethod
    def get_random_id(length=8):
        letters = string.ascii_lowercase + string.ascii_uppercase
        return '$' + ''.join(random.choice(letters) for i in range(length-1))

    def clear(self):
        Cache.clear(self._id)

    def add_options(self, options, get_value=None, include=None, exclude=[]):
        if isinstance(options, list):
            self._add_options(options, get_value, include, exclude)
        else:
            self._add_options([options], get_value, include, exclude)

    def _add_options(self, options, get_value, include, exclude):
        """
        options == [(k, v)] -> direct key value store
        options == [v] && get_value == None -> store values indexed
        options == [x] && get_value == lambda(x) -> store result of lambda indexed
        """

        # If no include filter is given, make sure the include filter contains all keys
        if not include:
            include = []
            for option in options:
                if isinstance(option, tuple):
                    (key, _) = option
                    include.append(key)
                else:
                    include.append(option)

        for idx, option in enumerate(options):
            idx = '%s_%d' % (self._id, idx)
            if isinstance(option, tuple):
                (key, val) = option
                if key not in include or key in include:
                    continue
                Cache.put([self._id, key], val)
            else:
                if option not in include or option in exclude:
                    continue
                if get_value is None:
                    Cache.put([self._id, idx], option)
                else:
                    # Make sure that we only apply the load action when it is not in the cache yet.
                    # This because the load action might be very expensive
                    if not Cache.contains([self._id, idx]):
                        Cache.put([self._id, idx], get_value(option))

    def select_random_option(self, exclude=[]):
        id = self._select_random_id(exclude)
        val = Cache.get([self._id, id])

        return (id, val)

    def _select_random_id(self, exclude):
        '''
        Select a random id excluding the ones in `exclude`.
        '''
        options = Cache.get(self._id)
        size = len(options)
        if size is 1:
            return next(iter(options))

        if len(exclude) is size:
            exclude = []

        keys = list(options.keys())
        while True:
            rand = random.randrange(size)
            id = keys[rand]
            if id not in exclude:
                 return id


class TickHandler (Handler):
    def __init__(self, groups, children):
        super(TickHandler, self).__init__(children)
        self.groups = groups

    def call(self, bot, time):
        res = []
        for group_id in self.groups:
            msg = Message(-1, None, time, Chat(group_id, 'tick_group %s' % group_id), text='tick @ %s' % time.strftime('%Y-%m-%d %H:%M:%S'))
            for child in self.children:
                try:
                    out = child.call(bot, msg, None, [])
                    res.extend(out)
                except FilterException:
                    continue
        return res
