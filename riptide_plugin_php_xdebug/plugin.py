import json
import os
from typing import Dict, TYPE_CHECKING, Union

import click
from click import style, echo

from riptide.config.document.command import Command
from riptide.config.document.service import Service
from riptide.config.files import get_project_meta_folder
from riptide.plugin.abstract import AbstractPlugin
from riptide.util import SystemFlag
from riptide_cli.helpers import cli_section, async_command, warn, RiptideCliError

if TYPE_CHECKING:
    from riptide.config.document.config import Config
    from riptide.config.document.project import Project
    from riptide.engine.abstract import AbstractEngine

CMD_XDEBUG = 'xdebug'

ENABLED_FLAG_NAME = 'enabled'
XDEBUG3_FLAG_NAME = 'xdebug3'
MODE_FLAG_NAME = 'mode'
REQUEST_TRIGGER_FLAG_NAME = 'request_trigger'
PARAMETERS_FLAG_NAME = 'parameters'

XDEBUG_PLUGIN_STATE_FILE = '.xdebug.json'
VERSION_ENV = 'RIPTIDE_XDEBUG_VERSION'
VERSION_LABEL = 'php_xdebug_version'
VERSION_VALID = ('2', '3')
WARNING_URL = 'https://github.com/theCapypara/riptide-plugin-php-xdebug#xdebug-version'


