import ConfigParser
from sojourner.malvern import *

# Helper class for accessing the data of a single conference
class Conference():
    def __init__(self, name):
        print "conference.py: __init__"
        print "Conference: set_name to %s" % name
        self.__name = name
        self.__config = ConfigParser.RawConfigParser()
        self.__config.read(sojourner_data_path('conferences/' + self.__name + '/' + self.__name))
        self.__schedule = self.__config.get(self.__name, 'schedule')
        print "conference.py: schedule url: %s" % self.__schedule
        self.__localxml = 'conferences/' + self.__name + '/schedule.xml'
        print "conference.py: local xml path: %s" % self.__localxml
        self.__banner = self.__config.get(self.__name, 'banner')
        print "conference.py: banner path: %s" % self.__banner
        print "conference.py: conference data loaded"

    def get_name(self):
        return self.__name

    def get_schedule_url(self):
        return self.__schedule

    def get_cached_xml(self):
        return self.__localxml

    def get_banner(self):
        return self.__banner
