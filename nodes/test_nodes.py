# nodes/test_nodes.py
from core.definitions import BaseNode, SocketType

class SocketArrayTestNode(BaseNode):
    CATEGORY = "Test"
    INPUT_SOCKETS = {
        "texts_1": {"type": SocketType.TEXT, "array": True, "is_dependency": True},
        "texts_2": {"type": SocketType.TEXT, "array": True, "is_dependency": True},
        "dependency": {"type": SocketType.ANY, "is_dependency": True}
    }
    OUTPUT_SOCKETS = {
        "output_1": {"type": SocketType.TEXT},
        "output_2": {"type": SocketType.TEXT}
    }

    def load(self):
        pass

    def execute(self, texts_1, texts_2, dependency):
        # Simple logic to concatenate the texts and pass them through
        output_1 = ", ".join(texts_1)
        output_2 = ", ".join(texts_2)
        print(f"Dependency received: {dependency}")
        return (output_1, output_2)
