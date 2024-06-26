import os
import time
import random
import asyncio
from pathlib import Path
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, executor, types

from apscheduler.schedulers.background import BackgroundScheduler

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException

from tech_zone.modules.parsing_tmm import get_trade_data
from tech_zone.modules.work_with_data import work_volume_calculation


load_dotenv('./tech_zone/env/.env')
bot = Bot(token=os.environ.get('TOKEN_TRADING_ASSIST_BOT'))
dp = Dispatcher(bot)


static_volume = 0
dynamic_volume = 2100


@dp.message_handler()
async def start_bot(message: types.Message):
    if message.text == '/start':
        await message.answer(text='Программа запущена')
        loop = asyncio.get_event_loop()
        loop.create_task(check_work_volume())
        scheduler_main_process()
        scheduler.start()

    elif message.text == '/resume':
        await message.answer(text='Программа возобновила работу')
        scheduler.resume()
        return
    elif message.text == '/stop':
        await message.answer(text='Программа приостановлена')
        scheduler.pause()
    else:
        return


def scheduler_main_process():
    global dynamic_volume

    chrome_service = Service(r'./tech_zone/driver_chrome_selenium/chromedriver.exe')
    chrome_options = webdriver.ChromeOptions()
    # chrome_options.add_argument('--proxy-server=190.61.88.147:8080')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--remote-debugging-port=9222')
    chrome_options.add_argument('--headless')
    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

    url = 'https://tradermake.money/app2/account/my-trades'

    email = os.environ.get('email_tmm')
    password = os.environ.get('password_tmm')

    try:
        driver.get(url=url)
        time.sleep(2)
        email_input = driver.find_element(By.ID, 'input-19')
        email_input.clear()
        email_input.send_keys(email)

        time.sleep(random.randrange(1, 2))
        password_input = driver.find_element(By.ID, 'input-23')
        password_input.clear()
        password_input.send_keys(password)

        time.sleep(random.randrange(1, 2))
        password_input.send_keys(Keys.ENTER)
        # try:
        #     wait = WebDriverWait(driver, 20)
        #     clickable_element = '/html/body/div[1]/div/div[1]/div/div[3]/div[3]/div/button/span/i'
        #     wait.until(ec.presence_of_element_located((By.XPATH, clickable_element)))
        #     wait.until(ec.element_to_be_clickable((By.XPATH, clickable_element)))
        #     driver.find_element(By.XPATH, clickable_element).click()
        # except (TimeoutException, ElementClickInterceptedException):
        #     time.sleep(2)
        #     driver.find_element(By.XPATH, '/html/body/div[1]/div/div[1]/div/div[3]/div[3]/div/button/span/i').click()

        driver.get(url=url)

        time.sleep(10)
        with open(Path(Path(__file__).parent, f'tech_zone/html/index.html'), 'w', encoding='utf8') as file:
            file.write(driver.page_source)

        trade_data = get_trade_data()

        if trade_data == 'no data':
            return
        else:
            if trade_data is None:
                dynamic_volume = 'нет данных'
                return
            elif trade_data == 'nothing trades':
                return
            else:
                trade_percent = trade_data[0]
                trade_volume = trade_data[1]
                trade_commission = trade_data[2]
                current_trade_id = trade_data[3]

                current_work_volume = work_volume_calculation(trade_percent, trade_volume, trade_commission, current_trade_id)
                dynamic_volume = current_work_volume
                return

    except Exception as ex:
        print(ex)
    finally:
        time.sleep(5)
        driver.close()
        driver.quit()


async def check_work_volume():
    global static_volume
    global dynamic_volume
    while True:
        if dynamic_volume == 'нет данных':
            await bot.send_message(402134252, 'Не удалось собрать данные с сайта.')
            await asyncio.sleep(10)

        elif dynamic_volume == 'баланс пуст':
            await bot.send_message(402134252, 'Сумма Вашего баланса равна нулю. Задайте иное значение.')

        elif dynamic_volume == 'просадка превышена':
            await bot.send_message(402134252, 'Недопустимый убыток! На сегодня торговля окончена.')

        elif static_volume != dynamic_volume:
            await bot.send_message(402134252, f'Рабочий объем: {dynamic_volume}$')
            static_volume = dynamic_volume

        await asyncio.sleep(10)

if __name__ == '__main__':

    scheduler = BackgroundScheduler()
    scheduler.add_job(scheduler_main_process, 'interval', seconds=20)
    executor.start_polling(dp, skip_updates=True)


