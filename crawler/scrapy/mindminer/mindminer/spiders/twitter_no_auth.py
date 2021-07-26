import re
import json
import logging
from urllib.parse import quote

from scrapy import http
from scrapy.spiders import CrawlSpider
from scrapy.core.downloader.middleware import DownloaderMiddlewareManager
from scrapy_selenium import SeleniumRequest, SeleniumMiddleware

from mindminer.items import Tweet, User


class TwitterNoAuth(CrawlSpider):
    """ Twitter spider to get Tweets without API authentication. """
    name = 'TwitterNoAuth'
    allowed_domains = ['twitter.com']
    url = 'https://twitter.com/explore'
    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy_selenium.SeleniumMiddleware': 800
        }
    }
    cookies = None
    x_guest_token = None
    headers = None

    def __init__(self, query='', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = (
            f'https://api.twitter.com/2/search/adaptive.json?'
            f'include_profile_interstitial_type=1'
            f'&include_blocking=1'
            f'&include_blocked_by=1'
            f'&include_followed_by=1'
            f'&include_want_retweets=1'
            f'&include_mute_edge=1'
            f'&include_can_dm=1'
            f'&include_can_media_tag=1'
            f'&skip_status=1'
            f'&cards_platform=Web-12'
            f'&include_cards=1'
            f'&include_ext_alt_text=true'
            f'&include_quote_count=true'
            f'&include_reply_count=1'
            f'&tweet_mode=extended'
            f'&include_entities=true'
            f'&include_user_entities=true'
            f'&include_ext_media_color=true'
            f'&include_ext_media_availability=true'
            f'&send_error_codes=true'
            f'&simple_quoted_tweet=true'
            f'&query_source=typed_query'
            f'&pc=1'
            f'&spelling_corrections=1'
            f'&ext=mediaStats%2ChighlightedLabel'
            f'&count=20'
            f'&tweet_search_mode=live'
        )
        self.url = self.url + '&q={query}'
        self.query = query
        self.num_search_issued = 0
        self.cursor_re = re.compile('"(scroll:[^"]*)"')

    def start_requests(self):
        """ Start requests to initial page. """
        yield SeleniumRequest(url=self.url, callback=self.parse_home_page)

    def parse_home_page(self, response):
        """ Get cookies. """
        self.update_cookies(response)
        for request in self.start_query_request():
            yield request

    def update_cookies(self, response):
        """ Set cookies and request headers. """
        driver = response.meta['driver']
        try:
            self.cookies = driver.get_cookies()
            self.x_guest_token = driver.get_cookie('gt')['value']
        except Exception as error:
            self.log(f'Cookies are not updated! Traceback: {error}')
        self.headers = {
            'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Z'
                             'v7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
            'x-guest-token': self.x_guest_token,
        }

    def start_query_request(self, cursor=None):
        """ Search request. """
        if cursor:
            url = self.url + '&cursor={cursor}'
            url = url.format(query=quote(self.query), cursor=quote(cursor))
        else:
            url = self.url.format(query=quote(self.query))
        request = http.Request(url, callback=self.parse_result_page, cookies=self.cookies, headers=self.headers)
        yield request

        self.num_search_issued += 1
        if self.num_search_issued % 100 == 0:
            for middleware in self.crawler.engine.downloader.middleware.middlewares:
                if isinstance(middleware, SeleniumMiddleware):
                    middleware.spider_closed()
            self.crawler.engine.downloader.middleware = DownloaderMiddlewareManager.from_crawler(self.crawler)
            yield SeleniumRequest(url=self.url, callback=self.update_cookies, dont_filter=True)

    def parse_result_page(self, response):
        """ Get tweets and users. """
        data = json.loads(response.text)
        for item in self.parse_tweet_item(data['globalObjects']['tweets']):
            yield item
        for item in self.parse_user_item(data['globalObjects']['users']):
            yield item
        cursor = self.cursor_re.search(response.text).group(1)
        for request in self.start_query_request(cursor=cursor):
            yield request

    @staticmethod
    def parse_tweet_item(items):
        for key, value in items.items():
            tweet = Tweet()
            tweet['id'] = key
            tweet['data'] = value
            yield tweet

    @staticmethod
    def parse_user_item(items):
        for key, value in items.items():
            user = User()
            user['id'] = key
            user['data'] = value
            yield
