import yaml


def dump(data):
    class Dumper(yaml.Dumper):
        def ignore_aliases(self, data):
            return True

    return yaml.dump(data, default_flow_style=False, sort_keys=False, Dumper=Dumper).encode('utf-8')
