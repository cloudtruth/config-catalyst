# -*- coding: utf-8 -*-
#
# Copyright (c) 2024 CloudTruth, Inc.
# All Rights Reserved
#
from __future__ import annotations


def coerce_types(type: str) -> str:
    if type == "null":
        return "string"
    elif type == "template":
        return "string"

    return type
