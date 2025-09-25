from core.natural_tasks import write_task


def test_write_task():
    write_task("docs/example")
    with open("docs/example.txt") as f:
        assert f.read() == "docs/example"
