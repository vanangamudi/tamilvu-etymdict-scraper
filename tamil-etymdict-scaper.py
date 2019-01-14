
import time
import argparse
from collections import Counter

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium import webdriver

from selenium.webdriver.common.keys import Keys

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


# tags, classes, ids for content extraction
INPUT_TEXTBOX_ID = 'txtNames1'

WORDS_POPUP_LIST_ID = 'ui-id-1'
WORDS_POPUP_LIST_CLASS = 'ui-autocomplete' # + ' ui-front ui-menu ui-widget ui-widget-content'
WORDS_POPUP_LIST_ITEMS_CLASS = 'ui-menu-item'

INITIAL_KEYWORD = 'காக்கைப்பித்து'
SUBMIT_BTN_ID = 'btnSearch'

def gather_words(wd):
    WORDS = Counter()
    input_text = INITIAL_KEYWORD
    
    lexicon = []
    with open('length_words_first.cleaned.txt', 'r') as f:
        lines = [l.strip().split('|')[0] for l in f.readlines() if len(l) < 5 and len(l) > 2]
        lexicon.extend(lines)

    words_already_lookedup = {}

    for i in tqdm(lexicon):
        input_text = i
        for max_len in reversed(range(1, 6)):
            try:
                while len(input_text) > max_len:
                    if input_text in words_already_lookedup:
                        input_text = input_text[:-1]
                        continue

                    words_already_lookedup[input_text] = 1
                    input_textbox = wd.find_element_by_id( INPUT_TEXTBOX_ID)
                    input_textbox.clear()
                    print('sending ', input_text)
                    input_textbox.send_keys(input_text + ' ')
                    WebDriverWait(wd, 10)
                    input_textbox.send_keys(Keys.BACK_SPACE)
                    input_text = input_text[:-1]

                    # Wait for the dynamically loaded elements to show up
                    WebDriverWait(wd, 10).until(
                        EC.visibility_of_element_located((By.CLASS_NAME, WORDS_POPUP_LIST_CLASS)))

                    html_page = wd.page_source
                    soup = BeautifulSoup(html_page, 'lxml')
                    new_words = [i.text for i in soup.find_all(class_=WORDS_POPUP_LIST_ITEMS_CLASS)]
                    WORDS.update(new_words)

                print('extracted {} words'.format(len(WORDS)))          

                with open('etymdict_lexicon.csv', 'w') as f:
                    f.write('\n'.join(WORDS.keys()))
                    f.flush()

            except:
                log.exception('ERROR: {}'.format(input_text))

                with open('etymdict_lexicon.csv', 'w') as f:
                    f.write('\n'.join(WORDS.keys()))
                    f.flush()

    wd.quit()



def gather_word_meanings(wd, words):
    words_already_lookedup = {}

    for i in tqdm(words):
        input_text = i
        try:
            words_already_lookedup[input_text] = 1
            input_textbox = wd.find_element_by_id( INPUT_TEXTBOX_ID)
            input_textbox.clear()
            print('sending ', input_text)
            input_textbox.send_keys(input_text)
            
            submit_btn = wd.find_element_by_id(SUBMIT_BTN_ID)
            submit_btn.click()
            wd.implicitly_wait(10)
            
            # Wait for the dynamically loaded elements to show up
            WebDriverWait(wd, 10).until(
                EC.visibility_of_element_located((By.CLASS_NAME, WORDS_POPUP_LIST_CLASS)))
            
            html_page = wd.page_source
            soup = BeautifulSoup(html_page, 'lxml')
            new_words = [i.text for i in soup.find_all(class_=WORDS_POPUP_LIST_ITEMS_CLASS)]
            WORDS.update(new_words)
            
            
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

    args = parser.parse_args()
    print(args)
    if not args.task == 'donothing':
        # Start the WebDriver and load the page
        wd = webdriver.Firefox()
        wd.get(URL)
        
        if args.task == 'words':
            gather_words(wd)
            
        if args.task == 'meanings':
            gather_word_meanings(wd, [])

    end = time.time()
    print('elasped: {}'.format(end-start))
