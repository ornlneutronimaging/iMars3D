from multiprocessing import Lock
from panel.widgets import Tqdm as _Tqdm
from typing import Union

LockType = Union[Lock, "mutlithreading.Lock"]  # noqa: F821
TqdmType = Union["panel.widgets.Tqdm", "imars3d.ui.widgets.Tqdm"]  # noqa: F821


class Tqdm(_Tqdm):
    """Tqdm is a thin wrapper around `panel.widgets.Tqdm <https://panel.holoviz.org/reference/indicators/Tqdm.html>`_ which adds missing functionality needed for using with `tqdm.contrib.concurrent.process_map <https://tqdm.github.io/docs/contrib.concurrent/#process_map>`_.

    Assuming that panel.widgets.Tqdm gets updated with the new functionality, this can be removed. v0.14.0 did not contain this functionality.

    The functionality added by this wrapper is managing a lock.

    Usage:

    .. code-block::

       import panel as pn
       import param
       import time
       from tqdm.contrib.concurrent import process_map
       pn.extension()

       class ProgressBarDemo(pn.viewable.Viewer):
           call_map_process = param.Action(lambda x: x.param.trigger("call_map_process"))

           def __init__(self, **params):
               super().__init__(**params)

               self.progress_bar = Tqdm()
               self._panel = pn.Column(
                   pn.widgets.Button.from_param(self.param.call_map_process),
                   self.progress_bar
               )

           @param.depends("call_map_process", watch=True)
           def _func_map_process(self):
               rst = process_map(
                   time.sleep,
                   [.3] * 10,
                   max_workers=2,
                   tqdm_class=self.progress_bar
               )


           def __panel__(self):
               return self._panel


    Then create an instance of the ``ProgressBarDemo`` and show it.
    """

    def __init__(self, *args, **kwargs):
        """Create a multiprocessing.Lock if one is not supplied."""
        self._lock = kwargs.pop("lock", Lock())
        super().__init__(*args, **kwargs)

    def get_lock(self) -> LockType:
        """
        Accessor method.

        Returns
        -------
            The lock owned by this object.
        """
        return self._lock

    def set_lock(self, lock: LockType) -> None:
        """
        Mutator method.

        Parameters
        ----------
        lock:
            Set the lock owned by this object.
        """
        self._lock = lock