class PhpXdebugPlugin(AbstractPlugin):
    def __init__(self):
        self.engine: AbstractEngine = None
        self._cached_xdebug_version = None

    def after_load_engine(self, engine: 'AbstractEngine'):
        self.engine = engine

    def after_load_cli(self, main_cli_object):
        from riptide_cli.command import interrupt_handler

        @cli_section("PHP")
        @main_cli_object.command(CMD_XDEBUG)
        @click.pass_context
        @click.argument('state', required=False)
        @click.option('--request/--no-request', '-r/-R', default=None,
                      help='Toggles whether or not Xdebug should automatically activate or only using a trigger '
                           '(--request sets `xdebug.start_with_request` to "yes", --no-request sets it to "trigger"). '
                           'Xdebug 3 only.')
        @click.option('--mode', '-m',
                      help='Sets the `xdebug.mode` setting (Xdebug 3 only; otherwise ignored)')
        @click.option('--config', '-c',
                      help="Can set additional configuration values (example: 'log=/tmp/xdebug.log,log_level=10')")
        @async_command(interrupt_handler=interrupt_handler)
        async def xdebug(ctx, request, mode=None, config=None, state=None):
            """
            Control Xdebug for this project.

            If STATE is not set:
              Output whether Xdebug is currently enabled for this project.

            If STATE is set and either 'on' or 'off':
              Enable / Disable Xdebug for the current project.

            Please note that these flags only control flags that need to be used in php.ini configuration files. The
            default PHP service from the Riptide repository is correctly configured to use this.

            """
            from riptide_cli.loader import cmd_constraint_project_loaded, load_riptide_core
            from riptide_cli.lifecycle import start_project, stop_project
            load_riptide_core(ctx)
            cmd_constraint_project_loaded(ctx)
            version = self.get_xdebug_version(ctx.system_config)  # Mainly do this, to show the warning if needed.

            if mode is not None:
                self._update_flag(ctx.system_config["project"], mode, MODE_FLAG_NAME)

            if request is not None:
                self._update_flag(ctx.system_config["project"], request, REQUEST_TRIGGER_FLAG_NAME)

            if config is not None:
                config_dict = {}
                for entry in config.split(','):
                    if entry != '':
                        try:
                            key, value = entry.split('=', 1)
                        except ValueError:
                            raise RiptideCliError("Invalid value for --config.", ctx)
                        config_dict[key] = value
                self._update_flag(ctx.system_config["project"], config_dict, PARAMETERS_FLAG_NAME)

            if state is not None:
                new_flag = True
                if state == 'off':
                    new_flag = False
                self._update_flag(ctx.system_config["project"], new_flag)
                # If there are services with the role 'php', run a quick restart on them.
                php_services = [
                    s['$name']
                    for s
                    in ctx.system_config["project"]["app"].get_services_by_role('php')
                    if self.engine.service_status(ctx.system_config["project"], s['$name'])
                ]
                if len(php_services) > 0 and self.engine:
                    # Reload the configuration before restarting, to make sure that the
                    # Opcache directory settings and maybe other settings affected by the flag are also properly set
                    ctx.loaded = False
                    load_riptide_core(ctx)
                    await stop_project(ctx, php_services, show_status=False)
                    await start_project(ctx, php_services, show_status=False, quick=True)

            state = self.get_state(ctx.system_config['project'])
            state_str = style('Disabled', fg='red')
            project_name = ctx.system_config["project"]["name"]
            config_str = ""
            for key, value in state[PARAMETERS_FLAG_NAME].items():
                config_str += f"{key}={value}"
            if state[ENABLED_FLAG_NAME]:
                state_str = style('Enabled', fg='green')
            if state[REQUEST_TRIGGER_FLAG_NAME]:
                trigger_str = 'yes'
                trigger_str_start_with_request = 'trigger'
            else:
                trigger_str = 'no'
                trigger_str_start_with_request = 'yes'
            echo(f"Xdebug status for {project_name}: {state_str}")
            echo(f'Detected Xdebug version: {version}')
            echo(f'Mode: {state[MODE_FLAG_NAME]}')
            echo(f'Extra configuration: {config_str.rstrip(",")}')
            echo(f'Request trigger: {trigger_str} (xdebug.start_with_request={trigger_str_start_with_request})')

    def after_reload_config(self, config: 'Config'):
        # Nothing to do. We work solely with flags.
        pass

    def get_flag_value(self, config: 'Config', flag_name: str) -> any:
        if not config.internal_contains("project"):
            return False
        if flag_name == XDEBUG3_FLAG_NAME:
            return self.get_xdebug_version(config) == '3'
        else:
            state = self.get_state(config.internal_get("project"))
            if flag_name in state:
                return state[flag_name]
        return False

    def get_state(self, project: 'Project') -> Dict:
        if not os.path.exists(self._get_configuration_path(project)):
            s = {ENABLED_FLAG_NAME: False}
        else:
            with open(self._get_configuration_path(project), 'r') as fp:
                s = json.load(fp)
        # For backwards compatibility we check these extra:
        if MODE_FLAG_NAME not in s:
            s[MODE_FLAG_NAME] = 'debug'
        if REQUEST_TRIGGER_FLAG_NAME not in s:
            s[REQUEST_TRIGGER_FLAG_NAME] = False
        if PARAMETERS_FLAG_NAME not in s:
            s[PARAMETERS_FLAG_NAME] = {}
        return s

    def _update_flag(self, project: 'Project', new_flag, flag_name=ENABLED_FLAG_NAME):
        state = self.get_state(project)
        state[flag_name] = new_flag
        with open(self._get_configuration_path(project), 'w') as fp:
            return json.dump(state, fp)

    def _get_configuration_path(self, project: 'Project'):
        return os.path.join(get_project_meta_folder(project.folder()), XDEBUG_PLUGIN_STATE_FILE)

    def get_xdebug_version(self, config: 'Config'):
        if not self.engine:
            raise ValueError("Tried to get the Xdebug version before the engine backend was initialized.")
        if self._cached_xdebug_version is None:
            version = self._detect_xdebug_version(config)
            if not version:
                if SystemFlag.IS_CLI:
                    warn(f"Could not reliably detect the XDebug version. Please see: {WARNING_URL}")
            self._cached_xdebug_version = version if version is not None else 2
        return self._cached_xdebug_version

    def _detect_xdebug_version(self, config: 'Config'):
        # 1. In env:
        if VERSION_ENV in os.environ and os.environ[VERSION_ENV] in VERSION_VALID:
            return os.environ[VERSION_ENV]
        proj = config.internal_get('project')
        # 2. In label of image of service with role 'php':
        svc = proj['app'].get_service_by_role('php')
        if svc:
            labels = self.engine.get_service_or_command_image_labels(svc)
            if labels is not None and VERSION_LABEL in labels and labels[VERSION_LABEL] in VERSION_VALID:
                return labels[VERSION_LABEL]
        # 3. In service/cmd env:
        for obj in list(proj['app']['services'].values()) + list(proj['app']['commands'].values()):
            obj: Union[Service, Command]
            env = obj.collect_environment()
            if VERSION_ENV in env and env[VERSION_ENV] in VERSION_VALID:
                return env[VERSION_ENV]
        return None
