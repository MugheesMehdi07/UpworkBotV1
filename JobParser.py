import asyncio
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from bardapi import Bard
from discordwebhook import Discord
from collections import deque
from queue import Queue
from threading import Thread
from datetime import datetime, date
import os
import ssl
from bs4 import BeautifulSoup
import feedparser
import re
import discord as ds
from discord.ext import commands
from models import Jobs, db, JobStatus
import time
from sqlalchemy import cast, Date

if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

# region
webhook_url = 'https://discord.com/api/webhooks/982424460378378250/Rq_ptQSWaD3um1iFkixXh7ZNf-MK7ylUMYaPzCPC6sucDr44FshPALgo0Xt0MC70XFg4'
webhook_url_test = 'https://discord.com/api/webhooks/983122713440825364/jkgqFxHPpe3yUIWeRFAmn7nP6AZncVB_C3uGMi2d-0BDCqqaQJm13365SrmR7r07lrGB'

rss_url = 'https://www.upwork.com/ab/feed/jobs/rss?category2_uid=531770282580668420%2C531770282580668419%2C531770282580668418&subcategory2_uid=1356688560628174848&location=Albania%2CArgentina%2CAustralia%2CAustria%2CBelgium%2CBritish+Virgin+Islands%2CCanada%2CDenmark%2CFinland%2CFrance%2CGeorgia%2CGermany%2CGreece%2CIreland%2CIsrael%2CItaly%2CJapan%2CLuxembourg%2CNetherlands%2CNorway%2CPanama%2CSweden%2CSwitzerland%2CUnited+Kingdom%2CUnited+States%2CAustralia+and+New+Zealand%2CEastern+Europe%2CNorthern+America%2CNorthern+Europe%2CWestern+Europe%2CEurope%2COceania&job_type=hourly%2Cfixed&budget=500-999%2C1000-4999%2C5000-&proposals=0-4%2C5-9&hourly_rate=10-&sort=recency&paging=0%3B10&api_params=1&q=&securityToken=07c870d664447cd60dc5ba83466eef1d1ac39704dcb898b65101c812dfc07be2b4e47bcbfab951936e0e48795285f3ca765fed15e392a94073e4c9ec4f52bdf0&userUid=1681609891785977856&orgUid=1681609891785977857'
add_keywords = ['']

exclude_keywords = ['shopify', 'wordpress', 'woocommerce', 'unreal', 'wix', 'webflow', 'cms', 'ui/ux',
                    'clickup', 'react native', 'laravel', 'salesforce', 'Ruby on Rails', 'ROR',
                    'ecommerce', 'crm', 'bigcommerce', 'nopcommerce', 'ux/ui', 'bubble.io', 'test', 'tester',
                    'testing', 'sqaurespace', 'Sharepoint', 'Perl', 'Squarespace', 'Data Entry', 'Typing',
                    'Word press', 'Php', 'Vba', 'Airtable']

key_index = 0
TEST = False
job_links = Queue()
discord_jobs = Queue()

if TEST:
    webhook_url = webhook_url_test

discord = None

seen_links = deque(maxlen=100)


# endregion


def fetch_jobs():
    print('Fetch Job')

    global job_links
    global seen_links

    while True:
        try:

            rss = feedparser.parse(rss_url)

            if rss.bozo:
                print("The RSS feed is not well-formed XML.")
                print("Exception: ", rss.bozo_exception)
                return
            elif 'status' not in rss or rss.status != 200:
                print(f"Failed to retrieve feed: HTTP status code {rss.status}")
                return

            rss_parsing(rss)

        except Exception as e:
            print(e)

        time.sleep(10)


def process_jobs():
    global discord_jobs
    global job_links
    global flag
    print('Process Job')
    while True:
        try:
            if flag == 'start':
                while not discord_jobs.empty():
                    job_dict = discord_jobs.get()
                    time.sleep(10)
                    broadcast_to_discord(job_dict)
                    print(f"""***********parsing following link : {job_dict}\n""")
        except Exception as e:
            print(e)


