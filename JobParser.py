import asyncio
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from bardapi import Bard
from discordwebhook import Discord
from collections import deque
from queue import Queue
from threading import Thread
import time
import os
import ssl
from bs4 import BeautifulSoup
import feedparser
import re
import discord as ds
from discord.ext import commands
# from models import Jobs, Proposals, db
from models import Jobs, db
import time


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
TEST = True

if TEST:
    webhook_url = webhook_url_test

discord = None

job_links = Queue()
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

        time.sleep(10)  # Or however often you want to fetch jobs


def process_jobs():
    global job_links
    global flag
    # print('Process Job')

    while True:
        try:
            # print('in process job job link queue size', job_links.qsize())
            if flag == 'start':
                print('job links', job_links.empty())
                if not job_links.empty():
                    print('in job link not empty')
                    job_dict = job_links.get()
                    print(f"""***********parsing following link : {job_dict['Job Link']}\n""")
                    write_response(job_dict)
                    time.sleep(10)
                    # parse_job(link)
                    # Existing job_info_scrape implementation goes here
            # print('in process job flag is empty')
        except Exception as e:
            print(e)


def rss_parsing(rss, us_only=""):
    global seen_links
    global job_links

    try:
        print("Parsing RSS for New Links------------ ")

        for entry in rss.entries:
            print('entry', entry)
            title = entry.title
            link = entry.link

            soup = BeautifulSoup(entry.description, 'html.parser')
            description = soup.get_text(separator=' ')

            # print("Job Title:", title)
            #
            # print("Job Link:", link)
            #
            # print("Job Description:", description)

            data = {
                "Job Link": link,
                "Job Title": title,
                "Job Description": description,
            }

            if not any(
                    exclude_word.lower() in title.lower()
                    for exclude_word in exclude_keywords
            ):

                if link not in seen_links:
                    job_links.put(data)
                    seen_links.append(link)
                    from app import app
                    with app.app_context():
                        total_jobs = Jobs.query.count()
                        print('total jobs', total_jobs)
                        if total_jobs == 100:
                            oldest_jobs = Jobs.query.all()
                            for job in oldest_jobs:
                                db.session.delete(job)
                            db.session.commit()
                        print('before new job')
                        new_job = Jobs(job_title=data['Job Title'], job_link=data['Job Link'], job_description=data['Job Description'])
                        print('new job', new_job)
                        db.session.add(new_job)
                        db.session.commit()
                        print('after committing job')

                    # print('new job added', job_links.get())

            else:
                print("Link contains excluded keywords")

        # print('job_links', job_links)

    except Exception as e:
        print(e)


