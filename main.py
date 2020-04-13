import os
import asyncio
import logging
import re
from dotenv import load_dotenv
load_dotenv()

from telethon import TelegramClient, events
from telethon.events.newmessage import NewMessage

logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s', level=logging.WARNING)

API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')

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

GET_FIGHT = True

def send(min_level, amount, monsters):
    m, s = min_level, amount

    bears = monsters['Bear']
    wolves = monsters['Wolf']
    boars = monsters['Boar']
    knights = monsters['Knight']
    beasts = bears or wolves or boars

    if m < 34:
        return False

    if s == 1:
        return not bears and m <= 55 or m <= 50

    if s == 2:
        if beasts:
            return not bears and m <= 38 or bears == 1 and m <= 36
        else:
            return not knights and m <= 46 or knights == 1 and m <= 40 or m <= 37

    if s == 3:
        return not beasts and (not knights and m <= 36 or m == 34)

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
        global GET_FIGHT
        
        if not GET_FIGHT or not event.buttons:
            return
            
        GET_FIGHT = False

        monsters_raw = event.pattern_match.group(1)
        m, s, monsters = process_monsters(monsters_raw)
        url = re.match(SHARE_FIGHT_RE, event.buttons[0][0].url).group(1)

        if send(m, s, monsters):
            await client.send_message('chtwrsbot', '%s\n%s' % (monsters_raw, url))
            print('sending fight of %d' % s)
            # await asyncio.sleep(1000)

        GET_FIGHT = True

    @client.on(events.NewMessage(
        incoming=True,
        pattern=FIGHT_RE
    ))
    async def fight_handler(event):
        global GET_FIGHT
        
        if not GET_FIGHT:
            return
            
        GET_FIGHT = False

        m, s, monsters = process_monsters(event.pattern_match.group(1))

        if send(m, s, monsters):
            await event.forward_to('chtwrsbot')
            print('sending fight of %d' % s)
            # await asyncio.sleep(1000)

        GET_FIGHT = True
       
    print('Connected')
    client.run_until_disconnected()
