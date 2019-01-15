
import time
import argparse
from collections import Counter

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium import webdriver

from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import StaleElementReferenceException

from bs4 import BeautifulSoup
from tqdm import tqdm

from pprint import pprint, pformat

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def mkdir(path):
    if os.path.exists(path):
        return
    log.info('creating {}'.format(path))
    if os.makedirs(path):
        log.info('created {}'.format(path))


URL = 'http://stream1.tamilvu.in/etytamildict/TamilDemo.aspx'

WORDS_FILEPATH   = 'etymdict_lexicon.csv'
LEXICON_FILEPATH = 'length_words_first.cleaned.txt'
LETTERS_FILEPATH = 'letters_from_tace16_data.csv'

WORD_MEANINGS_DUMP_FILEPATH = 'word_meanings.dump.csv'

# tags, classes, ids for content extraction
INPUT_TEXTBOX_ID = 'txtNames1'

WORDS_POPUP_LIST_ID          = 'ui-id-1'
WORDS_POPUP_LIST_CLASS       = 'ui-autocomplete' # + ' ui-front ui-menu ui-widget ui-widget-content'
WORDS_POPUP_LIST_ITEMS_CLASS = 'ui-menu-item'

INITIAL_KEYWORD = 'காக்கைப்பித்து'
SUBMIT_BTN_ID   = 'btnSearch'

def gather_words(args, wd):
    WORDS = Counter()
    input_text = INITIAL_KEYWORD
    
    __LEXICON__ = []
    with open(LEXICON_FILEPATH, 'r') as f:
        for l in f.readlines():
            l = l.strip()
            if len(l) < 5 and len(l) > 2:
                __LEXICON__.append(l.split('|')[0])
            

    words_already_lookedup = {}

    for i in tqdm(__LEXICON__):
        input_text = i
        for max_len in reversed(range(1, 6)):
            try:
                while len(input_text) > max_len:
                    if input_text in words_already_lookedup:
                        input_text = input_text[:-1]
                        continue

                    words_already_lookedup[input_text] = 1

                    print('sending ', input_text)
                    input_textbox = wd.find_element_by_id(INPUT_TEXTBOX_ID)
                    input_textbox.clear()
                    input_textbox.send_keys(input_text + ' ')
                    WebDriverWait(wd, 10)
                    input_textbox.send_keys(Keys.BACK_SPACE)

                    WebDriverWait(wd, 10).until(
                        EC.visibility_of_element_located(
                            (By.CLASS_NAME, WORDS_POPUP_LIST_CLASS)))

                    html_page = wd.page_source
                    soup      = BeautifulSoup(html_page, 'lxml')
                    new_words = [i.text for i in
                                 soup.find_all(class_=WORDS_POPUP_LIST_ITEMS_CLASS)]
                    
                    WORDS.update(new_words)
                    
                    input_text = input_text[:-1]

                    
                print('extracted {} words'.format(len(WORDS)))          

                with open(WORDS_FILEPATH, 'w') as f:
                    f.write('\n'.join(WORDS.keys()))
                    f.flush()

            except:
                log.exception('ERROR: {}'.format(input_text))

                with open(WORDS_FILEPATH, 'w') as f:
                    f.write('\n'.join(WORDS.keys()))
                    f.flush()

    wd.quit()

class wait_for_the_attribute_value(object):
    """
    https://stackoverflow.com/questions/43813170/using-selenium-webdriver-to-wait-the-attribute-of-element-to-change-value
    """

    def __init__(self, locator, attribute, value):
        self.locator = locator
        self.attribute = attribute
        self.value = value

    def __call__(self, driver):
        try:
            elements  = EC._find_elements(driver, self.locator)
            for element in elements:
                attribute = element.get_attribute(self.attribute)
                if attribute == self.value:
                    return True
                
            return False
        except StaleElementReferenceException:
            log.exception()
            return False

        
def gather_word_meanings(args, words=[]):
    if len(words) < 1:
        s = args.offset
        e = s + args.count
        words = open(WORDS_FILEPATH).read().split('\n')  [s:e]
        
        log.info('loaded {} words from {}'.format(len(words), WORDS_FILEPATH))

        """
        letters = open(LETTERS_FILEPATH).read().split('\n')
        log.info('loaded {} letter from {}'.format(len(letters), LETTERS_FILEPATH))
        """
        
    word_meanings_dump_file = open('{}_{}_{}'.format(WORD_MEANINGS_DUMP_FILEPATH,
                                                     s, e)
                                   , 'w')

    num_batches =  len(words)// args.batch_size
    for i in tqdm(range(num_batches)):
        batch = words[i * args.batch_size : (i+1) * args.batch_size]
        
        print('refreshing driver...')
        wd = webdriver.Firefox()
        wd.get(URL)
        
        for j, input_text in enumerate(tqdm(batch, desc='{}/{}'.format(i, num_batches))):
            try:

                #print('sending ', input_text)
                input_textbox = wd.find_element_by_id(INPUT_TEXTBOX_ID)
                input_textbox.clear()
                input_textbox = wd.find_element_by_id(INPUT_TEXTBOX_ID)
                input_textbox.send_keys(input_text)

                submit_btn = wd.find_element_by_id(SUBMIT_BTN_ID)
                submit_btn.click()
                WebDriverWait(wd, 10).until(
                    wait_for_the_attribute_value((By.TAG_NAME, 'span'),
                                                 'id',
                                                 'lblResults'))

                html_page = wd.page_source
                soup = BeautifulSoup(html_page, 'lxml')
                span = soup.find('span', id='lblResults')

                word_meanings_dump_file.write(
                    '||'.join( [input_text, span.prettify().replace('\n', '')] ) + '\n'
                )

                """
                #print(span.prettify())

                for i in [BeautifulSoup(i, 'lxml') for i in str(span).split('<br/>') if i]:
                    print(i.prettify())

                print('===')
                """
            except:
                log.exception('ERROR: {}'.format(input_text))


        wd.quit()
        

if __name__ == '__main__':

    start = time.time()

    parser = argparse.ArgumentParser(description='Scrape words and word meanings from tamilvu.org')
    parser.add_argument('-d', '--prefix-dir',
                        help='path to the results',
                        default='run00', dest='prefix_dir')
    
    parser.add_argument('--do-nothing', default='donothing', dest='task')
    subparsers = parser.add_subparsers(help='commands')
    words_parser = subparsers.add_parser('words', help='starts wordsing')
    words_parser.add_argument('--words', default='words', dest='task')

    word_meanings_parser = subparsers.add_parser('meanings', help='starts word_meaning')
    word_meanings_parser.add_argument('--word-meanings', default='word_meanings', dest='task')
    word_meanings_parser.add_argument('--count', default=10000000, dest='count', type=int)
    word_meanings_parser.add_argument('--offset', default=0, dest='offset', type=int)
    word_meanings_parser.add_argument('--batch-size', default=50, dest='batch_size', type=int)

    args = parser.parse_args()
    print(args)
    if not args.task == 'donothing':

        
        if args.task == 'words':
            # Start the WebDriver and load the page
            wd = webdriver.Firefox()
            wd.get(URL)
            gather_words(args, wd)
            wd.quit()
            
        if args.task == 'word_meanings':
            gather_word_meanings(args) #, ['கரந்தை'])
        
    end = time.time()
    print('elasped: {}'.format(end-start))
