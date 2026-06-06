#!/usr/bin/env python3
"""Deterministic PDD operation analyzer for GitHub Issues.

This script intentionally uses only Python standard library.
It reads the GitHub issue event JSON, extracts structured fields from the issue body,
and writes a stable Markdown report. No API key is required.
"""

import argparse
import json
import re
from pathlib import Path

FIELDS = [
    "商品名称",
