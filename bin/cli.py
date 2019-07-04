import sys
import os
from multiprocessing import Pool, Queue
import click
from bin.im import poolMangaer as im_run
import time

IDS = []
CMDS = Queue()

_FUNC = []
_ARGS = []



def cli(num):
    global IDS
    global  POOLNUM
    POOLNUM = num
    if id.find("-") > 0:
        start, stop = id.split("-")
        print(start)
        print(stop)
        IDS = [id for id in range(int(start), int(stop) + 1)]
    elif id.find(",") > 0:
        IDS = [int(i.strip()) for i in id.split(",")]
    else:
        IDS.append(int(id))
    # try:
    #
    # except:
    #     IDS.append(int(id))
    # click.secho("ID段: {}".format(IDS), bg="green", fg="black")

    pass


