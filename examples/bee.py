#!/usr/bin/env -S uv run -q --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pycouchdb",
#     "requests",
#     "via-jsonpath",
# ]
#
# [tool.uv.sources]
# via-jsonpath = { path = "../", editable = true }
# ///

import json
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import date, timedelta
from functools import cached_property

import pycouchdb
import requests

from via_jsonpath import Rule, Via


@dataclass(kw_only=True, frozen=True)
class CouchDB:
    server: pycouchdb.Server
    db_name: str

    @cached_property
    def db(self):
        try:
            return self.server.database(self.db_name)
        except pycouchdb.exceptions.NotFound:
            self.server.create(self.db_name)
            return self.server.database(self.db_name)


@dataclass(kw_only=True, frozen=True)
class Deno:
    @cached_property
    def deno(self):
        deno = shutil.which("deno")
        if not deno:
            raise RuntimeError("Deno not found.")
        return deno

    def run_script(self, js: str):
        with tempfile.NamedTemporaryFile(suffix=".js") as f:
            f.write(js.encode())
            f.flush()
            result = subprocess.run(
                [self.deno, "run", f.name], capture_output=True, text=True
            )
            if result.returncode != 0:
                raise RuntimeError(f"Deno script failed: {result.stderr}")
            return result.stdout


@dataclass(kw_only=True, frozen=True)
class BeeSolver(Deno):
    def get_bee(self, date: str):
        url = f"https://beesolver.com/{date}/answers"
        res = requests.get(url).text.splitlines()
        data = [line for line in res if re.match(r"\s*const\s+data\s+=\s+", line)]
        if not data:
            raise RuntimeError("No data found")
        script = "\n".join([data[0], "console.log(JSON.stringify(data));"])
        res = self.run_script(script)
        return json.loads(res)


day = date.today()
cutoff = date(2022, 1, 1)

con = CouchDB(
    server=pycouchdb.Server("http://chaise:sofa@lego:5984/"),
    db_name="bee",
)

bee = BeeSolver()

via = Via(Rule(src="$[*].data", dst="$"))

while True:
    day -= timedelta(days=1)
    if day < cutoff:
        break
    try:
        doc = con.db.get(day.isoformat())
        print(f"Stopping at {day}")
        break
    except pycouchdb.exceptions.NotFound:
        pass
    stash = bee.get_bee(day.isoformat())
    cooked = via.transform(stash)
    print(f"Saving {day}")
    doc = {"_id": day.isoformat(), **cooked}
    con.db.save(doc)
