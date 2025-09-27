#!/usr/bin/env python3
from time import sleep
from config import controllers

def main():
    try:
        while True:
            for c in controllers:
                c.run()
            sleep(1)
    except:
        for c in controllers:
            try:
                c.fallback()
            except:
                pass
        sleep(1)
        raise

if __name__ == '__main__':
    main()
