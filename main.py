__author__ = "Jonas Teufel"
__version__ = "0.0.0"

from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import ScreenManager
import pisole.pisole as pisole
from ui import ExerciseCreation
from ui import MainMenu, MainScreen
from ui import ExamsMenu, ExamsScreen


class PiLearnerWidget(GridLayout):

    def __init__(self):
        super(PiLearnerWidget, self).__init__()

        self.cols = 3
        self.rows = 1
        self.minimum_height = 480
        self.minimum_width = 1150

        sm = ScreenManager()
        s1 = MainScreen(sm)
        s2 = ExamsScreen(sm)
        sm.add_widget(s1)
        sm.add_widget(s2)
        self.add_widget(sm)

        self.add_widget(ExerciseCreation("Elektronik", "Halbleiterphysik"))

        self.console = pisole.SimplePisoleConsole()
        self.console.start()
        self.add_widget(self.console.get_widget())

class PiLearnerApp(App):

    def build(self):
        return PiLearnerWidget()

if __name__ == "__main__":
    app = PiLearnerApp()
    app.run()