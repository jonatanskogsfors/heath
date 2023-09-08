from heath import __version__

    
def test_version():
    print(__version__)
    assert __version__ == "0.1.6"
