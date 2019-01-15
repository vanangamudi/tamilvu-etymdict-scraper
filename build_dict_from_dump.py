
import time
import copy
import argparse
from collections import Counter, namedtuple

from bs4 import BeautifulSoup
from tqdm import tqdm

from pprint import pprint, pformat

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

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

Record = namedtuple("Record",
                   ['word',
                    'word_sense',
                    'pos',
                    'pronounication',
                    'tamil_meaning',
                    'english_meaning',
                    'reference',
                    'etymology'])

def build_records(args, word, span):
    records         = []
    
    word_sense      = ''
    pos             = ''
    pronounciation  = ''
    tamil_meaning   = ''
    english_meaning = ''
    reference       = ''
    etymology       = ''

    stop = False
    current_tag = list(span.children)[0]
    for i, current_tag in enumerate(span.descendants):
        try:
            print('========')
            log.info('{} current_tag.name: {}'.format(i, current_tag.name))
            log.info('{}   {}'.format(i, current_tag))

            if current_tag.name == '<br/>':
                continue
            
            elif current_tag.name == 'font':
                log.info(' {}'.format(current_tag.get('color')))
                log.info(' {}'.format(current_tag.text))
                if current_tag.has_attr('color'):                    
                    if 'Red' in current_tag.get('color'):
                        r = Record(word
                                   , word_sense
                                   , pos       
                                   , pronounciation  
                                   , tamil_meaning   
                                   , english_meaning 
                                   , reference       
                                   , etymology)
                        
                        records.append(r)                        
                        
                        word_sense      = ''
                        pos             = ''
                        pronounication  = ''
                        tamil_meaning   = ''
                        english_meaning = ''
                        reference       = ''
                        etymology       = ''
                        
                        word_sense = current_tag.text.strip()
                        just_got_word_sense = True
                        
                    if 'blue' in current_tag.get('color'):
                        if just_got_word_sense == True:
                            pronounciation = current_tag.text.strip()
                        else:
                            english_meaning = current_tag.text.strip()
                        just_got_word_sense = False
                        
                    if 'Green' in current_tag.get('color'):
                        pos = current_tag.text.strip()
                        just_got_pos = True

            
        except:
            log.exception(current_tag)

    pprint(locals())
    r = Record(word
               , word_sense
               , pos       
               , pronounciation  
               , tamil_meaning   
               , english_meaning 
               , reference       
               , etymology)
    
    records.append(r)
    return records

        
    
def build_dict(args):
    word_meanings = [ i.split('||') for i in open(args.dump_filepath).readlines()]
    records = []
    for i, (word, meanings) in enumerate(tqdm(word_meanings)):
        soup = BeautifulSoup(meanings, 'lxml')
        span = soup.find('span', id='lblResults')
        try:    
            records.extend(build_records(args, word,  span))
        except:
            log.exception('ERROR: {}'.format(word))
            
    return records

if __name__ == '__main__':

    start = time.time()

    parser = argparse.ArgumentParser(description='Scrape words and word meanings from tamilvu.org')
    parser.add_argument('-d', '--prefix-dir',
                        help='path to the results',
                        default='run00', dest='prefix_dir')


    parser.add_argument('--default', default='default', dest='task')
    parser.add_argument('--dump-filepath', default=WORD_MEANINGS_DUMP_FILEPATH, dest='dump_filepath')
    
    """
    subparsers = parser.add_subparsers(help='commands')
    words_parser = subparsers.add_parser('words', help='starts wordsing')
    words_parser.add_argument('--words', default='words', dest='task')

    word_meanings_parser = subparsers.add_parser('meanings', help='starts word_meaning')
    word_meanings_parser.add_argument('--word-meanings', default='word_meanings', dest='task')
    word_meanings_parser.add_argument('--count', default=10000000, dest='count', type=int)
    word_meanings_parser.add_argument('--offset', default=0, dest='offset', type=int)
    word_meanings_parser.add_argument('--batch-size', default=50, dest='batch_size', type=int)
    """
    
    args = parser.parse_args()
    print(args)
    if args.task == 'default':
        records = build_dict(args)
        pprint(records)
        
    end = time.time()
    print('elasped: {}'.format(end-start))
