"""7GUIs Task 4: Timer.

The solution shown here is arguably a bit overcomplex, since we could just have
used a Tinter ``.after`` callback for the concurrent timer update. However, this
is really only an option for "toy" problems like this one.

So I opted to show how a "real-life" application should do it. A real Thread
is used for the timer, which can operate totally independent from the GUI. In
consequence, setup/teardown get a bit more complex.

A ``Lock`` is used to protect the timer value, which is probably unecessary for
an atomic value but good practice for more complex data.

Clean shutdown is done by using a ``threading.Event``. I generally advise
against using ``daemon`` to "blow up" worker threads.
"""

from time import time
import tkinter as tk
import tkinter.ttk as ttk
from threading import Thread, Event, Lock
from ascii_designer import set_toolkit, AutoFrame


class Timer(AutoFrame):
    f_body = """
        |               |    -                  |
         Elapsed time:   <elapsed_pbar         >
         elapsed_text:.
         Duration:       [duration: 1 -+- 60   ]
         [           Reset                     ]
    """

    def __init__(self):
        super().__init__()
        self._elapsed_time_s = 0.0
        # Protects access to _elapsed_time_s.
        self._xthread_lock = Lock()
        # Used to signal the Timer Thread that it should stop.
        self._stop_timer = Event()

    def f_on_build(self):
        v = tk.DoubleVar(self[""], 0.0)
        pbar = ttk.Progressbar(self[""], maximum=1, mode="determinate", variable=v)
        pbar.variable = v
        # Replace placeholder and remember control
        self.elapsed_pbar = pbar
        self.f_controls["elapsed_pbar"] = pbar

        # Timer event callback
        self[""].bind("<<TimerTick>>", lambda _: self._update_display())
        # When form is closed, halt the timer thread.
        self[""].bind("<Destroy>", self._on_destroy)

    def f_on_show(self):
        """On show, start timer thread"""
        self._stop_timer = Event()
        thread = Thread(target=self._timer_loop, name="TimerThread")
        thread.start()

    def _on_destroy(self, *args):
        """on close, stop timer thread by setting the stop event."""
        self._stop_timer.set()

    def _timer_loop(self, rate_s=0.1):
        tkroot = self[""]
        last_tick_time = time()
        while not self._stop_timer.is_set():
            t = time()
            # XXX: This might be unsafe access
            duration = self.duration
            with self._xthread_lock:
                elapsed = self._elapsed_time_s + (t - last_tick_time)
                elapsed = min(elapsed, duration)
                self._elapsed_time_s = elapsed
            last_tick_time = t
            # Crossthread post of timer update
            tkroot.event_generate("<<TimerTick>>", when="tail")
            # Event.wait's timeout is used as rate-limiter.
            # !! Due to CPythons limitations, a non-throttled thread will most
            # likely "starve" the GUI thread.
            self._stop_timer.wait(rate_s)

    # GUI Events.
    def reset(self):
        with self._xthread_lock:
            self._elapsed_time_s = 0.0
        self._update_display()

    def on_duration(self, val):
        # XXX: Contrary to the documentation, ttk.Scale's command gives us a
        # string instead of a float.
        val = float(val)
        with self._xthread_lock:
            if self._elapsed_time_s > val:
                self._elapsed_time_s = val
        self._update_display()

    def _update_display(self):
        duration = self.duration
        with self._xthread_lock:
            elapsed = self._elapsed_time_s
        pbar = self["elapsed_pbar"]
        pbar["maximum"] = self.duration
        pbar.variable.set(elapsed)
        self.elapsed_text = f"{elapsed:0.2f} / {duration:0.2f}"


if __name__ == "__main__":
    set_toolkit("ttk")
    Timer().f_show()
