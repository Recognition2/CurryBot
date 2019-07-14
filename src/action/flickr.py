from action.action import Action
from cache import Cache
from logger import Logger

import requests

class FlickrAction (Action):
    '''
    An action that sends images from Flickr albums when triggered.
    '''

    def __init__(self, id, api_key, pack, include=None, exclude=None):
        '''
        Initialize a FlickrAction by preloading the images in the given albums.
        '''
        super(FlickrAction, self).__init__(id)
        self.key = api_key
        self.pack = pack
        self.include = include
        self.exclude = exclude

        self.update()

    def update(self):
        Logger.log_debug('Updating cache of %s' % self.id)
        flickr_album = self.make_request('flickr.photosets.getPhotos', 'photoset', {'photoset_id': self.pack})
        name = flickr_album['title']
        images = list(map(lambda x: x['id'], flickr_album['photo']))

        include = self.include if self.include else images
        exclude = self.exclude if self.exclude else []
        self.load_and_append_ids(images, (lambda id, self=self: self.load_image(id)), include=include, exclude=exclude, cache=True)

    def load_image(self, id):
        '''
        Load an image from the given id.
        '''
        Logger.log_debug('Requesting image with id %s' % id)
        try:
            photo = self.make_request('flickr.photos.getInfo', 'photo', {'photo_id': id})
            title = photo['title']['_content']
            description = photo['description']['_content']
            url = photo['urls']['url'][0]['_content']
            return {'title': title, 'description': description, 'url': url, 'cache': None}
        except:
            return None

    def make_request(self, method, expected, args={}):
        '''
        Make a request to the Flickr API
        '''
        arg_string = ""
        for arg in args:
            arg_string += '&%s=%s' % (arg, args[arg])
        response = requests.get('https://api.flickr.com/services/rest/?method=%s&api_key=%s%s&format=json&nojsoncallback=1' % (method, self.key, arg_string)).json()
        if expected not in response:
            print('ERROR')
            print(response)
        return response[expected]

    def select_reply(self, exclude):
        (id, image) = self.select_random_option(exclude=exclude)
        msg = '<a href="%s">📷</a>' % image['url']
        return (id, msg)

    def dispatch(self, bot, msg, exclude):
        (id, text) = self.select_reply(exclude)
        bot.send_message(chat_id=msg.chat.id, text=text, parse_mode='HTML')
        return [id]

    def dispatch_reply(self, bot, msg, reply_to, exclude):
        (id, text) = self.select_reply(exclude)
        bot.send_message(chat_id=msg.chat.id, text=text, reply_to_message_id=reply_to, parse_mode='HTML')
        return [id]