# Selenium
def parse_job(link):
    print("Parsing Job through Selenium -------------- ")

    firefox_services = Service(executable_path='geckodriver', port=3000,
                               service_args=['--marionette-port', '2828', '--connect-existing'])
    driver = webdriver.Firefox(service=firefox_services)

    credentials = {
        'username': 'shakeelrootpointers@gmail.com',
        'password': 'itu@123456',
        'answer': 'lahore',
    }

    driver.get(link)
    time.sleep(15)
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # login_needed = soup.find('a', href="/ab/account-security/login")
    # Check if the login button exists
    # if login_needed:
    #     # Login
    #     login(driver, credentials['username'], credentials['password'], credentials['answer'])

    try:
        try:
            header_element = driver.find_element(By.CSS_SELECTOR, 'header.up-card-header.d-flex h1')
            job_title = header_element.text
        except Exception as e:
            print(e)
            job_title = ""

        try:
            job_description_element = driver.find_element(By.CSS_SELECTOR,
                                                          'section.up-card-section div.job-description.break.mb-0')
            job_description = job_description_element.text
        except Exception as e:
            print(e)
            job_description = ""

        li_elements = soup.find_all('li', class_='d-flex d-md-block justify-space-between')

        try:
            proposals_element = [element for element in li_elements if 'Proposals:' in element.text][0]
            proposals_text = proposals_element.text.split(':')[1].strip()
            # Use regular expressions to find all sequences of digits in the string
            proposals_arr = re.findall(r'\d+', proposals_text)
            # Convert the numbers to integers
            proposals = list(map(int, proposals_arr))
        except Exception as e:
            print(f'An error occurred in proposals : {e}')
            proposals = 0

        try:
            interviewing_element = [element for element in li_elements if 'Interviewing:' in element.text][0]
            interviewing = int(interviewing_element.text.split(':')[1].strip())
        except Exception as e:
            print(f'An error occurred in interviewing : {e}')
            interviewing = 0

        try:
            invites_element = [element for element in li_elements if 'Invites sent:' in element.text][0]
            invites_sent = int(invites_element.text.split(':')[1].strip())
        except Exception as e:
            print(f'An error occurred in invites : {e}')
            invites_sent = 0

        try:
            budget_element = driver.find_element(By.CSS_SELECTOR,
                                                 'div.header.d-flex div[data-v-2bd71b67] div[data-v-913b0b82] p strong')
            job_price = [float(budget_element.text.replace("$", "").replace(",", ""))]
        except Exception as e:
            print(f'An error occurred in job_price : {e}')
            print('trying hourly rate job')
            # If that fails, try the alternative code
            try:
                rate_elements = driver.find_elements(By.CSS_SELECTOR, 'div.header.d-flex div[data-v-913b0b82] p strong')
                lower_rate = rate_elements[0].text.strip()
                upper_rate = rate_elements[1].text.strip()
                job_price = [float(lower_rate.replace("$", "").replace(",", "")),
                             float(upper_rate.replace("$", "").replace(",", ""))]
                print(job_price)
            except Exception as e:
                print(f'An error occurred in job_price : {e}')
                job_price = []

        try:
            skills = soup.find_all('a', class_='up-n-link cfe-ui-job-skill up-skill-badge m-0-left m-0-top m-xs-bottom')
            skills_text = [skill.get_text() for skill in skills]
        except Exception as e:
            print(f'An error occurred in skills : {e}')
            skills_text = []

        try:
            location_element = driver.find_elements(By.CSS_SELECTOR, 'li[data-qa="client-location"]')[1]
            country = location_element.find_element(By.CSS_SELECTOR, 'strong').text
            city = location_element.find_element(By.CSS_SELECTOR, 'div.text-muted span.nowrap').text
        except Exception as e:
            print(f'An error occurred in location : {e}')
            country = city = ""

        try:
            review_element = driver.find_elements(By.CSS_SELECTOR, 'div.text-muted.rating.mb-20 span.nowrap')[1]
            avg_review = float(review_element.text.split(" ")[0])
            number_of_reviews = int(review_element.text.split(" ")[2])
        except Exception as e:
            print(f'An error occurred in reviews : {e}')
            avg_review = 0.0
            number_of_reviews = 0

        try:
            job_posted_element = soup.find('li', attrs={'data-qa': 'client-job-posting-stats'})
            jobs_posted = int(job_posted_element.text.strip().split()[0])
        except Exception as e:
            print(f'An error occurred in jobs posted : {e}')
            jobs_posted = 0

        try:
            total_spent_element = soup.find('strong', attrs={'data-qa': 'client-spend'})
            total_spent = float(total_spent_element.text.strip().split()[0].replace("$", "").replace(",", ""))
        except Exception as e:
            print(f'An error occurred in total spent : {e}')
            total_spent = 0.0

        try:
            hires_element = soup.find('div', attrs={'data-qa': 'client-hires'})
            num_hires = int(hires_element.text.strip().split()[0])
        except Exception as e:
            print(f'An error occurred in hires : {e}')
            num_hires = 0

        try:
            location_restriction_element = soup.find('span', attrs={'class': 'vertical-align-middle'})
            location_restriction = location_restriction_element.text.strip()
        except Exception as e:
            print(f'An error occurred in location restriction : {e}')
            location_restriction = ""

        data = {
            "Job Link": link,
            "Job Title": job_title,
            "Job Description": job_description,
            "Proposals": proposals,
            "Interviewing": interviewing,
            "Job Price": job_price,
            "Skills": skills_text,
            "Invites Sent": invites_sent,
            "Country": country,
            "City": city,
            "Average Review": avg_review,
            "Number of Reviews": number_of_reviews,
            "Jobs Posted": jobs_posted,
            "Total Spent": total_spent,
            "Number of Hires": num_hires,
            "Location Restriction": location_restriction,
        }
        # print(data)
        shortlist_job(data)

    except Exception as e:
        print(e)


def shortlist_job(job_dict):
    print('in shortlist job')
    print("Shortlisting Jobs-------------- ")
    features = {}
    try:
        features['proposals'] = job_dict['Proposals'][0] < 10
    except Exception as e:
        print("Error with Proposals:", str(e))

    try:
        features['interviewing'] = job_dict['Interviewing'] < 3
    except Exception as e:
        print("Error with Interviewing:", str(e))

    try:
        features['invites'] = job_dict['Invites Sent'] < 10
    except Exception as e:
        print("Error with invites_sent:", str(e))

    try:
        features['country'] = job_dict['Country'] == '' or job_dict['Country'] in ['United States', 'United Kingdom',
                                                                                   'Australia', 'Canada', 'Germany',
                                                                                   'France', 'Netherlands', 'Spain',
                                                                                   'Italy', 'Switzerland',
                                                                                   'United Arab Emirates', 'Singapore',
                                                                                   'Israel', 'Belgium', 'Sweden',
                                                                                   'Ireland', 'Denmark', 'Austria',
                                                                                   'Japan']
    except Exception as e:
        print("Error with country:", str(e))

    try:
        features['avg review'] = job_dict['Average Review'] > 4 or job_dict['Average Review'] == 0
    except Exception as e:
        print("Error with avg_review:", str(e))

    try:
        features['location'] = job_dict['Location Restriction'] in ['Worldwide']
    except Exception as e:
        print("Error with location_restriction:", str(e))

    try:
        if len(job_dict['Job Price']) == 1:
            features['job_price'] = job_dict['Job Price'][0] >= 1000
        else:
            features['job_price'] = job_dict['Job Price'][1] > 20
    except Exception as e:
        print("Error with job_price:", str(e))

    # features.append(job_dict['skills'] in [])

    if any(value is False for value in features.values()):
        print("Job not shortlisted")
        job_dict["Shortlisted"] = "Not Shortlisted : {}".format(str(features))
        print('job dict in value', job_dict)
        broadcast_to_discord(job_dict)
    else:
        job_dict["Shortlisted"] = "Shortlisted : {}".format(str(features))
        print('job dict in else', job_dict)
        write_response(job_dict)


