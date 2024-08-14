import time

import selenium.common
from selenium import webdriver
from bs4 import BeautifulSoup
import random
import sys
import random


class AvitoParser:
    def __init__(self, url, send_msg, timeout, log, proxy=None, useragent=None):
        self.compare = None
        self.urls = []
        self.ct = 0
        self.stop_signal = False
        self.first_run = True
        self.chat_id = ''
        self.timeout = timeout
        self.url = url
        self.send_msg = send_msg
        self.log = log
        self.options = webdriver.ChromeOptions()
        self.options.add_argument("--log-level=3")
        if proxy:
            self.options.add_argument(f'--proxy-server={proxy}')
        if useragent:
            self.options.add_argument(f'user-agent={self.get_ua()}')
        self.driver = webdriver.Chrome(options=self.options)
        self.driver.set_page_load_timeout(3)

    def get_html(self):
        self.driver.refresh()
        time.sleep(self.timeout + random.uniform(0, 2))
        return self.driver.page_source

    def stop_selenium(self):
        self.stop_signal = True

    @staticmethod
    def get_ua():
        with open(file='useragents.txt', mode='r', encoding='utf-8') as file:
            data = file.read().split('\n')
            return random.choice(data)

    def run_pars(self):
        try:
            self.driver.get(self.url)
        except selenium.common.exceptions.TimeoutException:
            pass
        except selenium.common.exceptions.InvalidArgumentException:
            self.log('warning', 'Введён неправильный URL адрес')
            return
        except Exception:
            self.log('error', 'Неизвестная ошибка, надо перезапустить парсинг')
            return
        while True:
            try:
                s = BeautifulSoup(self.get_html(), 'lxml')
                # self.driver.delete_all_cookies()
                divs = s.find_all('div', {
                    'class': 'iva-item-root-_lk9K photo-slider-slider-S15A_ iva-item-list-rfgcH iva-item-redesign-rop6P'
                             ' iva-item-responsive-_lbhG items-item-My3ih items-listItem-Gd1jN js-catalog-item-enum'})

                if len(divs) < 2:
                    self.log('warning', 'В ответе сайта не найдены объявления, возможно временная блокировка IP')
                    time.sleep(random.uniform(3, 6))

                for c, i in enumerate(divs):
                    base = i.find('div', {'class': 'iva-item-titleStep-pdebR'}).find('a')

                    href = base['href']
                    title = base['title']

                    if href in self.urls:
                        pass
                    else:
                        self.urls.append(href)
                        if not self.first_run:
                            msg = 'Обнаружено новое объявление.\n'
                            self.log('good',
                                     f'Обнаружено новое объявление: {title}')
                            self.send_msg(title + '\n' + 'https://www.avito.ru' + href + '\n')

            except selenium.common.exceptions.TimeoutException:
                pass
            except Exception:
                self.log('error', 'Неизвестная ошибка, надо перезапустить парсинг')
                return
            if self.stop_signal:
                self.driver.close()
                self.driver.quit()
                sys.exit()
                return
            self.ct += 1
            if len(self.urls) > 500:
                self.urls = self.urls[100:]
            self.log('notify', f'{self.ct} запрос обработан.')
            self.first_run = False


class DromParser(AvitoParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def run_pars(self):
        try:
            self.driver.get(self.url)
        except selenium.common.exceptions.TimeoutException:
            pass
        except selenium.common.exceptions.InvalidArgumentException:
            self.log('warning', 'Введён неправильный URL адрес')
            return
        except Exception:
            self.log('error', 'Неизвестная ошибка, надо перезапустить парсинг')
            return
        while True:
            try:
                s = BeautifulSoup(self.get_html(), 'lxml')
                # self.driver.delete_all_cookies()
                divs = s.find_all('a', {
                    'class': 'css-xb5nz8 e1huvdhj1'})

                if len(divs) < 2:
                    self.log('warning', 'В ответе сайта не найдены объявления, возможно временная блокировка IP')
                    time.sleep(random.uniform(3, 6))

                for c, i in enumerate(divs):
                    base = i
                    href = base['href']
                    print(href)
                    # title = base['title']

                    if href in self.urls:
                        pass
                    else:
                        self.urls.append(href)
                        if not self.first_run:
                            msg = 'Обнаружено новое объявление.\n'
                            self.log('good',
                                     f'Обнаружено новое объявление: {href}')
                            self.send_msg(href + '\n')

            except selenium.common.exceptions.TimeoutException:
                pass
            except Exception:
                self.log('error', 'Неизвестная ошибка, надо перезапустить парсинг')
                return
            if self.stop_signal:
                self.driver.close()
                return
            self.ct += 1
            if len(self.urls) > 500:
                self.urls = self.urls[100:]
            self.log('notify', f'{self.ct} запрос обработан.')
            self.first_run = False
