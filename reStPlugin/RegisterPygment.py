# -*- coding: utf-8 -*-
# Copyright (C) 2007 Christophe Kibleur <kib2@free.fr>
#
# This file is part of reSTinPeace (http://kib2.alwaysdata.net).
#
# reSTinPeace is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# reSTinPeace is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

from docutils import nodes
from docutils.parsers.rst import directives, Directive

## Pygments
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

class Pygments(Directive):
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {
        'linenos': directives.flag,
        'hl_lines': directives.positive_int_list,
        'linenostart': directives.nonnegative_int,
        'linenostep': directives.positive_int,
        'linenospecial': directives.nonnegative_int,
        'nobackground': directives.flag,
        'anchorlinenos': directives.flag,
        'noclasses': directives.flag,
    }
    has_content = True

    def run(self):
        self.assert_has_content()
        try:
            lexer = get_lexer_by_name(self.arguments[0])
        except ValueError:
            # no lexer found
            lexer = get_lexer_by_name('text')

        options={}
        for (option, converter) in self.option_spec.iteritems():
            if converter == directives.flag:
                if option in self.options:
                    options[option] = True
            elif option in self.options:
                options[option] = self.options[option]

        formatter = HtmlFormatter(**options)
        parsed = highlight(u'\n'.join(self.content), lexer, formatter)
        return [nodes.raw('', parsed, format='html')]

directives.register_directive('code', Pygments)
directives.register_directive('code-block', Pygments)
directives.register_directive('sourcecode', Pygments)
directives.register_directive('sourcecode-block', Pygments)

