from wikiteam3.dumpgenerator.cli import Delay
from wikiteam3.dumpgenerator.config import Config


def saveLogs(config: Config = None, session=None):
    """Save Special:Log"""
    # get all logs from Special:Log
    """parse
    <select name='type'>
    <option value="block">Bloqueos de usuarios</option>
    <option value="rights">Cambios de perfil de usuario</option>
    <option value="protect" selected="selected">Protecciones de páginas</option>
    <option value="delete">Registro de borrados</option>
    <option value="newusers">Registro de creación de usuarios</option>
    <option value="merge">Registro de fusiones</option>
    <option value="import">Registro de importaciones</option>
    <option value="patrol">Registro de revisiones</option>
    <option value="move">Registro de traslados</option>
    <option value="upload">Subidas de archivos</option>
    <option value="">Todos los registros</option>
    </select>
"""
    Delay(config=config, session=session)
