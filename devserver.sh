#!/bin/sh

nix develop

uvicorn main:app --reload --host 0.0.0.0 --port 9002