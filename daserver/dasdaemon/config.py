import ConfigParser

class DaSDConfig(ConfigParser.RawConfigParser, object):

    def get_section(self, section):
        """Get config section as dict"""
        return dict(self.items(section))

    def get_all(self):
        """Get entire config as dict"""
        output = {}
        for section in self.sections():
            output[section] = {}
            for item, value in self.items(section):
                output[section][item] = value
        return output