def rss_parsing(rss, us_only=""):
    global seen_links
    global job_links
    global discord_jobs
    global flag
    base_url = 'http://upworkbot.rootpointers.net/jobs/'

    try:
        print("Parsing RSS for New Links------------ ")

        for entry in rss.entries:
            title = entry.title
            link = entry.link
            posted_on = datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %z')
            soup = BeautifulSoup(entry.description, 'html.parser')
            description = soup.get_text(separator=' ')
            data = {
                "Job Link": link,
                "Job Title": title,
                "Job Description": description,
                "Job Posted": posted_on
            }
            if not any(
                    exclude_word.lower() in title.lower()
                    for exclude_word in exclude_keywords
            ):

                if link not in seen_links:
                    seen_links.append(link)
                    from app import app
                    with app.app_context():
                        total_jobs = Jobs.query.count()
                        if total_jobs == 5000:
                            oldest_jobs = Jobs.query.all()
                            for job in oldest_jobs:
                                db.session.delete(job)
                            db.session.commit()
                        try:
                            new_job = Jobs(job_title=data['Job Title'], job_link=data['Job Link'],
                                           job_description=data['Job Description'], posted_on=data['Job Posted'])
                            db.session.add(new_job)
                            db.session.commit()
                            today = datetime.now()
                            date_now = date.today()
                            job_status_obj = JobStatus.query.filter(
                                JobStatus.added_on.cast(db.Date) == date_now).first()
                            if job_status_obj:
                                job_status_obj.total_jobs = job_status_obj.total_jobs + 1
                                db.session.commit()
                            else:
                                job_status_obj = JobStatus(total_jobs=1, added_on=today)
                                db.session.add(job_status_obj)
                                db.session.commit()
                            qs = Jobs.query.with_entities(Jobs.id, Jobs.job_title, Jobs.job_link).order_by(
                                Jobs.created_at.desc()).first()
                        except Exception as e:
                            print('An error occurred in creating job object', str(e))

                        if qs:
                            job_dict = {
                                'id': base_url + str(qs[0]),
                                'job_title': qs[1],
                                'job_link': qs[2]
                            }
                            if flag == 'start':
                                if job_dict not in discord_jobs.queue:
                                    discord_jobs.put(job_dict)
                            if job_dict not in job_links.queue:
                                job_links.put(job_dict)
            else:
                print("Link contains excluded keywords")
    except Exception as e:
        print(e)


