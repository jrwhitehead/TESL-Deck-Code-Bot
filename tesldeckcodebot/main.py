from bot import TESLDeckCodeBot
import argparse

print('deck-code-bot # Initialising...')
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='The Elder Scrolls: Legends Deck Code bot for Reddit.')
    # No default value to prevent accidental mayhem
    parser.add_argument('-s', '--target_sub', required=True, help='What subreddit will this instance monitor?')

    args = parser.parse_args()

    print('deck-code-bot # Started lurking in (/r/{})'.format(args.target_sub))
    bot = TESLDeckCodeBot(author='NotGooseFromTopGun', target_sub=args.target_sub)
    bot.start(batch_limit=10, buffer_size=1000)
    print('deck-code-bot # Stopped running.')
