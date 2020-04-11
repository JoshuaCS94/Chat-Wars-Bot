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

        forward = event.forward
        monsters = event.pattern_match.group(1)
    
        m = min(map(lambda l: int(l.group(3)), re.finditer(MONSTERS_RE, monsters)))
        s = sum(map(lambda l: int(l.group(1)) if l.group(1) else 1, re.finditer(MONSTERS_RE, monsters)))
    
        if s == 1 and 32 <= m <= 50:
            await event.forward_to('chtwrsbot')
            print('sending fight of 1')
            # await asyncio.sleep(500)
        if s == 2 and 32 <= m <= 35:
            await event.forward_to('chtwrsbot')
            print('sending fight of 2')
            # await asyncio.sleep(1000)
        if s == 30 and 31 <= m <= 33:
            await event.forward_to('chtwrsbot')
            print('sending fight of 3')
            # await asyncio.sleep(500)

        GET_FIGHT = True
       
    print('Connected')
    client.run_until_disconnected()
