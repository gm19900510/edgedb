#
# This source file is part of the EdgeDB open source project.
#
# Copyright 2019-present MagicStack Inc. and the EdgeDB authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


from __future__ import annotations
from typing import *  # NoQA

import functools
import re
import typing

from edb.common.markup.renderers import terminal
from edb.common.markup.renderers import styles

from . import context


style = styles.Dark256


ESCAPE = re.compile(r'[\x00-\x1f\\"\b\f\n\r\t]')

ESCAPE_DCT = {
    '\\': '\\\\',
    '"': '\\"',
    '\b': '\\b',
    '\f': '\\f',
    '\n': '\\n',
    '\r': '\\r',
    '\t': '\\t',
}

for i in range(0x20):
    ESCAPE_DCT.setdefault(chr(i), '\\u{0:04x}'.format(i))


def _encode_str(s: str) -> str:
    def replace(match: typing.Match[str]) -> str:
        return ESCAPE_DCT[match.group(0)]
    return '"' + ESCAPE.sub(replace, s) + '"'


@functools.singledispatch
def walk(
    o: Any,
    repl_ctx: context.ReplContext,
    buf: terminal.Buffer
) -> None:
    # The default renderer.  Shouldn't be ever called,
    # but if for some reason we haven't defined a renderer
    # for some edgedb type it's better to render something
    # than crash.
    buf.write(str(o))


@walk.register(list)
@walk.register(tuple)
def _set(
    o: Sequence[Any],
    repl_ctx: context.ReplContext,
    buf: terminal.Buffer
) -> None:
    with buf.foldable_lines():
        buf.write('[', style.bracket)
        with buf.indent():
            for idx, el in enumerate(o):
                walk(el, repl_ctx, buf)
                if idx < (len(o) - 1):
                    buf.write(',')
                    buf.mark_line_break()
        buf.write(']', style.bracket)


@walk.register(dict)
def _dict(
    o: Mapping[str, Any],
    repl_ctx: context.ReplContext,
    buf: terminal.Buffer
) -> None:
    with buf.foldable_lines():
        buf.write('{', style.bracket)
        with buf.indent():
            for idx, (key, el) in enumerate(o.items()):
                walk(key, repl_ctx, buf)
                buf.write(': ')
                walk(el, repl_ctx, buf)
                if idx < (len(o) - 1):
                    buf.write(',')
                    buf.mark_line_break()
        buf.write('}', style.bracket)


@walk.register(int)
@walk.register(float)
def _numeric(
    o: Union[int, float],
    repl_ctx: context.ReplContext,
    buf: terminal.Buffer
) -> None:
    buf.write(str(o), style.code_number)


@walk.register
def _str(
    o: str,
    repl_ctx: context.ReplContext,
    buf: terminal.Buffer
) -> None:
    o = str(o)
    buf.write(_encode_str(str(o)), style.code_string)


@walk.register
def _bool(
    o: bool,
    repl_ctx: context.ReplContext,
    buf: terminal.Buffer
) -> None:
    buf.write(str(o).lower(), style.code_constant)


@walk.register
def _empty(
    o: None,
    repl_ctx: context.ReplContext,
    buf: terminal.Buffer
) -> None:
    buf.write('null', style.code_constant)