def write_response(job_dict):
    print('in write response of job parser')
    print("Getting AI Proposal Now -------------- ")

    global key_index
    try:
        API_KEY = "ZQgDduUgpJyco4jvBvzKM11firS5fwjWsV54xQNyYbXlilIMFo15akOYnGryXwWRxnYbaA."
        API_KEYS = [
            "ZQgDduUgpJyco4jvBvzKM11firS5fwjWsV54xQNyYbXlilIMFo15akOYnGryXwWRxnYbaA.",
            "ZwgGcyldhHBJf6GHh6GOc2ob_2vipNxaxf70l3YjDP-eOxfYO_F7hwfcw5XBni_qRKFGYA.",
            "ZgiPGLZC2OHOGd-ehwwDeRkkwvlt17FkpuYn0WluAF3Qu1EpFhatAfAcBUulcVnvEsjz8Q.",
            "YwjU50L0GNkYG5ylXwWeKIIGXvLrfuK6Wk4ewiZU8-aoSW8u3poWgKmBMHCrvy5Ab_kA8g.",
            "ZgjnhpFJL0_mlhMTlQ5yl4KUje3WJLsMNT9hDhcahC27-RmPvU5jmcOxakx-yFHkfLCWdw.",
            "ZQgCIRSLQ5RLe4r257amvGTgilDi47VK6s3VytwCdhRRZdaKYO-kU7fYZd8tfaNedl-h3w.",
            "YwiGFUYqFLhmxJMMeAaGLKlz2TzqBWHgCbSqx1-yXDWP6m-cI6w85MCC2KDTf3dMvkS9RQ.",
            "CjIBSAxbGfOLIQ6zZqhOAmiExXeeof1hqV3qVpEdO406f0hXHtZerKGtw8eV4qHDN43j0BAA.",
            "ZggDMrw-qa3ngHXElhXflwLjQlYYiCabg-1xl46x7MOAGjXmKOhbhnsOm1B0V163RlKh-Q."
        ]
        print('bard api key', API_KEYS[key_index])
        os.environ['_BARD_API_KEY'] = API_KEYS[key_index]

        updated_index = (key_index + 1) % len(API_KEYS)
        key_index = updated_index
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

        bard_response = Bard().get_answer(input_text)['content']
        print('bard response before checker', bard_response)
        if bard_response is None:
            print(' in bard response none checker')
            return "Error with generate proposal:"
        bard_response = ''.join(bard_response)
        special_characters = ['###', '\*', '\*\*', '**']

        for character in special_characters:
            bard_response = re.sub(re.escape(character), '', bard_response)

        # broadcast_to_discord(job_dict, bard_response)
        return bard_response
    except Exception as e:
        print("Error with generate proposal:", str(e))
        # broadcast_to_discord(job_dict, 'Error with generating proposal : {}'.format(e))


def broadcast_to_discord(job_dict, job_response=None):
    global discord
    print('discord', discord)
    print("Sending to Discord-------------- ")
    print(job_dict)
    job_description = job_dict.pop('Job Description')
    print('job description', job_description)
    # create a list of formatted strings from the job_dict
    if job_response:
        # join the list into a single string with line breaks
        job_dict['proposal response'] = job_response
    job_title = job_dict['Job Title']
    job_link = job_dict['Job Link']
    proposal_response = job_dict['proposal response']



    formatted_dict = [f'**{k}**: {v}' for k, v in job_dict.items()]

    # Add line on end
    message = '\n---------------------------------\n'
    message += '\n'.join(formatted_dict)
    message += '\n---------------------------------\n'
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
    print('after starting thread1 ')
    thread2.start()
    print('after starting thread2')

    # Start the bot asynchronously
    asyncio.run(run_bot())

    # Wait for both threads to finish
    thread1.join()
    print('after thread1 join')
    thread2.join()
    print('after thread2 join')


if __name__ == "__main__":
    main()
