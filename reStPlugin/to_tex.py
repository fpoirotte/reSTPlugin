#!/usr/bin/python
# encoding: utf-8

try:
    import locale
    locale.setlocale(locale.LC_ALL, '')
except:
    pass
import docutils.core
from docutils.core import publish_cmdline, default_description


description = ('Generates LaTeX documents from standalone reStructuredText '
               'sources. Uses `pygments` to colorize code. '
               'Needs an adapted stylesheet' + default_description)

# Define a new directive `sourcecode` that uses the `pygments` source
# highlighter to render code in color.
#
# Code from the `pygments`_ documentation for `Using Pygments in ReST
# documents`_.

from docutils import nodes
from docutils.parsers.rst import directives
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import LatexFormatter

#pygments_formatter = LatexFormatter(option='wrap',
#                                    #linenos=True,
#                                    style="fruity",
#                                    full=False)

pygments_formatter = LatexFormatter( linenos=False,
                    encoding='utf-8',
                    verboptions="frame=lines,framerule=2pt,fontfamily=courier,fontsize=\\small,label={[source code begin]source code end}"
                  )
#pygments_formatter.full = True
def pygments_directive(name, arguments, options, content, lineno,
                       content_offset, block_text, state, state_machine):
    try:
        lexer = get_lexer_by_name(arguments[0])
    except ValueError:
        # no lexer found - use the text one instead of an exception
        lexer = get_lexer_by_name('text')
    parsed = highlight(u'\n'.join(content), lexer, pygments_formatter)
    return [nodes.raw('', parsed, format='latex')]
pygments_directive.arguments = (1, 0, 1)
pygments_directive.content = 1
directives.register_directive('sourcecode', pygments_directive)


if __name__ == "__main__":

    publish_cmdline(writer_name='latex',
                    settings_overrides={'output_encoding':'utf8',
                                        'documentoptions':'10pt,a4paper,french',
                                        'stylesheet':'default.sty',
                                        'language':'fr'
                                        },
                    description=description)
