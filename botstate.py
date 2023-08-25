import dotenv
import os
import time
import pickle

class Botstate:
    currentfile = ""
    token = dotenv.get_key("./.env", "TOKEN")
    allowed_ids = dotenv.get_key("./.env", "ALLOWED_USERIDS").split(":")
    repo_path = dotenv.get_key("./.env", "REPO_PATH")
    data_storage = dotenv.get_key("./.env", "DATA_STORAGE")
    datemode = True

    def __init__(self) -> None:
        self.storage_path = dotenv.get_key("./.env", "DATA_STORAGE")
        if (os.path.isfile(self.storage_path)):
            with open(self.storage_path, "rb") as objfile:
                instance = pickle.load(objfile)
                for k in instance.__dict__.keys():
                     setattr(self, k, getattr(instance, k))
        else:
            print("No storage file found - creating new state from scatch")

    def save(self) -> None:
         with open(self.storage_path, "wb") as objfile:
             pickle.dump(self, objfile)

    def setfile(self, path):
        self.currentfile = path
        self.save()

    def setdatemode(self, value):
        self.datemode = value
        self.save()

    def handleText(self, text):
        if (self.datemode):
           return time.strftime("\n%d.%m.%y - %H:%M:\n") + text
        else:
           return text