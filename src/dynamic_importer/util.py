# -*- coding: utf-8 -*-
#
# Copyright (c) 2024 CloudTruth, Inc.
# All Rights Reserved
#
from __future__ import annotations

import os

from click import Option
from click import UsageError
from ruamel.yaml import YAML
from ruamel.yaml.compat import StringIO


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


class StringableYAML(YAML):
    """
    ruamel.yaml has strong opinions about dumping to a string but provides
    an example of how to do it "if you really need to have it (or think you do)"

    Since we do some post-processing on the dumped string before writing it
    to disk, we DO, in fact, need to have it.

    See also:
    https://yaml.readthedocs.io/en/latest/example/#output-of-dump-as-a-string
    """

    def dump(self, data, stream=None, **kw):
        inefficient = False
        if stream is None:
            inefficient = True
            stream = StringIO()
        YAML.dump(self, data, stream, **kw)
        if inefficient:
            return stream.getvalue()
