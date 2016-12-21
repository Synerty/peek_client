import logging
from typing import Type

from peek_plugin_base.PluginCommonEntryHookABC import PluginCommonEntryHookABC
from peek_plugin_base.client.PluginClientEntryHookABC import PluginClientEntryHookABC
from peek_client.plugin.PeekClientPlatformHook import PeekClientPlatformHook
from peek_platform.plugin.PluginLoaderABC import PluginLoaderABC
from peek_platform.plugin.PluginFrontendInstallerABC import PluginFrontendInstallerABC


logger = logging.getLogger(__name__)


class ClientPluginLoader(PluginLoaderABC, PluginFrontendInstallerABC):
    _instance = None

    def __new__(cls, *args, **kwargs):
        assert cls._instance is None, "ClientPluginLoader is a singleton, don't construct it"
        cls._instance = PluginLoaderABC.__new__(cls)
        return cls._instance

    def __init__(self, *args, **kwargs):
        PluginLoaderABC.__init__(self, *args, **kwargs)
        PluginFrontendInstallerABC.__init__(self, *args, platformService="client", **kwargs)

    @property
    def _entryHookFuncName(self) -> str:
        return "peekClientEntryHook"

    @property
    def _entryHookClassType(self):
        return PluginClientEntryHookABC

    @property
    def _platformServiceNames(self) -> [str]:
        return ["client"]

    def loadAllPlugins(self):
        PluginLoaderABC.loadAllPlugins(self)
        self.buildFrontend()

    def unloadPlugin(self, pluginName: str):
        PluginLoaderABC.unloadPlugin(self, pluginName)

        # Remove the Plugin resource tree
        from peek_client.backend.SiteRootResource import root as serverRootResource
        try:
            serverRootResource.deleteChild(pluginName.encode())
        except KeyError:
            pass

    def _loadPluginThrows(self, pluginName: str, EntryHookClass: Type[PluginCommonEntryHookABC],
                        pluginRootDir: str) -> None:
        # Everyone gets their own instance of the plugin API
        platformApi = PeekClientPlatformHook()

        pluginMain = EntryHookClass(pluginName=pluginName,
                                  pluginRootDir=pluginRootDir,
                                  platform=platformApi)

        # Load the plugin
        pluginMain.load()

        # Start the Plugin
        pluginMain.start()

        # Add all the resources required to serve the backend site
        # And all the plugin custom resources it may create
        from peek_client.backend.SiteRootResource import root as serverRootResource
        serverRootResource.putChild(pluginName.encode(), platformApi.rootResource)

        self._loadedPlugins[pluginName] = pluginMain


