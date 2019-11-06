import requests, random, praw, re, os, time

from collections import OrderedDict

class DeckCode:
    DECK_CODE_IMAGE_BASE_URL = '(http://tesl-decks.markjfisher.net/image/{})'

    @staticmethod
    def remove_duplicates(seq):
        seen = set()
        seq_no_dupes = []
        if type(seq) == list:
            for x in seq:
                if x not in seq_no_dupes:
                    seq_no_dupes.append(x)                
            return seq_no_dupes
        elif type(seq) == str:
            no_dupes_response = []
            for line in seq.splitlines():
                if line not in seen or line == "":
                    seen.add(line)
                    no_dupes_response.append(line)
            seq = '\n'.join(no_dupes_response)
            return seq  
        else:
            return seq  

    def __init__(self, name, img_url):
        self.name = name
        self.img_url = img_url

class TESLDeckCodeBot:

    CODE_MENTION_REGEX = re.compile(r'(?<!\/)SPA[A-Za-z]{20,}')

    @staticmethod
    def find_deckcode_mentions(s):

        return DeckCode.remove_duplicates(TESLDeckCodeBot.CODE_MENTION_REGEX.findall(s))

    def _get_praw_instance(self):
        r = praw.Reddit(client_id=os.environ['CLIENT_ID'],
                        client_secret=os.environ['CLIENT_SECRET'],
                        user_agent='Python TESL Deck Code Bot v.001 u/TESL-Deck-Code-bot',
                        username=os.environ['REDDIT_USERNAME'],
                        password=os.environ['REDDIT_PASSWORD'])
        return r

    def _process_submission(self, s):
        deckcodes = TESLDeckCodeBot.find_deckcode_mentions(s.selftext)
        if len(deckcodes) > 0 and not s.saved:
            try:
                deckcodes = list(dict.fromkeys(deckcodes))
                self.log('Commenting in post by {} titled "{}" about the following deckcodes: {}'.format(s.author, s.title, deckcodes))
                response = self.build_response(deckcodes, s.author)
                s.reply(response)
                s.save()
                self.log('Done commenting and saved thread.')
            except PrawcoreException as e:
                self.log('There was an error while trying to reply so I\'m going to wait 60 seconds before trying again.')
                self.log(e)
                time.sleep(60)

    def _process_comment(self, c):
        deckcodes = TESLDeckCodeBot.find_deckcode_mentions(c.body)
        if len(deckcodes) > 0 and not c.saved and c.author != os.environ['REDDIT_USERNAME']:
            try:
                deckcodes = list(dict.fromkeys(deckcodes))
                self.log('Replying to {} in comment id {} about the following deckcodes: {}'.format(c.author, c.id, deckcodes))
                response = self.build_response(deckcodes, c.author)
                c.reply(response)
                c.save()
                self.log('Done replying and saved comment.')
            except PrawcoreException as e:
                self.log('There was an error while trying to reply so I\'m going to wait 60 seconds before trying again.')
                self.log(e)
                time.sleep(60)

    # TODO: Make this template-able, maybe?
    def build_response(self, deckcodes, author):
        self.log('Building response.')
        response = (''' Hi {}, here are your deck code image links: \n\n'''.format(author))
        too_long = None
        deckcode_quantity = 0
        deckcodes_found = 0
		
        for code in deckcodes:
            #code = DeckCode.DECK_CODE_IMAGE_BASE_URL.format(code)
            if deckcodes != None:
                if len(deckcodes) > 10: # just making sure the comment isn't too long
                    deckcodes_found += int(len(deckcodes)) - 10
                    deckcodes = deckcodes[:10]
                    too_long = True
                for dcode in deckcodes:
                    dcode = DeckCode.DECK_CODE_IMAGE_BASE_URL.format(dcode)
                    if (str(dcode)) not in response:
                        response += '[{}]{}\n\n\n'.format(deckcodes.index(dcode), str(dcode))

        if too_long == True:
            response += '\n Your query matched with too many deckcodes. {} further results were omitted. I only link 10 at a time.\n\n'.format(deckcodes_found)

        response += '\n\n\n^(_Hi, I\'m a bot. Thanks to fenrock369 for creating this awesome webservice._)\n' \
                    '\n\n[^Send ^PM](https://www.reddit.com/message/compose/?to={})'.format(self.author)
					
        if len(response) > 10000:
            response = 'I\'m afraid your query created a reply that was too long.\n\n' \
                       'Try entering less deckcodes in your comment/post and I\'ll consider replying.'
        return response

    def log(self, msg):
        print('TESL-Deck-Code-bot # {}'.format(msg))

    def start(self, batch_limit=10, buffer_size=1000):
        r = None
        try:
            r = self._get_praw_instance()

        except PrawcoreException as e:
            self.log('Reddit seems to be down! Aborting.')
            self.log(e)
            return

        already_done = []
        #subreddit = r.subreddit(self.target_sub)

        while True:
            try:
		        # Updated the method of acquiring comments and submission as new submissions were not being caught
		        # Method from here: https://www.reddit.com/r/redditdev/comments/7vj6ox/can_i_do_other_things_with_praw_while_reading/dtszfzb/?context=3
                new_submissions = r.subreddit(self.target_sub).stream.submissions(pause_after=-1) 
                new_comments = r.subreddit(self.target_sub).stream.comments(pause_after=-1)

            except PrawcoreException as e:
                self.log('Reddit seems to be down! Aborting.')
                self.log(e)
                return

            for s in new_submissions:
                if s is None:
                    break
                self._process_submission(s)
                # The bot will also save submissions it replies to to prevent double-posting.
                already_done.append(s.id)
            for c in new_comments:
                if c is None:
                    break
                self._process_comment(c)
                # The bot will also save comments it replies to to prevent double-posting.
                already_done.append(c.id)

            # If we're using too much memory, remove the bottom elements
            if len(already_done) >= buffer_size:
                already_done = already_done[batch_limit:]

    def __init__(self, author='Anonymous', target_sub='all'):
        self.author = author
        self.target_sub = target_sub
