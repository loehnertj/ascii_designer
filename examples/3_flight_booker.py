from datetime import date, datetime
import tkinter.ttk as ttk
from tkinter.messagebox import showinfo
from ascii_designer import set_toolkit, AutoFrame, Invalid


def str2date(s):
    return datetime.strptime(s, "%d.%m.%Y").date()


def date2str(dt):
    return dt.strftime("%d.%m.%Y")


class FlightBooker(AutoFrame):
    f_body = """
        |   <->
         [kind:  v]
         [t1: _   ]
         [t2: _   ] 
          [ Book ]
    """
    f_option_tk_autovalidate = True

    def f_on_build(self):
        self["kind"]["values"] = ["one-way flight", "return flight"]
        self["t1"].variable.convert = str2date
        self["t2"].variable.convert = str2date
        self["t1"].variable.convert_set = date2str
        self["t2"].variable.convert_set = date2str

        self.kind = "one-way flight"
        self.t1 = self.t2 = datetime.now().date()
        # initial ctl update
        self.on_kind(self.kind)

    @property
    def booking_possible(self):
        """True if all constraints are met."""
        dt1 = self.t1
        dt2 = self.t2
        if dt1 is Invalid:
            return False
        if self.kind == "return flight":
            if dt2 is Invalid:
                return False
            if dt2 < dt1:
                return False
        return True

    def _update_book(self):
        self["book"].state(["!disabled"] if self.booking_possible else ["disabled"])

    def on_kind(self, kind):
        """Enable/disable T2, then check constraints."""
        self["t2"].state(["!disabled"] if kind == "return flight" else ["disabled"])
        self._update_book()

    def on_t1(self, dt1):
        """Recheck constraints."""
        self._update_book()

    def on_t2(self, dt2):
        """Recheck constraints."""
        self._update_book()

    def book(self):
        """Execute booking"""
        dt1 = self.t1
        if self.kind == "one-way flight":
            message = f"You have booked a one-way flight on {date2str(dt1)}."
        elif self.kind == "return flight":
            dt2 = self.t2
            message = f"You have booked a return flight from {date2str(dt1)} to {date2str(dt2)}."
        else:
            # Safeguard
            raise ValueError("Unexpected flight kind")
        showinfo("Booking successfull", message)


def setup_style(root):
    style = ttk.Style()
    style.map(
        "TEntry",
        # Order matters: earlier entries take precedence.
        fieldbackground=[("disabled", "#d0d0d0"), ("invalid", "red")],
        foreground=[("disabled", "#808080"), ("invalid", "black")],
    )


if __name__ == "__main__":
    set_toolkit("ttk", {"add_setup": setup_style})
    FlightBooker().f_show()
