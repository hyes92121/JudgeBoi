import sys
import logging
import datetime

# define a global logger for all files. This is the parent of all loggers in distinct files.
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# configure streamhandler
sh = logging.StreamHandler(sys.stdout)
str_fmt = "%(name)s - %(message)s"
fmter = logging.Formatter(str_fmt)
sh.setFormatter(fmter)

# configure filehandler
fh = logging.FileHandler("logs/{}.log".format(datetime.datetime.now().strftime("%m%d.%H%M")), mode='a')
strfmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
datefmt = "%Y-%m-%d %H:%M"
fmter = logging.Formatter(strfmt, datefmt)
fh.setFormatter(fmter)

# add handlers to logger
logger.addHandler(sh)
logger.addHandler(fh)
