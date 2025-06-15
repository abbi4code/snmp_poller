#!/usr/bin/env python3

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__),'poller'))

from main import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())