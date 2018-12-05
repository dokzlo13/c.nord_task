#!/usr/bin/env sh


if [ "$1" = "tests" ]
then
  echo "Tests running"
  python -m doctest -v ./core/*.py
  python -m tornado.testing tests
fi

if [ "$1" = "server" ]
then
  echo "Server running"
  python app.py
fi
