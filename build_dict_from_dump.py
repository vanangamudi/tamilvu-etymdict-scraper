import re
import time
import copy
import argparse
from collections import Counter, namedtuple

from bs4 import BeautifulSoup
from tqdm import tqdm

from pprint import pprint, pformat

import logging
FORMAT_STRING = "%(levelname)-8s:%(name)-8s.%(funcName)-8s>> %(message)s"
logging.basicConfig(format=FORMAT_STRING)
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

RECORD_FIELDS = ['word',
                 'word_sense',
                 'pos',
                 'pronounication',
                 'tamil_meaning',
                 'english_meaning',
                 'reference',
                 'etymology',
                 'example',
                 'alternatives',
                 'unparsed_content']

Record = namedtuple("Record", RECORD_FIELDS)

from enum import Enum
class STATE(Enum):
    FOUND_INITIAL_STATE          = -1
    FOUND_WORD_SENSE             = 0
    FOUND_PRONOUNCIATION         = 1
    FOUND_POS                    = 2
    FOUND_REFERENCE              = 3
    FOUND_TAMIL_MEANING          = 4
    FOUND_ENGLISH_MEANING        = 5
    FOUND_ETYMOLOGY              = 6
    FOUND_EXAMPLE                = 7
    FOUND_BREAK                  = 8
    FOUND_SUPERSCRIPT            = 9
    FOUND_ALTERNATIVE_SPELLINGS  = 10

