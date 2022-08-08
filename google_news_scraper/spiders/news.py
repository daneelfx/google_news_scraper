from datetime import date, timedelta
import html2text
import csv

import scrapy
from scrapy_splash import SplashRequest

html_handler = html2text.HTML2Text()
html_handler.ignore_links = \
html_handler.ignore_images = \
html_handler.ignore_tables = True

file = open("google_news_scraper/utils/user_agent_list.csv")
AGENTS = csv.reader(file)
header = next(AGENTS)
AGENTS = list(map(lambda agent: agent[0], AGENTS))
file.close()

class NewsSpider(scrapy.Spider):
    name = 'news'
    # allowed_domains = ['www.google.com']
    BASE_URL = 'https://www.google.com'
    # start_urls = ['http://www.google.com/']

    script = '''
        function main(splash, args)
            splash.private_mode_enabled = false
            splash.images_enabled = false

            -- splash:set_user_agent(args.user_agent)    

            headers = {
                ['Accept-Language'] = args.language
            }

            splash:set_custom_headers(headers)

            url = args.url
            assert(splash:go(url))
            splash:wait(4)
            -- overall_time = 4s

            -- selects main google.com search input, inserts text on it and press enter

            search_input = assert(splash:select('.gLFyf.gsfi'))
            search_input:focus()
            search_input:send_text(args.search_term)
            search_input:send_keys('<Enter>')

            splash:wait(4)
            -- overall_time = 8s

            -- iterates over type-of-search buttons and clicks on the "Noticias"/"News" one

            for i = 1, #assert(splash:select_all('div.hdtb-mitem a')) do
                search_type_btn = assert(splash:select_all('div.hdtb-mitem a')[i])
                text_content_btn = search_type_btn:text()
                if text_content_btn == 'Noticias' or text_content_btn == 'News' then
                    search_type_btn:mouse_click()
                    break
                end
            end

            splash:wait(4)
            -- overall_time = 12s

            -- clicks on "Herramientas"/"Tools" button
            
            tools_btn = assert(splash:select('#hdtb-tls'))
            tools_btn:mouse_click()
            splash:wait(2)
            -- overall_time = 16s


            -- iterates over option buttons and clicks on the "Reciente"/"Recent" one

            for i = 1, #assert(splash:select_all('div.hdtb-mn-hd div')) do
                option_btn = assert(splash:select_all('div.hdtb-mn-hd div')[i])
                text_content_btn = option_btn:text()
                if text_content_btn == 'Reciente' or text_content_btn == 'Recent' then
                    option_btn:mouse_click()
                    break
                end
            end

            splash:wait(2)
            -- overall_time = 18s

            -- iterates over suboptions buttons and clicks on the "Personalizar..."/"Custom range..." one
            customize_btn = splash:select('g-menu-item[jsname="NNJLud"] div div span')
            customize_btn:mouse_click()

            splash:wait(2)
            -- overall_time = 20s

            -- selects start_date button and inserts start date on it
            start_date_input = assert(splash:select('#OouJcb'))
            start_date_input:focus()
            start_date_input:send_text(args.start_date)

            splash:wait(2)
            -- overall_time = 22s

            -- selects end_date button and inserts end date on it
            end_date_input = assert(splash:select('#rzG2be'))
            end_date_input:focus()
            end_date_input:send_text(args.end_date)

            splash:wait(2)
            -- overall_time = 24s

            -- selects and presses "Ir"/"Go" button
            go_btn = assert(splash:select('g-button[jsaction="hNEEAb"]'))
            go_btn:mouse_click()

            splash:wait(4)
            -- overall_time = 28s

            -- the following only runs if target language is spanish
            if args.language == 'es-CO' then
                -- iterates over option buttons and clicks on the "Buscar en la Web" one
                for i = 1, #assert(splash:select_all('div.hdtb-mn-hd div')) do
                    option_btn = assert(splash:select_all('div.hdtb-mn-hd div')[i])
                    text_content_btn = option_btn:text()
                    if text_content_btn == 'Buscar en la Web' then
                        option_btn:mouse_click()
                        break
                    end
                end

                splash:wait(2)
                -- overall_time = 30s

                -- iterates over output-language buttons and clicks on the "Buscar páginas en Español" one 
                for i = 1, #assert(splash:select_all('g-menu-item[jsname="NNJLud"] div a')) do
                    search_type_btn = assert(splash:select_all('g-menu-item[jsname="NNJLud"] div a')[i])
                    text_content_btn = search_type_btn:text()
                    if text_content_btn == 'Buscar páginas en Español' then
                        search_type_btn:mouse_click()
                        break
                    end
                end

                splash:wait(4)
                -- overall_time = 34s
            end

            -- 28s <= overall_time <= 36s

            return splash:html()
        end
    '''

    # script2 = '''
    #     function main(splash, args)
    #         splash.private_mode_enabled = false
    #         splash.images_enabled = false

    #         -- splash:set_user_agent(splash.args.user_agent)    

    #         url = args.url
    #         assert(splash:go(url))
    #         splash:wait(2)

    #         return splash:html()
    #     end
    # '''

    def start_requests(self):

        search_terms = [term.upper() for term in self.search_terms.split(',')]
        language = self.language.lower()

        start_year, start_month, start_day = [int(date_element) for date_element in self.start_date.split('-')]
        end_year, end_month, end_day = [int(date_element) for date_element in self.end_date.split('-')]

        # search_terms = ['GRUPO ARGOS', 'BANCO BOGOTA', 'BANCOLOMBIA', 'CEMENTOS ARGOS', 'CELSIA', 'CORFICOLOMBIANA', 'DAVIVIENDA', 'ECOPETROL', 'GRUPO AVAL', 'GRUPO ENERGIA BOGOTA', 'ISA', 'NUTRESA', 'GRUPO SURA']
      
        search_terms = ['GRUPO ARGOS']
        language = 'es'
        start_year, start_month, start_day = 2022, 1, 1
        end_year, end_month, end_day = 2022, 1, 1
        
        end_date = date(end_year, end_month, end_day)

        for search_term in search_terms:
            temp_date = date(start_year, start_month, start_day)
            while temp_date <= end_date:
                yield SplashRequest(url = NewsSpider.BASE_URL,
                                    callback = self.parse, 
                                    meta = {'search_term': search_term, 'news_exact_date': temp_date.strftime('%Y-%m-%d')}, 
                                    endpoint = 'execute', 
                                    args = {'lua_source': self.script,
                                            'timeout': 90,
                                            'search_term': search_term,
                                            'language': 'en-CA' if language == 'en' else 'es-CO',
                                            'start_date': f'{temp_date.month}/{temp_date.day}/{temp_date.year}',
                                            'end_date': f'{temp_date.month}/{temp_date.day}/{temp_date.year}'})
                                            
                temp_date = temp_date + timedelta(days = 1)

    def parse(self, response):
        news_list = response.xpath('//div[@id="rso"]/div')

        for news in news_list:
            meta_info = response.request.meta.copy()
            news_title =  news.xpath('.//div[@role="heading"]/text()').get()
            news_url =  news.xpath('.//div[@role="heading"]/ancestor::a/@href').get()
            meta_info.update({'url': news_url, 'news_title': news_title})

            yield SplashRequest(url = news_url, callback = self.parse_news, meta = meta_info)

        # next_page_url = response.xpath('.//a[@id="pnnext"]/@href').get()

        # if next_page_url:
        #     yield SplashRequest(url = f'https://www.google.com{next_page_url}',
        #                         callback = self.parse,
        #                         meta = response.request.meta,
        #                         endpoint = 'execute', 
        #                         args = {'lua_source': self.script2})


    def parse_news(self, response):

        def _join_text_recursively(selector):
            output_str = ''

            if not selector.xpath('./child::node()'):
                return html_handler.handle(selector.get()).replace('\n', '')
            
            return output_str + ''.join([_join_text_recursively(selector) for selector in selector.xpath('./child::node()')])

        parents = response.xpath('//body//p/parent::node()')
        news_text_content = ''
        max_children = 0
        
        # Compute the highest number of paragraphs on each parent element
        for parent in parents:
            children = parent.xpath('./child::p')
            num_children = len(children)
            if num_children > max_children:
                max_children = num_children

        # Only search children of parent element with most children
        for parent in parents:
            children = parent.xpath('./child::p')
            num_children = len(children)

            if num_children == max_children:
                for child in children:
                    news_text_content += _join_text_recursively(child)
 
        yield {
            'search_term': response.request.meta['search_term'],
            'news_url_absolute': response.request.meta['url'],
            'news_exact_date': response.request.meta['news_exact_date'],
            'news_title': response.request.meta['news_title'].replace('\n', ''),
            'news_text_content': news_text_content,
        }        