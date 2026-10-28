"""DEMO FIXTURE"""
import csv


def read(path):
    with open(path) as f:
        return list(csv.DictReader(f))