def write_response(job_dict):
    print("Getting AI Proposal Now -------------- ")
    bard_response = ''
    subject_line = ''
    closing_word = ''
    closing_words = ["thanks,", "sincerely,", "best regards,"]
    response_lines = []
    global key_index
    try:
        API_KEYS = [
            "aggGc0rADR67gsgo1URb-sruZZrn-Pqi8uvn1zr19HDb9hnI7_AATT_xbQVu5k5hFnGKSg.",
            "aQjAjb1-R7nFlp9eMjb_gqzeVIySua1eHWiKfetlFJy7szHbrmWTlQroO-m8kxxu6iYTFg.",
            "aghlBFt8ebPpL80jdTr6_k-mOt-J9u7ybkI7lzqA23KyrDc3MKCEF3TBJlkhlGzW8ljhZjdw.",
            # "aghlBBvXbL_Z-4tO978RcNsLX9yD98y9ZWP6SRbQt-Sb33e6lXY5R4XtDAUxhFn9CkjA.",
            # "ZQgDduUgpJyco4jvBvzKM11firS5fwjWsV54xQNyYbXlilIMFo15akOYnGryXwWRxnYbaA.",
            # "ZwgGcyldhHBJf6GHh6GOc2ob_2vipNxaxf70l3YjDP-eOxfYO_F7hwfcw5XBni_qRKFGYA.",    # error
            # "ZgiPGLZC2OHOGd-ehwwDeRkkwvlt17FkpuYn0WluAF3Qu1EpFhatAfAcBUulcVnvEsjz8Q.",  # error
            # "YwjU50L0GNkYG5ylXwWeKIIGXvLrfuK6Wk4ewiZU8-aoSW8u3poWgKmBMHCrvy5Ab_kA8g.",  # error
            "ZgjnhpFJL0_mlhMTlQ5yl4KUje3WJLsMNT9hDhcahC27-RmPvU5jmcOxakx-yFHkfLCWdw.",
            # "ZQgCIRSLQ5RLe4r257amvGTgilDi47VK6s3VytwCdhRRZdaKYO-kU7fYZd8tfaNedl-h3w.",  # error
            # "YwiGFUYqFLhmxJMMeAaGLKlz2TzqBWHgCbSqx1-yXDWP6m-cI6w85MCC2KDTf3dMvkS9RQ.",  # error
            # "CjIBSAxbGfOLIQ6zZqhOAmiExXeeof1hqV3qVpEdO406f0hXHtZerKGtw8eV4qHDN43j0BAA.",    # error
            # "ZggDMrw-qa3ngHXElhXflwLjQlYYiCabg-1xl46x7MOAGjXmKOhbhnsOm1B0V163RlKh-Q."   #error
        ]
        rejection_list = [
            "not programmed",
            "i'm unable to",
            "text-based ai",
            "language model ai",
            "can't assist",
            "language model",
            'unable'
        ]
        try:
            os.environ['_BARD_API_KEY'] = API_KEYS[key_index]
            updated_index = (key_index + 1) % len(API_KEYS)
            key_index = updated_index
        except Exception as e:
            print('in bard exception', str(e))
            return 'An error occurred while attempting to generate the proposal'
        game_portfolio = "https://play.google.com/store/apps/developer?id=Tap2Play,+LLC"
        app_portfolio = "https://apps.apple.com/us/app/grocerapp-online-grocery/id1119311709?platform=iphone \n https://play.google.com/store/apps/details?id=com.barfee.mart"
        web_portfolio = "http://www.xiqinc.com/ (B2B Marketing Platform)"
        input_text = f"""
        Please write a proposal response for the following project with title: {job_dict['Job Title']},
        and description: {job_dict['Job Description']}. If the project is related to Game Development,
        please incorporate this link in the portfolio: {game_portfolio}. If it's related to Mobile App Development,
        please provide this link: {app_portfolio}. If it's about Web Development, please include this link: {web_portfolio}.
        Make sure the first two lines of the proposal are directly relevant to the project title and description.
        If the project requires an individual, introduce yourself accordingly. If it requires a company/agency,
        mention Rootpointers as the agency which has more than 75 resources. In the end, suggest scheduling a call
        to discuss more details about the project. Please keep the proposal concise and under 150 words.
        """
        try:
            bard_response = Bard().get_answer(input_text)['content']
        except Exception as e:
            print('in bard exception', str(e))
            return 'An error occurred while attempting to generate the proposal'

        if bard_response is None:
            return 'An error occurred while attempting to generate the proposal'

        for a in rejection_list:
            if a in str(bard_response.lower()):
                bard_response = write_response(job_dict)
                break

        if bard_response:
            lines = bard_response.split('\n')
            for line in range(len(lines) - 1, -1, -1):
                if "subject" in lines[line].lower():
                    subject_line = '{0} \n'.format(line)
                    del lines[line]
                if any(word in lines[line].lower() for word in closing_words):
                    closing_word = '\n {0}'.format(line)
                    del lines[line]
                if "i hope this proposal is concise" in lines[line].lower():
                    del lines[line]
            bard_response = ''.join(lines)
        special_characters = ['###', '***', '**', '*', '\*\*\*', '\*\*', '\*',  '>>', '>', '\n\n\n']
        str_index = 0
        for character in special_characters:
            bard_response = re.sub(re.escape(character), '', bard_response)
        
        if 'bard' in bard_response.lower():
            bard_response.replace("Bard", "[Your Identity]")

        # if 'thanks' in bard_response.lower():
        #     str_index = bard_response.lower().index('thanks')
        #     bard_response = bard_response[:str_index]
        #
        # elif 'sincerely' in bard_response.lower():
        #     str_index = bard_response.lower().index('sincerely')
        #     bard_response = bard_response[:str_index]
        #
        # elif 'best regards' in bard_response.lower():
        #     str_index = bard_response.lower().index('regards')
        #     bard_response = bard_response[:str_index]

        if 'Sure,' in bard_response:
            response = bard_response.split(':')
            bard_response = ' '.join(response[1:])
        if 'Hi' not in bard_response and 'Dear ' not in bard_response:
            bard_response = f'Hi [Client Name],\n{bard_response}'

        proposal_response = {
            'bard_response': bard_response,
            'subject_line': subject_line,
            'closing': closing_word
        }
        return proposal_response
    except Exception as e:
        return 'An error occurred while attempting to generate the proposal'


def broadcast_to_discord(job_dict, job_response=None):
    global discord
    print("Sending to Discord-------------- ")
    job_id = job_dict['id']
    job_title = job_dict['job_title']
    job_link = job_dict['job_link']

    message = f'Job Title: {job_title}\nApp Link: {job_id}\nJob Main Link: {job_link}'
    discord.post(content=message)
    print('after sending to discord')


discord_token = 'MTEzNzQ3NDgzMzg2OTk3OTcyOQ.GBfeTV.JlkqAuuMmYY1YXKL7lUnlu8Y7_GMvnL-wx4Hjo'
flag = ''
intents = ds.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')


@bot.event
async def on_message(message):
    print(f'Message content: {message.content}')
    global flag

    # Perform any additional checks or actions based on the message content
    if message.content.lower() == '!start':
        flag = 'start'
        await message.channel.send('Bidding started')
    elif message.content.lower() == '!stop':
        flag = 'stop'
        await message.channel.send("Bidding stopped.")


async def run_bot():
    await bot.start(discord_token)


def main():
    global discord
    print('in job parser main thread')
    discord = Discord(url=webhook_url)
    discord.post(content="Bidding Started")

    thread1 = Thread(target=fetch_jobs)
    thread2 = Thread(target=process_jobs)

    # Start threads
    thread1.start()
    thread2.start()

    # Start the bot asynchronously
    asyncio.run(run_bot())

    # Wait for both threads to finish
    thread1.join()
    thread2.join()


if __name__ == "__main__":
    main()
