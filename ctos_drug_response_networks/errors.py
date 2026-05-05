class CtosReproError(Exception):
    """Base package error."""


class ConfigError(CtosReproError):
    exit_code = 2


class InputSchemaError(CtosReproError):
    exit_code = 3


class MissingAssetError(CtosReproError):
    exit_code = 4


class UnsupportedRouteError(CtosReproError):
    exit_code = 5


class LeakageError(CtosReproError):
    exit_code = 6


class ReleaseMetadataError(CtosReproError):
    exit_code = 7


class RuntimeExecutionError(CtosReproError):
    exit_code = 8


class TruthLockError(CtosReproError):
    exit_code = 9
