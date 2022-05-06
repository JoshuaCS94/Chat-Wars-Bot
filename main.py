from telethon import TelegramClient, events
import os
import logging
import re
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s', level=logging.WARNING)

API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
FIGHTS_ENABLED = True
FORAY_ENABLED = True
FIGHT_RE = re.compile(
    r'You met some hostile creatures\. Be careful:\n'
    r'((.|\n)+)'
    r'\n'
    r'/fight_\w+'
)
FIGHT_RE_BOTATO = re.compile(
    r'.* has found some monsters:\n'
    r'\n'
    r'((.|\n)+)'
)
SHARE_FIGHT_RE = re.compile(r'https://t\.me/share/url\?url=(/fight_.+)')
MONSTERS_RE = re.compile(r'(?:(\d) x )?\w+ (\w+) lvl\.(\d+)(\n {2}╰ .+\n)?\n?')
MONSTERS_TYPES = ['Collector', 'Sentinel', 'Alchemist', 'Ranger', 'Blacksmith', 'Knight', 'Boar', 'Wolf', 'Bear']

LEVEL = 39


def send(min_level, amount, monsters):
    m, s = min_level, amount

    bears = monsters['Bear']
    wolves = monsters['Wolf']
    boars = monsters['Boar']
    knights = monsters['Knight']
    beasts = bears or wolves or boars

    if m < LEVEL - 10:
        return False

    if s == 1:
        return not bears and m <= LEVEL + 15 or m <= LEVEL + 10

    if s == 2:
        if beasts:
            return not bears and m <= LEVEL + 3 or bears == 1 and m <= LEVEL
        else:
            return not knights and m <= LEVEL + 10 or knights == 1 and m <= LEVEL or m <= LEVEL - 5

    if s == 3:
        return not beasts and (not knights and m <= LEVEL - 5 or m <= LEVEL - 8)


def process_monsters(monsters_raw):
    monsters = {m: 0 for m in MONSTERS_TYPES}
    m = 100  # Monsters minimum level
    s = 0    # Monsters total amount

    for l in re.finditer(MONSTERS_RE, monsters_raw):
        amount = int(l.group(1) or 1)
        monster = l.group(2)
        level = int(l.group(3))

        m = min(m, level)
        s += amount
        monsters[monster] = amount

    return m, s, monsters


with TelegramClient('anon', API_ID, API_HASH) as client:
    @client.on(events.NewMessage(
        incoming=True,
        pattern=FIGHT_RE_BOTATO
    ))
    async def fight_handler_botato(event):
        if not event.buttons:
            return
            
        monsters_raw = event.pattern_match.group(1)
        m, s, monsters = process_monsters(monsters_raw)
        url = re.match(SHARE_FIGHT_RE, event.buttons[0][0].url).group(1)

        if send(m, s, monsters):
            await client.send_message('chtwrsbot', '%s\n%s' % (monsters_raw, url))
            print('sending fight of %d' % s)

    @client.on(events.NewMessage(
        incoming=True,
        pattern=FIGHT_RE
    ))
    async def fight_handler(event):
        m, s, monsters = process_monsters(event.pattern_match.group(1))

        if send(m, s, monsters):
            await event.forward_to('chtwrsbot')
            print('sending fight of %d' % s)

    print('Connected')
    client.run_until_disconnected()
