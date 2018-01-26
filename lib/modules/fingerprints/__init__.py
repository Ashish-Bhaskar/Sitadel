import importlib
import os
import pkgutil

from lib.config.settings import Risk
from lib.request import request
from lib.utils import output
from .. import IPlugin


class FingerprintPlugin(metaclass=IPlugin):
    # Default risk level for fingerprint module is NO DANGER since it only analyze one request response
    level = Risk.NO_DANGER

    def process(self, headers, content):
        raise NotImplementedError(str(self) + ": Process method not found")

    def __repr__(self):
        parent_module = self.__class__.__module__.split('.')[-2]
        return parent_module.title()


class Fingerprints:
    def __init__(self, agent, proxy, redirect, timeout, url, cookie):

        self.url = url
        self.cookie = cookie
        self.output = output.Output()
        self.request = request.Request(
            agent=agent,
            proxy=proxy,
            redirect=redirect,
            timeout=timeout
        )

    def run(self, plugins_activated):
        self.output.info('Launching fingerprints modules...')
        # Register the plugins from configuration
        for p in plugins_activated:
            currentdir = os.path.dirname(os.path.realpath(__file__))
            pkgpath = os.path.dirname(currentdir + "/%s/" % p)
            modules = [name for _, name, _ in pkgutil.iter_modules([pkgpath])]
            for module in modules:
                importlib.import_module(".{pkg}.{mod}".format(pkg=p, mod=module), __package__)
        try:
            # Send the recon request
            resp = self.request.send(
                url=self.url,
                method="GET",
                payload=None,
                headers=None,
                cookies=self.cookie
            )

            # Pass the result over the fingerprint module for processing
            fingerprints = (
                [(p(), p().process(resp.headers, resp.text)) for p in FingerprintPlugin.plugins])

            # Display findings for each category of modules
            for category, result in fingerprints:
                if result is not None:
                    self.output.finding('{category} detected: {result}'.format(category=category, result=result))

        except Exception as e:
            print(e)