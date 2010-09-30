import py
from iniconfig import _parse as parse, IniConfig


check_tokens = {
    'section': (
        '[section]',
        [(1, 'section', None, None)]
    ),
    'value': (
        'value = 1',
        [(1, None, 'value', '1')]
    ),
    'value in section': (
        '[section]\nvalue=1',
        [(1, 'section', None, None), (2, 'section', 'value', '1')]
    ),
    'value with continuation': (
        'names =\n Alice\n Bob',
        [(1, None, 'names', 'Alice\nBob')]
    ),
    'value with aligned continuation': (
        'names = Alice\n'
        '        Bob',
        [(1, None, 'names', 'Alice\nBob')]
    ),
    'blank line':(
        '[section]\n\nvalue=1',
        [(1, 'section', None, None), (3, 'section', 'value', '1')]
    ),
    'comment': (
        '# comment',
        []
    ),
    'comment on value': (
        'value = 1 # comment',
        [(1, None, 'value', '1')]
    ),

    'comment on section': (
        '[section] #comment',
        [(1, 'section', None, None)]
    ),

}


weird_lines = [
    '!!',
    '[uhm',
    'comeon]',
    '[uhm =',
    'comeon] =',
]

def pytest_generate_tests(metafunc):
    if 'input' in metafunc.funcargnames:
        for name, (input, expected) in check_tokens.items():
            metafunc.addcall(id=name, funcargs={
                'input': input,
                'expected': expected,
            })
    elif hasattr(metafunc.function, 'multi'):
        kwargs = metafunc.function.multi.kwargs
        names, values = zip(*kwargs.items())
        from itertools import product
        values = product(*values)
        for p in values:
            metafunc.addcall(funcargs=dict(zip(names, p)))


def test_tokenize(input, expected):
    parsed = parse(input)
    assert parsed == expected


def test_continuation_needs_perceeding_token():
    with py.test.raises(ValueError) as excinfo:
        parse(' Foo')
    assert 'line 1' in excinfo.value.args[0]

def test_continuation_cant_be_after_section():
    with py.test.raises(ValueError) as excinfo:
        parse('[section]\n Foo')
    assert 'line 2' in excinfo.value.args[0]

def test_section_cant_be_empty():
    with py.test.raises(ValueError) as excinfo:
        parse('[]')


@py.test.mark.multi(line=weird_lines)
def test_error_on_weird_lines(line):
    with py.test.raises(ValueError) as excinfo:
        parse('!!')



def test_iniconfig_from_file(tmpdir):
    path = tmpdir/'test.txt'
    path.write('[metadata]\nname=1')

    config = IniConfig(path=str(path))
    config2 = IniConfig(fp=path) # abuse py.path.local.read
    config3 = IniConfig(data=path.read())

def test_iniconfig_section_first(tmpdir):
    with py.test.raises(ValueError) as excinfo:
        IniConfig(data='name=1')
    assert excinfo.value.args[0] == "expected section in line 1, got name 'name'"

def test_iniconig_section_duplicate_fails():
    with py.test.raises(ValueError) as excinfo:
        IniConfig(data='[section]\n[section]')
    assert 'duplicate section' in excinfo.value.args[0]

def test_iniconfig_duplicate_key_fails():
    with py.test.raises(ValueError) as excinfo:
        IniConfig(data='[section]\nname = Alice\nname = bob')

    assert 'duplicate value' in excinfo.value.args[0]

def test_iniconfig_lineof():
    config = IniConfig(data=
        '[section]\n'
        'value = 1\n'
        '[section2]\n'
        '# comment\n'
        'value =2'
    )

    assert config.lineof('missing') is None
    assert config.lineof('section') == 1
    assert config.lineof('section2') == 3
    assert config.lineof('section', 'value') == 2
    assert config.lineof('section2','value') == 5


