from telethon import TelegramClient, events
import os
import logging
import re
import asyncio
import random
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s', level=logging.INFO)

API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
FIGHTS_ENABLED = True
FORAY_ENABLED = True
CW_BOT_ID = 408101137
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
PLAYER_RE = re.compile(r'.*Level: (\d+)', re.DOTALL)

LEVEL = 0


def send(min_level, amount, monsters):
    if not FIGHTS_ENABLED:
        return False

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
    @client.on(events.NewMessage(incoming=True, pattern=FIGHT_RE_BOTATO))
    async def fight_botato(event):
        if not event.buttons:
            return
            
        monsters_raw = event.pattern_match.group(1)
        m, s, monsters = process_monsters(monsters_raw)
        url = re.match(SHARE_FIGHT_RE, event.buttons[0][0].url).group(1)

        if send(m, s, monsters):
            await client.send_message('chtwrsbot', f'{monsters_raw}\n\n{url}')
            logging.info(f'Got fight of {s} monsters from Botato')

    @client.on(events.NewMessage(incoming=True, pattern=FIGHT_RE))
    async def fight(event):
        m, s, monsters = process_monsters(event.pattern_match.group(1))

        if send(m, s, monsters):
            await event.forward_to('chtwrsbot')
            logging.info(f'Got fight of {s} monsters')

    @client.on(events.NewMessage(chats=CW_BOT_ID, pattern='You were strolling around', incoming=True))
    async def foray(event):
        if not FORAY_ENABLED:
            return

        logging.info('Foray stopped!')
        await asyncio.sleep(random.randint(10, 100))
        event.buttons[0][0].click()

    @client.on(events.NewMessage(chats=CW_BOT_ID, pattern=PLAYER_RE, incoming=True))
    async def level(event):
        global LEVEL

        new_level = int(event.pattern_match.group(1))

        if new_level != LEVEL:
            LEVEL = new_level
            logging.info(f'Updating player level to {new_level}')

    @client.on(events.NewMessage(chats='me', pattern='/toggle_fights'))
    async def toggle_fights(event):
        global FIGHTS_ENABLED
        FIGHTS_ENABLED = not FIGHTS_ENABLED
        info = f'Setting FIGHTS to {FIGHTS_ENABLED}'
        logging.info(info)
        await event.reply(info)

    @client.on(events.NewMessage(chats='me', pattern='/toggle_foray'))
    async def toggle_foray(event):
        global FORAY_ENABLED
        FORAY_ENABLED = not FORAY_ENABLED
        info = f'Setting FORAY to {FORAY_ENABLED}'
        logging.info(info)
        await event.reply(info)

    logging.info('Connected')
    client.run_until_disconnected()
