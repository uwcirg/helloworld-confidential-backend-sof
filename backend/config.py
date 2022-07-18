"""Default configuration

Use env var to override
"""
import os

SERVER_NAME = os.getenv("SERVER_NAME", "localtest.me:5000")
SECRET_KEY = os.getenv("SECRET_KEY", "59f7dd09-e830-4e93-a36d-23a53c06d944")

SOF_CLIENT_ID = os.getenv("SOF_CLIENT_ID", "HelloWorldConfidential")
SOF_CLIENT_SECRET = os.getenv("SOF_CLIENT_SECRET", "b3f3793f-7f9f-471b-9138-81744a2974e7")
SOF_CLIENT_SCOPES = os.getenv("SOF_CLIENT_SCOPES", "patient/*.read launch/patient")

LAUNCH_DEST = os.getenv("LAUNCH_DEST", "localtest.me:3000")
VERSION_STRING = os.getenv("VERSION_STRING")
