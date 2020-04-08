import configparser


class Config(object):
    config_parser = configparser.ConfigParser()
    config_parser.read('config/config.cfg')

    width = config_parser.getint('dimension', 'width', fallback=800)
    height = config_parser.getint('dimension', 'height', fallback=640)
    threshold = config_parser.getint('recognition', 'threshold', fallback=50)
    show_match_result = config_parser.getboolean('recognition', 'show_match_result', fallback=True)

    @staticmethod
    def save():
        with open('config/config.cfg', 'w') as config:
            Config.config_parser.write(config)
