import pytest
from immigration_monitor.db import Store, now
from immigration_monitor.fetch import Response
from immigration_monitor.extract import extract
from immigration_monitor.monitor import run_checks

URL='https://www.canada.ca/fictional-test'


def page(word='must',extra='',nav='Home'):
    return f'<html><title>Fictional test guidance</title><nav>{nav}</nav><main><h1>Fictional Employer Requirements</h1><p>Employers {word} provide supporting evidence for this fictional example program. This is test content only.</p>{extra}</main></html>'.encode()


class FakeFetcher:
    def __init__(self,response): self.response=response;self.calls=[]
    def fetch(self,url,headers=None):
        self.calls.append((url,headers))
        if isinstance(self.response,Exception): raise self.response
        return self.response if isinstance(self.response,Response) else Response(200,url,self.response,{'content-type':'text/html','etag':'"test"'})


@pytest.fixture
def store(tmp_path):
    return Store(tmp_path/'data')


@pytest.fixture
def source(store):
    with store.connect() as db:
        id=db.execute('INSERT INTO sources(title,url,agency,tags,source_type,next_due) VALUES (?,?,?,?,?,?)',
            ('Fictional test',URL,'Test agency','test','public guidance',now())).lastrowid
    return id


def check(store,source,body):
    return run_checks(store,source_id=source,fetcher=FakeFetcher(body),extractor=extract)
