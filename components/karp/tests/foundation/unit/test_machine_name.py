from karp.foundation.value_objects import MachineName


def test_valid_machine_name_succeeds():
    name = "machine_name"
    machine_name = MachineName(name=name)
    # assert str(machine_name) == name
    assert machine_name.name == name