def build_records(args, word, span):
    records         = []
    
    word_sense      = ''
    pos             = ''
    pronounciation  = ''
    tamil_meaning   = ''
    english_meaning = ''
    reference       = ''
    etymology       = ''
    example         = ''
    alternatives    = ''
    unparsed_content= ''

    stop = False
    CURRENT_STATE = STATE.FOUND_INITIAL_STATE
    PREV_STATE    = STATE.FOUND_INITIAL_STATE

    def add_to_records(log_info):
        log.info('{} == adding to records'.format(log_info))
        r = Record(word
                   , word_sense
                   , pos       
                   , pronounciation  
                   , tamil_meaning   
                   , english_meaning 
                   , reference       
                   , etymology
                   , example
                   , alternatives
                   , unparsed_content)
        
        records.append(r)        

    for i, current_tag in enumerate(span.contents):
        used_up = False
        try:
            log.info('== {} current_tag.name: {}'.format(i, current_tag.name))
            log.info('== {}   {}'.format(i, current_tag))

            if current_tag.name == '<br/>':
                CURRENT_STATE = STATE.FOUND_BREAK
                used_up = True
                
            elif current_tag.name == 'font':

                log.info(' font  {}'.format(current_tag.get('color')))
                log.info(' text  {}'.format(current_tag.text))
                if current_tag.has_attr('color'):

                    if 'Red' in current_tag.get('color'):
                        log.info('STATE.FOUND_WORD_SENSE')
                        CURRENT_STATE = STATE.FOUND_WORD_SENSE
                        
                        add_to_records('found red')
                        
                        word_sense      = ''
                        pos             = ''
                        pronounication  = ''
                        tamil_meaning   = ''
                        english_meaning = ''
                        reference       = ''
                        etymology       = ''
                        example         = ''
                        
                        word_sense = current_tag.text.strip()
                        used_up = True
                        
                    if 'blue' in current_tag.get('color'):

                        if PREV_STATE == STATE.FOUND_WORD_SENSE:
                            log.info('STATE.FOUND_PRONOUNCIATION')
                            CURRENT_STATE = STATE.FOUND_PRONOUNCIATION
                            pronounciation = current_tag.text.strip()
                            used_up = True
                            
                        elif PREV_STATE == STATE.FOUND_TAMIL_MEANING:
                            log.info('STATE.FOUND_TAMIL_MEANING')
                            CURRENT_STATE = STATE.FOUND_ENGLISH_MEANING
                            english_meaning = current_tag.text.strip()
                            used_up = True
                            
                    if 'Green' in current_tag.get('color'):
                        log.info('STATE.FOUND_POS')
                        CURRENT_STATE = STATE.FOUND_POS
                        pos = current_tag.text.strip()
                        used_up = True
                        
            elif current_tag.name == None:
                if re.search('^\d+\..*', current_tag.string):
                    log.info('STATE.FOUND_TAMIL_MEANING')
                    CURRENT_STATE = STATE.FOUND_TAMIL_MEANING

                    add_to_records('From NONE')
                    
                    tamil_meaning   = current_tag.string
                    english_meaning = ''
                    reference       = ''
                    etymology       = ''
                    example         = ''

                    used_up = True
                        
                elif ';' in current_tag.string.strip():
                    if len(current_tag.string.strip()) > 1:
                        log.info('STATE.FOUND_TAMIL_MEANING')
                        CURRENT_STATE = STATE.FOUND_TAMIL_MEANING
                        
                        add_to_records('from NONE->;')
                        tamil_meaning   = current_tag.string
                        english_meaning = ''
                        reference       = ''
                        etymology       = ''
                        example         = ''
                        tamil_meaning = current_tag.string

                        used_up = True
                        
                elif current_tag.string.strip().startswith('['):
                    log.info('STATE.FOUND_ETYMOLOGY')
                    CURRENT_STATE = STATE.FOUND_ETYMOLOGY
                    etymology = current_tag.string

                    used_up = True
                                            
                elif len(current_tag.string.strip()) < 30:
                    if PREV_STATE == STATE.FOUND_BREAK:
                        log.info('STATE.FOUND_TAMIL_MEANING')
                        CURRENT_STATE = STATE.FOUND_TAMIL_MEANING
                        
                        add_to_records('from NONE-> len < 30')
                        tamil_meaning   = current_tag.string
                        english_meaning = ''
                        reference       = ''
                        etymology       = ''
                        example         = ''
                        tamil_meaning = current_tag.string

                        used_up = True
                        
                    
            elif current_tag.name == 'i':
                if current_tag.text.strip().startswith('('):
                    if '.' in current_tag.text:
                        log.info('PREV_STATE -- found .')
                        CURRENT_STATE = PREV_STATE
                        reference = current_tag.text
                        used_up = True
                        
                    elif PREV_STATE == STATE.FOUND_EXAMPLE:
                        log.info('STATE.FOUND_REFERENCE')
                        CURRENT_STATE = STATE.FOUND_REFERENCE
                        reference = current_tag.text
                        used_up = True
                        
                    else:
                        if PREV_STATE == STATE.FOUND_WORD_SENSE:
                            log.info('STATE.FOUND_WORD_SENSE - alternatives')
                            CURRENT_STATE = STATE.FOUND_WORD_SENSE
                            alternatives = '//'.join([alternatives, current_tag.text])
                            used_up = True

                if current_tag.text.strip().startswith('"'):
                    log.info('STATE.FOUND_EXAMPLE')
                    CURRENT_STATE = STATE.FOUND_EXAMPLE
                    example = '//'.join([example, current_tag.text])
                    used_up = True
            elif 'sup' in current_tag.name:
                log.info('STATE.FOUND_SUPERSCRIPT')
                CURRENT_STATE = STATE.FOUND_SUPERSCRIPT
                if PREV_STATE == STATE.FOUND_WORD_SENSE:
                    log.info('STATE.FOUND_WORD_SENSE')
                    CURRENT_STATE = STATE.FOUND_WORD_SENSE
                    word_sense += current_tag.string
                    used_up = True

            if used_up == False:
                if current_tag.string:
                    s = current_tag.string
                else:
                    s = current_tag.text

                if s:
                    unparsed_content = '//'.join([unparsed_content, s])
            
            
        except:
            log.exception(current_tag)

        PREV_STATE = CURRENT_STATE

    print('===')
    add_to_records('end of for loop')
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
        print(len(records))

        with open('dict.csv', 'w') as f:
            f.write('|'.join(i for i in RECORD_FIELDS) + '\n')
            
            records = ['|'.join(i for i in r) for r in records]
            f.write('\n'.join(reversed(records)))
        
    end = time.time()
    print('elasped: {}'.format(end-start))
