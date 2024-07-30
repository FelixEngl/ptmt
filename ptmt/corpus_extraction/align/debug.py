import typing


class DebuggableComponent(typing.Protocol):
    def debug(self):
        self.debug_with_depth(0)

    def debug_with_depth(self, depth: int):
        print(' ' * (depth * 2) + f'CALL: {self.debug_desc()}')
        self.debug_down(depth + 1)

    def debug_desc(self) -> str:
        return repr(self)

    def debug_down(self, depth: int):
        pass


def debug(obj: DebuggableComponent):
    obj.debug()
