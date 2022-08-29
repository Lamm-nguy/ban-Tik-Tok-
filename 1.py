import argparse
import asyncio
import contextlib
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

import aiofiles
import requests
from colorama import Fore, init

init(autoreset=True)

TIKTOK_ENDPOINT = "https://www.tiktok.com/@{}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US",
    "Content-Type": "application/json"
}


THREAD_LOCK = Lock()


def ensure_outfile() -> None:
    if not os.path.exists("./results"):
        os.mkdir("./results")
        open("./results/banned.txt", 'w')


def output_available(result: tuple[str, int]) -> None:
    username, status = result
    THREAD_LOCK.acquire()
    if (status == 404):
        print(f"[  {Fore.LIGHTRED_EX}BAN  {Fore.RESET}] -> {username}")
        with open("./results/banned.txt", 'a') as of:
            of.write(str(username + '\n'))
            of.close()
    elif (status == 403):
        print(f"[  {Fore.LIGHTRED_EX}RATELIMIT  {Fore.RESET}] -> {username}")
    else:
        print(f"[ {Fore.LIGHTGREEN_EX}LIVE {Fore.RESET}] -> {username}")
    THREAD_LOCK.release()


def check_user(usernames: list[str], session: requests.Session) -> None:
    for username in usernames:
        with contextlib.suppress(requests.exceptions.SSLError, requests.exceptions.ConnectionError):
            with session.head(TIKTOK_ENDPOINT.format(username), headers=HEADERS) as resp:
                output_available((username, resp.status_code))


async def start() -> None:
    global USERNAMES
    async with aiofiles.open(WORDLIST, mode='r') as infile:
        USERNAMES = [line.strip() for line in await infile.readlines()]
        USERNAMES = [USERNAMES[x:x + int(THREADS + 1)]
                     for x in range(0, len(USERNAMES), int(THREADS + 1))]
    ensure_outfile()
    with requests.Session() as session:
        with ThreadPoolExecutor(max_workers=int(THREADS)) as executor:
            for sublist in USERNAMES:
                executor.submit(check_user, sublist, session)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(sys.argv[0], description="github.com/9sv")
    parser.add_argument("wordlist", action="store")
    WORDLIST = (parser.parse_args()).wordlist
    THREADS = int(
        input(f"[{Fore.LIGHTBLUE_EX} Worker Count {Fore.RESET}] -> "))
    THREADS = 5 if THREADS >= 5 else THREADS  # Avoid rate limits to keep proxyless
    asyncio.run(start())
