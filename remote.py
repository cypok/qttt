import httplib2
import urllib
import json

class Remote:
    def __init__(self, config):
        self.api_key = config['site']['api_key']
        self.url = config['site']['base_url']

        self.http = httplib2.Http()

    def getUser(self):
        params = {'api_key':self.api_key}
        url = '%s/account.json?%s' % (self.url, urllib.urlencode(params))
        type = 'GET'
        res = json.loads(self.http.request(url, type)[1])
        return res

    def getProjects(self):
        params = {'api_key':self.api_key}
        url = '%s/projects.json?%s' % (self.url, urllib.urlencode(params))
        type = 'GET'
        res = json.loads(self.http.request(url, type)[1])
        return res

    def sendUpdate(self, text):
        url = '%s/updates.json?%s' % (self.url, urllib.urlencode({'api_key':self.api_key}))
        type = 'POST'
        data = 'update[human_message]=%s' % unicode(text).encode('utf-8')
        res = json.loads(self.http.request(url, type, data)[1])
        return (res.get('error') is None), res

    def editUpdate(self, upd, data):
        url = '%s/updates/%s.json?%s' % (self.url, upd.uuid, urllib.urlencode({'api_key':self.api_key}))
        type = 'POST'
        data = '_method=put&update[human_message]=%s&update[started_at]=%s&update[finished_at]=%s&update[hours]=%s' % (
                unicode(data['message']).encode('utf-8'),
                data['started_at'].isoformat(),
                data['finished_at'].isoformat() if data.get('finished_at') is not None else '',
                data['hours'] if data.get('hours') is not None else ''
        )
        res = json.loads(self.http.request(url, type, data)[1])
        return (res.get('error') is None), res

    def deleteUpdate(self, upd):
        url = '%s/updates/%s.json?%s' % (self.url, upd.uuid, urllib.urlencode({'api_key':self.api_key}))
        type = 'POST'
        data = '_method=delete'
        res = json.loads(self.http.request(url, type, data)[1])
        return (res.get('error') is None), res

    def getUpdates(self, since=None):
        params = {'api_key':self.api_key,'limit':45}
        #if since:
            #params['since'] = since
        url = '%s/updates.json?%s' % (self.url, urllib.urlencode(params))
        type = 'GET'
        res = json.loads(self.http.request(url, type)[1])
        return res

    def getLastUpdate(self):
        url = '%s/updates/last.json?%s' % (self.url, urllib.urlencode({'api_key':self.api_key}))
        type = 'GET'
        res = json.loads(self.http.request(url, type)[1])
        return (res if res.get('error') is None else None)

    def finishLast(self):
        url = '%s/updates/finish_last.json?%s' % (self.url, urllib.urlencode({'api_key':self.api_key}))
        type = 'POST'
        json.loads(self.http.request(url, type)[1])


