import dotenv
import os
import time
import pickle

class Botstate:
    _file = ""
    data_storage = dotenv.get_key("./.env", "DATA_STORAGE")
    _datemode = True
    _keepspeech = False

    def __init__(self) -> None:
        self.storage_path = dotenv.get_key("./.env", "DATA_STORAGE")
        if (os.path.isfile(self.storage_path)):
            with open(self.storage_path, "rb") as objfile:
                instance = pickle.load(objfile)
                for k in instance.__dict__.keys():
                     setattr(self, k, getattr(instance, k))
        else:
            print("No storage file found - creating new state from scatch")

        #always load these from disk!
        self.allowed_ids = dotenv.get_key("./.env", "ALLOWED_USERIDS").split(":")
        self.repo_path = dotenv.get_key("./.env", "REPO_PATH")

    def save(self) -> None:
         with open(self.storage_path, "wb") as objfile:
             pickle.dump(self, objfile)

    @property
    def file(self):
        return self._file
    
    @file.setter
    def file(self, path):
        self._currentfile = path
        self.save()

    @property
    def datemode(self):
        return self._datemode

    @datemode.setter
    def datemode(self, value):
        self._datemode = value
        self.save()

    @property
    def keepspeech(self):
        return self._keepspeech

    @keepspeech.setter
    def keepspeech(self, value):
        self._keepspeech = value
        self.save()

    def handleText(self, text):
        if (self._datemode):
           return f"({time.time()}) - " + time.strftime("%d.%m.%y - %H:%M:\n") + text
        else:
            return text
