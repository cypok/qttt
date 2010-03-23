import os
import sys
import yaml

class Config:
    @staticmethod
    def set_if_empty(d, key, value):
        if key not in d:
            d[key] = value

    def __init__(self):
        if len(sys.argv) > 1:
            self.config_file = sys.argv[1]
        else:
            self.config_file = os.path.expanduser('~/.tttrc')
        self.data = {}

    def read(self):
        with open(self.config_file) as f:
            self.data = yaml.load(f.read())

    def write(self):
        with open(self.config_file, 'w') as f:
            f.write( yaml.dump(self.data, default_flow_style = False, explicit_start = True) )

    def __getitem__(self, item):
        return self.data.get(item)
    
    def __setitem__(self, item, value):
        self.date[item] = value

    def set_defaults(self):
        self.set_if_empty(self.data, 'qttt', {})

        self.set_if_empty(self.data['qttt'], 'db_path', '~/.ttt/updates.db')
        
        self.set_if_empty(self.data['qttt'], 'geometry', {})

        self.set_if_empty(self.data['qttt']['geometry'], 'left', 400)
        self.set_if_empty(self.data['qttt']['geometry'], 'top', 50)
        self.set_if_empty(self.data['qttt']['geometry'], 'width', 350)
        self.set_if_empty(self.data['qttt']['geometry'], 'height', 550)
