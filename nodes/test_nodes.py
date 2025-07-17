# nodes/test_nodes.py
from core.definitions import BaseNode, SocketType, NodeStateUpdate

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

class CounterNode(BaseNode):
    """
    A node that counts how many times it has been executed within a single workflow run.
    It demonstrates the use of the node's runtime memory.
    """
    CATEGORY = "Test"

    INPUT_SOCKETS = {
        "trigger": {"type": SocketType.ANY}
    }
    OUTPUT_SOCKETS = {
        "count": {"type": SocketType.NUMBER}
    }

    def load(self):
        pass

    def execute(self, trigger):
        current_count = self.memory.get('count', 0)
        new_count = current_count + 1
        self.memory['count'] = new_count
        print(f"CounterNode: Executed {new_count} time(s).")
        return (new_count,)

class LoopingAccumulatorNode(BaseNode):
    """
    A node that demonstrates the "do not wait" and dynamic state update features to create a loop.
    It takes an initial value, then adds to it every time the 'add_value' input is triggered.
    """
    CATEGORY = "Test"
    INPUT_SOCKETS = {
        "initial_value": {"type": SocketType.NUMBER},
        "add_value": {"type": SocketType.NUMBER, "do_not_wait": True}
    }
    OUTPUT_SOCKETS = {
        "result": {"type": SocketType.NUMBER}
    }

    def load(self):
        # Initialize memory state
        self.memory['total'] = 0
        self.memory['is_initialized'] = False

    def execute(self, initial_value=None, add_value=None):
        is_initialized = self.memory.get('is_initialized', False)

        if not is_initialized:
            # First execution: triggered by 'initial_value'
            if initial_value is None:
                return (0,) # Should not happen if graph is correct

            total = float(initial_value)
            self.memory['total'] = total
            self.memory['is_initialized'] = True
            
            print(f"LoopingAccumulator: Initialized with {total}")

            # IMPORTANT: Tell the engine to only wait for 'add_value' from now on.
            # This creates the loop behavior.
            state_update = NodeStateUpdate(wait_for_inputs=['add_value'])
            return ((total,), state_update)
        else:
            # Subsequent executions: triggered by 'add_value'
            if add_value is None:
                # If triggered by something else without a value, just output current total
                return (self.memory['total'],)

            total = self.memory['total'] + float(add_value)
            self.memory['total'] = total
            
            print(f"LoopingAccumulator: Added {add_value}, new total is {total}")
            
            # No state update needed, the wait config is already correct.
            return (total,)
