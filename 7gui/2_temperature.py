from ascii_designer import AutoFrame, set_toolkit

class TemperatureConverter(AutoFrame):
    f_body = """
                    |           |               |
        [ celsius_ ] Celsius =   [ fahrenheit_ ] Fahrenheit
    """

    def f_on_build(self):
        self.celsius = ""
        self.fahrenheit = ""

    def on_celsius(self, val):
        try:
            val = float(val)
        except ValueError:
            return
        self.fahrenheit = val * (9.0/5.0) + 32.0

    def on_fahrenheit(self, val):
        try:
            val = float(val)
        except ValueError:
            return
        self.celsius = (val - 32.0) * 5.0 / 9.0


if __name__ == "__main__":
    set_toolkit("tk")
    TemperatureConverter().f_show()
