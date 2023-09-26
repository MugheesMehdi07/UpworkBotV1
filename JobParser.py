import asyncio
import threading
import openai
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from discordwebhook import Discord
from collections import deque
from queue import Queue
from threading import Thread
from datetime import datetime, date
import ssl
from bs4 import BeautifulSoup
import feedparser
import discord as ds
from discord.ext import commands
from app import Jobs, db, JobStatus
import time
# from signals import notification





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
flag = None


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
                continue
                
            elif 'status' not in rss or rss.status != 200:
                print(f"Failed to retrieve feed: HTTP status code {rss.status}")
                continue
                

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


def rss_parsing(rss, rs_only =''):
    global seen_links
    global job_links
    global discord_jobs
    global flag
    prod_url = 'http://upworkbot.rootpointers.net/jobs/'
    dev_url = 'http://localhost:3000/jobs/'

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
                            # notification(new_job)
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
                        except Exception as e:
                                print('An error occurred in creating job object', str(e))
                        qs = Jobs.query.with_entities(Jobs.id, Jobs.job_title, Jobs.job_link).order_by(
                            Jobs.created_at.desc()).first()

                        if qs:
                            job_dict = {
                                'id': prod_url + str(qs[0]),
                                'job_title': qs[1],
                                'job_link': qs[2]
                            }
                            global flag
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
    subject = ''
    response = ''
    closing_index = 0
    closing = ''
    closing_words = ["thanks", "sincerely", "best regards", "warm regards"]
    proposal_by = ''
    global key_index
    try:
        API_KEY = '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'

        print('in api proposal by ', job_dict['proposal_by'])
        game_portfolio = "https://play.google.com/store/apps/developer?id=Tap2Play,+LLC"
        app_portfolio = "https://apps.apple.com/us/app/grocerapp-online-grocery/id1119311709?platform=iphone \n https://play.google.com/store/apps/details?id=com.barfee.mart"
        web_portfolio = "http://www.xiqinc.com/ (B2B Marketing Platform)"
        portfolio_mughees = f"""
        https://www.smartmitt.com/ (AI based Training Platform for Baseball Batters and Pitchers)
        https://xiqinc.com/ (Silicon Valley Based B2B Sales and Marketing Platform using AI to generate and analyze Leads)
        https://www.sparrowcharts.com/ (Social Media Analytics Platform that comabines all in on platform to handle and track your social media activity)
        """
        portfolio_company = f"""
        Web Application Development:
        Mobile App:
        Mobile Games:
        """
        if job_dict['proposal_by'] == 'mughees':
            proposal_by = f' Write on behalf of me named mughees, i have more than 7 years of experience in Web  Development (Django, Flask) with frontend (React, Vue.js) and also has Master in Data Science with expertise in AI Models building. Include the following application {portfolio_mughees} under portfolio that seem best suited. Make sure the first two lines of the proposalare directly relevant to the project title and description. Make bid  solution oriented describe  first how I will be doing this job then explain my relevant experience.'
        elif job_dict['proposal_by'] == 'company':
            proposal_by = f' Write on behalf of an organization RootPointers. Include the following application {portfolio_company} under portfolio that seem best suited. Make sure the first two lines of the proposal are directly relevant to the project title and description. Make bid  solution oriented describe  first how this organization will be doing this job then explain their relevant experience.'
        else:
            proposal_by = ''

        input_text = f"""
        Please write an Upwork proposal response for the following project with title: {job_dict['Job Title']}, and
        description {job_dict['Job Description']}. {proposal_by if proposal_by else ''}
         Keep proposal response concise and under 150 words.
        """

        print('input text', input_text)
        openai.api_key = API_KEY
        model = "gpt-3.5-turbo"
        print('before response')
        completion_tokens = openai.ChatCompletion.create(model=model, messages=[{'role': 'system', 'content': 'You are a helpful assistant that generates proposals.'}, {'role': 'user', 'content': input_text}])
        completion_tokens = completion_tokens['choices'][0]['message']['content']
        if not completion_tokens:
            return f'An error occurred while attempting to generate the proposal.'
        if 'dear' in completion_tokens.lower():
            sub_index = completion_tokens.lower().index('dear')
            subject = completion_tokens[:sub_index]
            completion_tokens = completion_tokens[sub_index:]
        for word in closing_words:
            if word in completion_tokens.lower():
                closing_index = completion_tokens.lower().index(word)
                closing = completion_tokens[closing_index - 5:]
                completion_tokens = completion_tokens[:closing_index - 5]

        response_dict = {
            'subject': subject if 'subject' in subject.lower() else '',
            'main': completion_tokens,
            'closing': closing if any(keyword in closing.lower() for keyword in ['regards', 'sincerely']) else ''
        }

        return response_dict

    except Exception as e:
        return f'An error occurred while attempting to generate the proposal {str(e)}'


def broadcast_to_discord(job_dict, job_response=None):
    global discord
    print("Sending to Discord-------------- ")
    job_id = job_dict['id']
    job_title = job_dict['job_title']
    job_link = job_dict['job_link']
    message = f'Job Title: {job_title}\nApp Link: {job_id}\nJob Main Link: {job_link}'
    discord.post(content=message)


discord_token = 'MTEzNzQ3NDgzMzg2OTk3OTcyOQ.GBfeTV.JlkqAuuMmYY1YXKL7lUnlu8Y7_GMvnL-wx4Hjo'
flag = None
intents = ds.Intents.all()
bot = commands.Bot(command_prefix='Bidding ', intents=intents)


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')


def flag_set(flag):
    global discord
    discord = Discord(url=webhook_url)
    if flag == 'true':
        discord.post(content="Bidding Started")
    elif flag == 'false':
        discord.post(content="Bidding Stopped")

@bot.event
async def on_message(message):
    print(f'Message content: {message.content}')
    global flag

    if message.content.lower() == 'bidding started':
        flag = 'start'
    elif message.content.lower() == 'bidding stopped':
        flag = 'stop'


async def run_bot():
    print('in run bot')
    await bot.start(discord_token)


def main():
    global discord
    discord = Discord(url=webhook_url)
    # discord.post(content="Bidding Started")

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

