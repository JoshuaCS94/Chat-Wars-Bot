import os
import asyncio
import logging
import re

from telethon import TelegramClient, events
from telethon.events.newmessage import NewMessage

logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s', level=logging.WARNING)

API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')

GET_FIGHT = True
FIGHT_RE = re.compile(
    r'You met some hostile creatures\. Be careful:\n'
    r'((.|\n)+)'
    r'\n'
    r'/fight_\w+'
)
MONSTERS_RE = re.compile(r'(?:(\d) x )?\w+ (\w+) lvl\.(\d+)\n( {2}╰ .+\n)?')

def send(monsters):
    m, s = monsters

    return m >= 33 and (
        s == 1 and m <= 50 or 
        s == 2 and m <= 35 or
        s == 0 and m <= 35
    )

with TelegramClient('anon', API_ID, API_HASH) as client:
    @client.on(events.NewMessage(
        incoming=True,
        pattern=FIGHT_RE
    ))
    async def fight_handler(event):
        global GET_FIGHT
        
        if not GET_FIGHT:
            return
            
        GET_FIGHT = False

        monsters_raw = event.pattern_match.group(1)

        m = 100  # Monsters minimum level
        s = 0    # Monsters total amount

        for l in re.finditer(MONSTERS_RE, monsters_raw):
            m = min(m, int(l.group(3)))
            s += int(l.group(1)) or 1
    
        monsters = m, s

        if send(monsters):
            await event.forward_to('chtwrsbot')
            print('sending fight of %d' % s)
            # await asyncio.sleep(1000)

        GET_FIGHT = True
       
    print('Connected')
    client.run_until_disconnected()
