from ascii_designer import AutoFrame, set_toolkit, Invalid

class TemperatureConverter(AutoFrame):
    f_body = """
                    |           |               |
        [ celsius_ ] Celsius =   [ fahrenheit_ ] Fahrenheit
    """
    # Using value converter also counts as validation
    f_option_tk_autovalidate = True

    def f_on_build(self):
        self.celsius = ""
        self.fahrenheit = ""
        self["celsius"].variable.convert = float
        self["fahrenheit"].variable.convert = float

    def on_celsius(self, val):
        if val is Invalid:
            return
        self.fahrenheit = val * (9.0/5.0) + 32.0

    def on_fahrenheit(self, val):
        if val is Invalid:
            return
        self.celsius = (val - 32.0) * 5.0 / 9.0


if __name__ == "__main__":
    set_toolkit("ttk")
    TemperatureConverter().f_show()
