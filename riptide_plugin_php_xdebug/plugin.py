import json
import os
from typing import Dict, TYPE_CHECKING

import click
from click import style, echo

from riptide.config.files import get_project_meta_folder
from riptide.plugin.abstract import AbstractPlugin
from riptide_cli.helpers import cli_section, async_command

if TYPE_CHECKING:
    from riptide.config.document.config import Config
    from riptide.config.document.project import Project
    from riptide.engine.abstract import AbstractEngine

CMD_XDEBUG = 'xdebug'
ENABLED_FLAG_NAME = 'enabled'
XDEBUG_PLUGIN_STATE_FILE = '.xdebug.json'


class PhpXdebugPlugin(AbstractPlugin):
    def __init__(self):
        self.engine: AbstractEngine = None

    def after_load_engine(self, engine: 'AbstractEngine'):
        self.engine = engine

    def after_load_cli(self, main_cli_object):
        from riptide_cli.command import interrupt_handler

        @cli_section("PHP")
        @main_cli_object.command(CMD_XDEBUG)
        @click.pass_context
        @click.argument('state', required=False)
        @async_command(interrupt_handler=interrupt_handler)
        async def xdebug(ctx, state=None):
            """
            Control Xdebug for this project.

            If STATE is not set:
              Output whether Xdebug is currently enabled for this project.

            If STATE is set and either 'on' or 'off':
              Enable / Disable Xdebug for the current project.
            """
            from riptide_cli.loader import cmd_constraint_project_loaded, load_riptide_core
            from riptide_cli.lifecycle import start_project, stop_project
            load_riptide_core(ctx)
            cmd_constraint_project_loaded(ctx)

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

            state_str = style('Disabled', fg='red')
            project_name = ctx.system_config["project"]["name"]
            if self.get_flag_value(ctx.system_config, ENABLED_FLAG_NAME):
                state_str = style('Enabled', fg='green')
            echo(f"Xdebug status for {project_name}: {state_str}.")


    def after_reload_config(self, config: 'Config'):
        # Nothing to do. We work solely with flags.
        pass

    def get_flag_value(self, config: 'Config', flag_name: str) -> bool:
        if "project" not in config:
            return False
        if flag_name == ENABLED_FLAG_NAME:
            return self.get_state(config["project"])[ENABLED_FLAG_NAME]
        return False

    def get_state(self, project: 'Project') -> Dict:
        if not os.path.exists(self._get_configuration_path(project)):
            return {ENABLED_FLAG_NAME: False}
        with open(self._get_configuration_path(project), 'r') as fp:
            return json.load(fp)

    def _update_flag(self, project: 'Project', new_flag):
        state = self.get_state(project)
        state[ENABLED_FLAG_NAME] = new_flag
        with open(self._get_configuration_path(project), 'w') as fp:
            return json.dump(state, fp)

    def _get_configuration_path(self, project: 'Project'):
        return os.path.join(get_project_meta_folder(project.folder()), XDEBUG_PLUGIN_STATE_FILE)
