import aiohttp
from bs4 import BeautifulSoup
import asyncio
import config


class AutoRiaParser:
    def __init__(self):
        self.cars_data = []
        self.__car_html_sections = []
        self.__url = config.url
        self.__cars_sections_in_page = config.cars_sections_in_page

    @staticmethod
    async def __get_html(session, page_number, size):
        base_link = config.url
        base_link += f'&page={page_number}&size={size}'
        referer_link = base_link.replace('/search/', '/advanced-search/')

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'uk-UA,uk;q=0.8,ru;q=0.6,en-US;q=0.4,en;q=0.2',
            'Referer': referer_link,
            'Sec-GPC': '1',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Connection': 'keep-alive',
            'Priority': 'u=0, i',
        }

        async with session.get(base_link, headers=headers) as response:
            return await response.text()

    @staticmethod
    async def __get_media_data(session, car_url):
        car_id = car_url.split('_')[-1].replace('.html', '')
        url = f'https://auto.ria.com/demo/bu/finalPage/photos/{car_id}'

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0',
            'Accept': '*/*',
            'Accept-Language': 'uk-UA,uk;q=0.8,ru;q=0.6,en-US;q=0.4,en;q=0.2',
            'Referer': car_url,
            'DNT': '1',
            'Sec-GPC': '1',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Priority': 'u=4',
        }

        async with session.get(url, headers=headers) as response:
            return await response.json()

    async def __parse_media_data(self, session, car_url):
        media_data = await self.__get_media_data(session, car_url)

        photo_links = []
        video_link = None

        if media_data.get('video', None):
            video_link = "https://www.youtube.com/watch?v=" + media_data.get('video', None)
        for photo in media_data['photo']:
            photo_links.append(photo['huge'])

        return video_link, photo_links

    async def cars_html_collect(self):
        self.cars_data.clear()
        page_number = 0

        async with aiohttp.ClientSession() as session:
            while True:
                html = await self.__get_html(session, page_number, self.__cars_sections_in_page)
                soup = BeautifulSoup(html, "html.parser")
                sections = soup.find_all('section', class_='ticket-item')
                if sections:
                    self.__car_html_sections.extend(sections)
                    page_number += 1
                else:
                    print('Cars html-data collected')
                    break

    async def get_cars_info(self):
        if not self.__car_html_sections:
            raise ValueError('There is no html sections!')

        for section in self.__car_html_sections:
            res = section.find('a', class_='address')
            name, model, year = res.text.split()
            car_link = res.get('href')
            prices = section.find('div', class_='price-ticket')
            price_in_dollars = prices.get('data-main-price')
            information_about_car = section.find('div', class_="definition-data")
            date_info = section.find('div', class_="footer_ticket").text.strip()
            mileage = information_about_car.find('li', class_="item-char js-race").text.strip()
            city = information_about_car.find('li', class_="item-char view-location js-location").text.strip()
            city = city.replace(' ( від )', '')

            current_car = {
                "model": f"{name} {model}",
                "year": year,
                "url": car_link,
                "price": price_in_dollars,
                "mileage": mileage,
                "city": city,
                "date_info": date_info,
                "video_link": None,
                "photos": None}
            self.cars_data.append(current_car)

    async def get_photos_and_videos(self):
        if not self.cars_data:
            raise ValueError('There is no cars data!')

        car_urls = [i['url'] for i in self.cars_data]

        async with aiohttp.ClientSession() as session:
            tasks = [self.__parse_media_data(session, url) for url in car_urls]
            results = await asyncio.gather(*tasks)

        for index, (video_link, photos) in enumerate(results):
            self.cars_data[index].update({"video_link": video_link, "photos": photos})

    async def get_photos_videos_by_link(self, url):
        async with aiohttp.ClientSession() as session:
            video_link, photos = await self.__parse_media_data(session, url)
            return video_link, photos

    async def parse_all(self):
        await self.cars_html_collect()
        await self.get_cars_info()
        await self.get_photos_and_videos()
