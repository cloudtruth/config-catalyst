from __future__ import annotations

import os

from click import Option
from click import UsageError


def validate_env_values(ctx, param, value):
    if isinstance(value, tuple):
        return value
    env_path = value.split(":")
    if len(env_path) != 2:
        raise UsageError("You must specify environment values as `env:file_path`.")
    if not os.path.isfile(env_path[1]):
        raise UsageError("Path to environment values file could not be accessed.")
    return value


# These classes are not actively used. But they'll probably be useful at some point.
class MutuallyExclusiveOption(Option):
    def __init__(self, *args, **kwargs):
        self.mutually_exclusive = set(kwargs.pop("mutually_exclusive", []))
        help = kwargs.get("help", "")
        if self.mutually_exclusive:
            ex_str = ", ".join(self.mutually_exclusive)
            kwargs["help"] = help + (
                " NOTE: This argument is mutually exclusive with "
                " arguments: [" + ex_str + "]."
            )
        super(MutuallyExclusiveOption, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        if self.mutually_exclusive.intersection(opts) and self.name in opts:
            raise UsageError(
                "Option Error: `{}` is mutually exclusive with "
                "arguments `{}`.".format(self.name, ", ".join(self.mutually_exclusive))
            )

        return super(MutuallyExclusiveOption, self).handle_parse_result(ctx, opts, args)


class RequiredDependentOption(Option):
    def __init__(self, *args, **kwargs):
        self.required_dependents = set(kwargs.pop("required_dependents", []))
        help = kwargs.get("help", "")
        if self.required_dependents:
            ex_str = ", ".join(self.required_dependents)
            kwargs["help"] = help + (
                " NOTE: This argument requires specifying the following"
                " arguments: [" + ex_str + "]."
            )
        super().__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        if not self.required_dependents <= opts and self.name in opts:
            raise UsageError(
                "Option Error: `{}` requires specifying the following "
                "arguments `{}`.".format(self.name, ", ".join(self.mutually_exclusive))
            )

        return super().handle_parse_result(ctx, opts, args)
