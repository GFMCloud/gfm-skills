# pond-sensor

<!-- Demo material for a skill trial, not real. -->

## Background

This project reads the temperature and oxygen sensors in a garden pond and posts the readings to a
small dashboard. It began as a weekend project. It is written in Python. Python is a programming
language that is popular for small hardware projects. The sensors talk over I2C, which is a
two-wire bus for connecting chips.

## General guidance

- Be careful and thorough.
- Think step by step.
- Write good, clean code that is easy to read.
- Make sure your changes work.
- Follow best practices.
- Don't be lazy.
- Always do your best.
- Ask if anything is unclear.

## Layout

- `sensor/` reads the sensors
- `dashboard/` serves the page
- `tests/` holds the tests
- `requirements.txt` lists the packages

## Commands

- `python3 -m pytest` runs the tests
- `python3 -m dashboard` starts the dashboard

## Rules

1. Run `python3 -m pytest` before saying a change works.
2. Oxygen readings below 4 mg/L page the owner; never change that threshold without asking.
3. Don't use print for logging.
4. Be thorough.
5. Run the tests before you finish.
