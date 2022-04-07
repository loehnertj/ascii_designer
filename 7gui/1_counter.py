from ascii_designer import AutoFrame, set_toolkit

class Counter(AutoFrame):
    f_body = """
                    |
        [ Counter_ ] [Count]
    """

    def f_on_build(self):
        self["counter"]["state"] = "readonly"
        self.counter = "0"

    def count(self):
        self.counter = str(int(self.counter)+1)


if __name__ == "__main__":
    set_toolkit("tk")
    Counter().f_show()
