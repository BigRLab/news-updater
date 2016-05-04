from subprocess import check_output

from owncloud_news_updater.updaters.api import Api, Feed
from owncloud_news_updater.updaters.updater import Updater, UpdateThread


class Cli:
    def run(self, commands):
        return check_output(commands)


class CliUpdater(Updater):
    def __init__(self, config, logger, api, cli):
        super().__init__(config, logger)
        self.cli = cli
        self.api = api

    def before_update(self):
        self.logger.info('Running before update command: %s' %
                         ' '.join(self.api.before_cleanup_command))
        self.cli.run(self.api.before_cleanup_command)

    def start_update_thread(self, feeds):
        return CliUpdateThread(feeds, self.logger,
                               self.api, self.cli)

    def all_feeds(self):
        feeds_json = self.cli.run(self.api.all_feeds_command).strip()
        feeds_json = str(feeds_json, 'utf-8')
        self.logger.info('Running get all feeds command: %s' %
                         ' '.join(self.api.all_feeds_command))
        self.logger.info('Received these feeds to update: %s' % feeds_json)
        return self.api.parse_feed(feeds_json)

    def after_update(self):
        self.logger.info('Running after update command: %s' %
                         ' '.join(self.api.after_cleanup_command))
        self.cli.run(self.api.before_cleanup_command)


class CliUpdateThread(UpdateThread):
    def __init__(self, feeds, logger, api, cli):
        super().__init__(feeds, logger)
        self.cli = cli
        self.api = api

    def update_feed(self, feed):
        command = self.api.update_feed_command + [str(feed.feedId),
                                                  feed.userId]
        self.logger.info('Running update command: %s' % ' '.join(command))
        self.cli.run(command)


class CliApi(Api):
    def __init__(self, config):
        directory = config.url
        phpini = config.phpini
        self.directory = directory.rstrip('/')
        base_command = ['php', '-f', self.directory + '/occ']
        if phpini is not None and phpini.strip() != '':
            base_command += ['-c', phpini]
        self.before_cleanup_command = base_command + [
            'news:updater:before-update']
        self.all_feeds_command = base_command + ['news:updater:all-feeds']
        self.update_feed_command = base_command + ['news:updater:update-feed']
        self.after_cleanup_command = base_command + [
            'news:updater:after-update']


class CliApiV2(CliApi):
    def __init__(self, config):
        super().__init__(config)

    def _parse_json(self, feed_json):
        feed_json = feed_json['data']['updater']
        return [Feed(info['feedId'], info['userId']) for info in feed_json]


def create_cli_api(config):
    if config.apilevel == 'v1-2':
        return CliApi(config)
    if config.apilevel == 'v2':
        return CliApiV2(config)
