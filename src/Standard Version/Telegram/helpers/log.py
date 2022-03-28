import logging
import os
import sys

folder = os.path.join(os.path.dirname(sys.argv[0]))
os.chdir(folder)
if not os.path.exists('Logs'):
    os.mkdir('Logs')
log_filename = os.path.join(os.path.dirname(sys.argv[0]), 'Logs/aio.log')
log = logging.getLogger('AIO - Telegram')
logging.basicConfig(
    filename=log_filename,
    level=logging.ERROR,
    format='[%(asctime)s]-[%(name)s] - %(levelname)s - %(message)s',
    datefmt='%d-%b-%y %H:%M:%S'
)
