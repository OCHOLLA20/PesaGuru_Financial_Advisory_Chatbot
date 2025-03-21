import os
import sys
import time
import json
import csv
import statistics
import requests
import concurrent.futures
import matplotlib.pyplot as plt
import numpy as np
import psutil
import random  # Add this import to fix the undefined variable errors
from datetime import datetime, timedelta
import logging
from functools import wraps
from typing import Dict, List, Tuple, Any, Callable
import argparse

# Selenium for browser performance testing
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Import locust for distributed load testing if available
try:
    from locust import HttpUser, task, between
    LOCUST_AVAILABLE = True
except ImportError:
    LOCUST_AVAILABLE = False
    print("Locust not installed. Distributed load testing will be disabled.")